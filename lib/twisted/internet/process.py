# -*- test-case-name: lib.twisted.test.test_process -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

# System Imports
import gc, os, sys, stat, traceback, select, signal, errno

try:
    import pty
except ImportError:
    pty = None

try:
    import fcntl, termios
except ImportError:
    fcntl = None

from lib.twisted.python import log, failure
from lib.twisted.python.util import switchUID
from lib.twisted.internet import fdesc, abstract, error
from lib.twisted.internet.main import CONNECTION_LOST, CONNECTION_DONE
from lib.twisted.internet._baseprocess import BaseProcess

ProcessExitedAlready = error.ProcessExitedAlready
reapProcessHandlers = {}

def reapAllProcesses():
    for process in reapProcessHandlers.values():
        process.reapProcess()

def registerReapProcessHandler(pid, process):
    if pid in reapProcessHandlers:
        raise RuntimeError("Try to register an already registered process.")
    try:
        auxPID, status = os.waitpid(pid, os.WNOHANG)
    except:
        log.msg('Failed to reap %d:' % pid)
        log.err()
        auxPID = None
    if auxPID:
        process.processEnded(status)
    else:
        # if auxPID is 0, there are children but none have exited
        reapProcessHandlers[pid] = process

def unregisterReapProcessHandler(pid, process):
    if not (pid in reapProcessHandlers
            and reapProcessHandlers[pid] == process):
        raise RuntimeError("Try to unregister a process not registered.")
    del reapProcessHandlers[pid]

def detectLinuxBrokenPipeBehavior():
    global brokenLinuxPipeBehavior
    r, w = os.pipe()
    os.write(w, 'a')
    reads, writes, exes = select.select([w], [], [], 0)
    if reads:
        # Linux < 2.6.11 says a write-only pipe is readable.
        brokenLinuxPipeBehavior = True
    else:
        brokenLinuxPipeBehavior = False
    os.close(r)
    os.close(w)

detectLinuxBrokenPipeBehavior()

class ProcessWriter(abstract.FileDescriptor):
    connected = 1
    ic = 0
    enableReadHack = False

    def __init__(self, reactor, proc, name, fileno, forceReadHack=False):
        abstract.FileDescriptor.__init__(self, reactor)
        fdesc.setNonBlocking(fileno)
        self.proc = proc
        self.name = name
        self.fd = fileno

        if not stat.S_ISFIFO(os.fstat(self.fileno()).st_mode):
            self.enableReadHack = False
        elif forceReadHack:
            self.enableReadHack = True
        else:
            try:
                os.read(self.fileno(), 0)
            except OSError:
                self.enableReadHack = True

        if self.enableReadHack:
            self.startReading()

    def fileno(self):
        return self.fd

    def writeSomeData(self, data):
        rv = fdesc.writeToFD(self.fd, data)
        if rv == len(data) and self.enableReadHack:
            self.startReading()
        return rv

    def write(self, data):
        self.stopReading()
        abstract.FileDescriptor.write(self, data)

    def doRead(self):
        if self.enableReadHack:
            if brokenLinuxPipeBehavior:
                fd = self.fd
                r, w, x = select.select([fd], [fd], [], 0)
                if r and w:
                    return CONNECTION_LOST
            else:
                return CONNECTION_LOST
        else:
            self.stopReading()

    def connectionLost(self, reason):
        fdesc.setBlocking(self.fd)

        abstract.FileDescriptor.connectionLost(self, reason)
        self.proc.childConnectionLost(self.name, reason)

class ProcessReader(abstract.FileDescriptor):
    connected = 1

    def __init__(self, reactor, proc, name, fileno):
        abstract.FileDescriptor.__init__(self, reactor)
        fdesc.setNonBlocking(fileno)
        self.proc = proc
        self.name = name
        self.fd = fileno
        self.startReading()

    def fileno(self):
        return self.fd

    def writeSomeData(self, data):
        assert data == ""
        return CONNECTION_LOST

    def doRead(self):
        return fdesc.readFromFD(self.fd, self.dataReceived)

    def dataReceived(self, data):
        self.proc.childDataReceived(self.name, data)

    def loseConnection(self):
        if self.connected and not self.disconnecting:
            self.disconnecting = 1
            self.stopReading()
            self.reactor.callLater(0, self.connectionLost,
                                   failure.Failure(CONNECTION_DONE))

    def connectionLost(self, reason):
        abstract.FileDescriptor.connectionLost(self, reason)
        self.proc.childConnectionLost(self.name, reason)

class _BaseProcess(BaseProcess, object):

    status = None
    pid = None

    def reapProcess(self):
        try:
            try:
                pid, status = os.waitpid(self.pid, os.WNOHANG)
            except OSError, e:
                if e.errno == errno.ECHILD:
                    # no child process
                    pid = None
                else:
                    raise
        except:
            log.msg('Failed to reap %d:' % self.pid)
            log.err()
            pid = None
        if pid:
            self.processEnded(status)
            unregisterReapProcessHandler(pid, self)

    def _getReason(self, status):
        exitCode = sig = None
        if os.WIFEXITED(status):
            exitCode = os.WEXITSTATUS(status)
        else:
            sig = os.WTERMSIG(status)
        if exitCode or sig:
            return error.ProcessTerminated(exitCode, sig, status)
        return error.ProcessDone(status)

    def signalProcess(self, signalID):
        if signalID in ('HUP', 'STOP', 'INT', 'KILL', 'TERM'):
            signalID = getattr(signal, 'SIG%s' % (signalID,))
        if self.pid is None:
            raise ProcessExitedAlready()
        os.kill(self.pid, signalID)


    def _resetSignalDisposition(self):
        for signalnum in range(1, signal.NSIG):
            if signal.getsignal(signalnum) == signal.SIG_IGN:
                signal.signal(signalnum, signal.SIG_DFL)

    def _fork(self, path, uid, gid, executable, args, environment, **kwargs):
        settingUID = (uid is not None) or (gid is not None)
        if settingUID:
            curegid = os.getegid()
            currgid = os.getgid()
            cureuid = os.geteuid()
            curruid = os.getuid()
            if uid is None:
                uid = cureuid
            if gid is None:
                gid = curegid
            # prepare to change UID in subprocess
            os.setuid(0)
            os.setgid(0)

        collectorEnabled = gc.isenabled()
        gc.disable()
        try:
            self.pid = os.fork()
        except:
            # Still in the parent process
            if settingUID:
                os.setregid(currgid, curegid)
                os.setreuid(curruid, cureuid)
            if collectorEnabled:
                gc.enable()
            raise
        else:
            if self.pid == 0:
                try:
                    sys.settrace(None)
                    self._setupChild(**kwargs)
                    self._execChild(path, settingUID, uid, gid,
                                    executable, args, environment)
                except:
                    try:
                        stderr = os.fdopen(2, 'w')
                        stderr.write("Upon execvpe %s %s in environment %s\n:" %
                                     (executable, str(args),
                                      "id %s" % id(environment)))
                        traceback.print_exc(file=stderr)
                        stderr.flush()
                        for fd in range(3):
                            os.close(fd)
                    except:
                        pass
                os._exit(1)

        if settingUID:
            os.setregid(currgid, curegid)
            os.setreuid(curruid, cureuid)
        if collectorEnabled:
            gc.enable()
        self.status = -1

    def _setupChild(self, *args, **kwargs):
        raise NotImplementedError()

    def _execChild(self, path, settingUID, uid, gid,
                   executable, args, environment):
        if path:
            os.chdir(path)
        # set the UID before I actually exec the process
        if settingUID:
            switchUID(uid, gid)
        os.execvpe(executable, args, environment)

    def __repr__(self):
        return "<%s pid=%s status=%s>" % (self.__class__.__name__,
                                          self.pid, self.status)

class Process(_BaseProcess):
    debug = False
    debug_child = False

    status = -1
    pid = None

    processWriterFactory = ProcessWriter
    processReaderFactory = ProcessReader

    def __init__(self,
                 reactor, executable, args, environment, path, proto,
                 uid=None, gid=None, childFDs=None):
        if not proto:
            assert 'r' not in childFDs.values()
            assert 'w' not in childFDs.values()
        _BaseProcess.__init__(self, proto)

        self.pipes = {}
        helpers = {}

        if childFDs is None:
            childFDs = {0: "w",
                        1: "r", 
                        2: "r", 
                        }
        debug = self.debug
        if debug: print "childFDs", childFDs

        _openedPipes = []
        def pipe():
            r, w = os.pipe()
            _openedPipes.extend([r, w])
            return r, w

        fdmap = {} # maps childFD to parentFD
        try:
            for childFD, target in childFDs.items():
                if debug: print "[%d]" % childFD, target
                if target == "r":
                    readFD, writeFD = pipe()
                    if debug: print "readFD=%d, writeFD=%d" % (readFD, writeFD)
                    fdmap[childFD] = writeFD     # child writes to this
                    helpers[childFD] = readFD    # parent reads from this
                elif target == "w":
                    # we need a pipe that the parent can write to
                    readFD, writeFD = pipe()
                    if debug: print "readFD=%d, writeFD=%d" % (readFD, writeFD)
                    fdmap[childFD] = readFD      # child reads from this
                    helpers[childFD] = writeFD   # parent writes to this
                else:
                    assert type(target) == int, '%r should be an int' % (target,)
                    fdmap[childFD] = target      # parent ignores this
            if debug: print "fdmap", fdmap
            if debug: print "helpers", helpers

            self._fork(path, uid, gid, executable, args, environment, fdmap=fdmap)
        except:
            map(os.close, _openedPipes)
            raise
        self.proto = proto

        for childFD, parentFD in helpers.items():
            os.close(fdmap[childFD])

            if childFDs[childFD] == "r":
                reader = self.processReaderFactory(reactor, self, childFD,
                                        parentFD)
                self.pipes[childFD] = reader

            if childFDs[childFD] == "w":
                writer = self.processWriterFactory(reactor, self, childFD,
                                        parentFD, forceReadHack=True)
                self.pipes[childFD] = writer

        try:
            if self.proto is not None:
                self.proto.makeConnection(self)
        except:
            log.err()
        registerReapProcessHandler(self.pid, self)


    def _setupChild(self, fdmap):
        debug = self.debug_child
        if debug:
            errfd = sys.stderr
            errfd.write("starting _setupChild\n")

        destList = fdmap.values()
        try:
            import resource
            maxfds = resource.getrlimit(resource.RLIMIT_NOFILE)[1] + 1
            if maxfds > 1024:
                maxfds = 1024
        except:
            maxfds = 256

        for fd in xrange(maxfds):
            if fd in destList:
                continue
            if debug and fd == errfd.fileno():
                continue
            try:
                os.close(fd)
            except:
                pass
        if debug: print >>errfd, "fdmap", fdmap
        childlist = fdmap.keys()
        childlist.sort()

        for child in childlist:
            target = fdmap[child]
            if target == child:
                if debug: print >>errfd, "%d already in place" % target
                fdesc._unsetCloseOnExec(child)
            else:
                if child in fdmap.values():
                    newtarget = os.dup(child) # give it a safe home
                    if debug: print >>errfd, "os.dup(%d) -> %d" % (child,
                                                                   newtarget)
                    os.close(child) # close the original
                    for c, p in fdmap.items():
                        if p == child:
                            fdmap[c] = newtarget # update all pointers
                if debug: print >>errfd, "os.dup2(%d,%d)" % (target, child)
                os.dup2(target, child)
        old = []
        for fd in fdmap.values():
            if not fd in old:
                if not fd in fdmap.keys():
                    old.append(fd)
        if debug: print >>errfd, "old", old
        for fd in old:
            os.close(fd)

        self._resetSignalDisposition()

    def writeToChild(self, childFD, data):
        self.pipes[childFD].write(data)

    def closeChildFD(self, childFD):
        if childFD in self.pipes:
            self.pipes[childFD].loseConnection()

    def pauseProducing(self):
        for p in self.pipes.itervalues():
            if isinstance(p, ProcessReader):
                p.stopReading()

    def resumeProducing(self):
        for p in self.pipes.itervalues():
            if isinstance(p, ProcessReader):
                p.startReading()

    def closeStdin(self):
        self.closeChildFD(0)

    def closeStdout(self):
        self.closeChildFD(1)

    def closeStderr(self):
        self.closeChildFD(2)

    def loseConnection(self):
        self.closeStdin()
        self.closeStderr()
        self.closeStdout()

    def write(self, data):
        if 0 in self.pipes:
            self.pipes[0].write(data)

    def registerProducer(self, producer, streaming):
        if 0 in self.pipes:
            self.pipes[0].registerProducer(producer, streaming)
        else:
            producer.stopProducing()

    def unregisterProducer(self):
        if 0 in self.pipes:
            self.pipes[0].unregisterProducer()

    def writeSequence(self, seq):
        if 0 in self.pipes:
            self.pipes[0].writeSequence(seq)

    def childDataReceived(self, name, data):
        self.proto.childDataReceived(name, data)

    def childConnectionLost(self, childFD, reason):
        os.close(self.pipes[childFD].fileno())
        del self.pipes[childFD]
        try:
            self.proto.childConnectionLost(childFD)
        except:
            log.err()
        self.maybeCallProcessEnded()

    def maybeCallProcessEnded(self):
        if self.pipes:
            return
        if not self.lostProcess:
            self.reapProcess()
            return
        _BaseProcess.maybeCallProcessEnded(self)

class PTYProcess(abstract.FileDescriptor, _BaseProcess):

    status = -1
    pid = None

    def __init__(self, reactor, executable, args, environment, path, proto,
                 uid=None, gid=None, usePTY=None):
        if pty is None and not isinstance(usePTY, (tuple, list)):
            raise NotImplementedError(
                "cannot use PTYProcess on platforms without the pty module.")
        abstract.FileDescriptor.__init__(self, reactor)
        _BaseProcess.__init__(self, proto)

        if isinstance(usePTY, (tuple, list)):
            masterfd, slavefd, ttyname = usePTY
        else:
            masterfd, slavefd = pty.openpty()
            ttyname = os.ttyname(slavefd)

        try:
            self._fork(path, uid, gid, executable, args, environment,
                       masterfd=masterfd, slavefd=slavefd)
        except:
            if not isinstance(usePTY, (tuple, list)):
                os.close(masterfd)
                os.close(slavefd)
            raise

        os.close(slavefd)
        fdesc.setNonBlocking(masterfd)
        self.fd = masterfd
        self.startReading()
        self.connected = 1
        self.status = -1
        try:
            self.proto.makeConnection(self)
        except:
            log.err()
        registerReapProcessHandler(self.pid, self)

    def _setupChild(self, masterfd, slavefd):
        os.close(masterfd)
        if hasattr(termios, 'TIOCNOTTY'):
            try:
                fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
            except OSError:
                pass
            else:
                try:
                    fcntl.ioctl(fd, termios.TIOCNOTTY, '')
                except:
                    pass
                os.close(fd)

        os.setsid()

        if hasattr(termios, 'TIOCSCTTY'):
            fcntl.ioctl(slavefd, termios.TIOCSCTTY, '')

        for fd in range(3):
            if fd != slavefd:
                os.close(fd)

        os.dup2(slavefd, 0) # stdin
        os.dup2(slavefd, 1) # stdout
        os.dup2(slavefd, 2) # stderr

        for fd in xrange(3, 256):
            try:
                os.close(fd)
            except:
                pass

        self._resetSignalDisposition()

    def closeStdin(self):
        pass

    def closeStdout(self):
        pass

    def closeStderr(self):
        pass

    def doRead(self):
        return fdesc.readFromFD(
            self.fd,
            lambda data: self.proto.childDataReceived(1, data))

    def fileno(self):
        """
        This returns the file number of standard output on this process.
        """
        return self.fd

    def maybeCallProcessEnded(self):
        if self.lostProcess == 2:
            _BaseProcess.maybeCallProcessEnded(self)

    def connectionLost(self, reason):
        abstract.FileDescriptor.connectionLost(self, reason)
        os.close(self.fd)
        self.lostProcess += 1
        self.maybeCallProcessEnded()

    def writeSomeData(self, data):
        return fdesc.writeToFD(self.fd, data)
