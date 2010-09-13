# -*- test-case-name: lib.twisted.test.test_internet,lib.twisted.internet.test.test_posixbase -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

import warnings
import socket
import errno
import os
from lib.zope.interface import implements, classImplements
from lib.twisted.python.compat import set
from lib.twisted.internet.interfaces import IReactorUNIX, IReactorUNIXDatagram
from lib.twisted.internet.interfaces import IReactorTCP, IReactorUDP, IReactorSSL, _IReactorArbitrary
from lib.twisted.internet.interfaces import IReactorProcess, IReactorMulticast
from lib.twisted.internet.interfaces import IHalfCloseableDescriptor
from lib.twisted.internet import error
from lib.twisted.internet import tcp, udp
from lib.twisted.python import log, failure, util
from lib.twisted.persisted import styles
from lib.twisted.python.runtime import platformType, platform
from lib.twisted.internet.base import ReactorBase, _SignalReactorMixin

try:
    from lib.twisted.internet import ssl
    sslEnabled = True
except ImportError:
    sslEnabled = False

try:
    from lib.twisted.internet import unix
    unixEnabled = True
except ImportError:
    unixEnabled = False

processEnabled = False
if platformType == 'posix':
    from lib.twisted.internet import fdesc, process, _signals
    processEnabled = True

if platform.isWindows():
    try:
        import win32process
        processEnabled = True
    except ImportError:
        win32process = None

class _SocketWaker(log.Logger, styles.Ephemeral):
    disconnected = 0

    def __init__(self, reactor):
        self.reactor = reactor
        # Following select_trigger (from asyncore)'s example;
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server.bind(('127.0.0.1', 0))
        server.listen(1)
        client.connect(server.getsockname())
        reader, clientaddr = server.accept()
        client.setblocking(0)
        reader.setblocking(0)
        self.r = reader
        self.w = client
        self.fileno = self.r.fileno

    def wakeUp(self):
        try:
            util.untilConcludes(self.w.send, 'x')
        except socket.error, (err, msg):
            if err != errno.WSAEWOULDBLOCK:
                raise

    def doRead(self):
        try:
            self.r.recv(8192)
        except socket.error:
            pass

    def connectionLost(self, reason):
        self.r.close()
        self.w.close()

class _FDWaker(object, log.Logger, styles.Ephemeral):
    disconnected = 0

    i = None
    o = None

    def __init__(self, reactor):
        """Initialize.
        """
        self.reactor = reactor
        self.i, self.o = os.pipe()
        fdesc.setNonBlocking(self.i)
        fdesc._setCloseOnExec(self.i)
        fdesc.setNonBlocking(self.o)
        fdesc._setCloseOnExec(self.o)
        self.fileno = lambda: self.i

    def doRead(self):
        fdesc.readFromFD(self.fileno(), lambda data: None)

    def connectionLost(self, reason):
        if not hasattr(self, "o"):
            return
        for fd in self.i, self.o:
            try:
                os.close(fd)
            except IOError:
                pass
        del self.i, self.o

class _UnixWaker(_FDWaker):

    def wakeUp(self):
        if self.o is not None:
            try:
                util.untilConcludes(os.write, self.o, 'x')
            except OSError, e:
                if e.errno != errno.EAGAIN:
                    raise

if platformType == 'posix':
    _Waker = _UnixWaker
else:
    _Waker = _SocketWaker

class _SIGCHLDWaker(_FDWaker):
    def __init__(self, reactor):
        _FDWaker.__init__(self, reactor)

    def install(self):
        _signals.installHandler(self.o)

    def uninstall(self):
        _signals.installHandler(-1)

    def doRead(self):
        _FDWaker.doRead(self)
        process.reapAllProcesses()

class PosixReactorBase(_SignalReactorMixin, ReactorBase):
    implements(_IReactorArbitrary, IReactorTCP, IReactorUDP, IReactorMulticast)

    def _disconnectSelectable(self, selectable, why, isRead, faildict={
        error.ConnectionDone: failure.Failure(error.ConnectionDone()),
        error.ConnectionLost: failure.Failure(error.ConnectionLost())
        }):
        self.removeReader(selectable)
        f = faildict.get(why.__class__)
        if f:
            if (isRead and why.__class__ ==  error.ConnectionDone
                and IHalfCloseableDescriptor.providedBy(selectable)):
                selectable.readConnectionLost(f)
            else:
                self.removeWriter(selectable)
                selectable.connectionLost(f)
        else:
            self.removeWriter(selectable)
            selectable.connectionLost(failure.Failure(why))

    def installWaker(self):
        if not self.waker:
            self.waker = _Waker(self)
            self._internalReaders.add(self.waker)
            self.addReader(self.waker)

    _childWaker = None
    def _handleSignals(self):
        _SignalReactorMixin._handleSignals(self)
        if platformType == 'posix':
            if not self._childWaker:
                self._childWaker = _SIGCHLDWaker(self)
                self._internalReaders.add(self._childWaker)
                self.addReader(self._childWaker)
            self._childWaker.install()
            process.reapAllProcesses()

    def _uninstallHandler(self):
        if self._childWaker:
            self._childWaker.uninstall()

    def spawnProcess(self, processProtocol, executable, args=(),
                     env={}, path=None,
                     uid=None, gid=None, usePTY=0, childFDs=None):
        args, env = self._checkProcessArgs(args, env)
        if platformType == 'posix':
            if usePTY:
                if childFDs is not None:
                    raise ValueError("Using childFDs is not supported with usePTY=True.")
                return process.PTYProcess(self, executable, args, env, path,
                                          processProtocol, uid, gid, usePTY)
            else:
                return process.Process(self, executable, args, env, path,
                                       processProtocol, uid, gid, childFDs)
        elif platformType == "win32":
            if uid is not None or gid is not None:
                raise ValueError("The uid and gid parameters are not supported on Windows.")
            if usePTY:
                raise ValueError("The usePTY parameter is not supported on Windows.")
            if childFDs:
                raise ValueError("Customizing childFDs is not supported on Windows.")

            if win32process:
                from lib.twisted.internet._dumbwin32proc import Process
                return Process(self, processProtocol, executable, args, env, path)
            else:
                raise NotImplementedError, "spawnProcess not available since pywin32 is not installed."
        else:
            raise NotImplementedError, "spawnProcess only available on Windows or POSIX."

    def listenUDP(self, port, protocol, interface='', maxPacketSize=8192):
        p = udp.Port(port, protocol, interface, maxPacketSize, self)
        p.startListening()
        return p

    def listenMulticast(self, port, protocol, interface='', maxPacketSize=8192, listenMultiple=False):
        p = udp.MulticastPort(port, protocol, interface, maxPacketSize, self, listenMultiple)
        p.startListening()
        return p

    def connectUNIX(self, address, factory, timeout=30, checkPID=0):
        assert unixEnabled, "UNIX support is not present"
        c = unix.Connector(address, factory, timeout, self, checkPID)
        c.connect()
        return c

    def listenUNIX(self, address, factory, backlog=50, mode=0666, wantPID=0):
        assert unixEnabled, "UNIX support is not present"
        p = unix.Port(address, factory, backlog, mode, self, wantPID)
        p.startListening()
        return p

    def listenUNIXDatagram(self, address, protocol, maxPacketSize=8192,
                           mode=0666):
        assert unixEnabled, "UNIX support is not present"
        p = unix.DatagramPort(address, protocol, maxPacketSize, mode, self)
        p.startListening()
        return p

    def connectUNIXDatagram(self, address, protocol, maxPacketSize=8192,
                            mode=0666, bindAddress=None):
        assert unixEnabled, "UNIX support is not present"
        p = unix.ConnectedDatagramPort(address, protocol, maxPacketSize, mode, bindAddress, self)
        p.startListening()
        return p

    def listenTCP(self, port, factory, backlog=50, interface=''):
        p = tcp.Port(port, factory, backlog, interface, self)
        p.startListening()
        return p

    def connectTCP(self, host, port, factory, timeout=30, bindAddress=None):
        c = tcp.Connector(host, port, factory, timeout, bindAddress, self)
        c.connect()
        return c

    def connectSSL(self, host, port, factory, contextFactory, timeout=30, bindAddress=None):
        assert sslEnabled, "SSL support is not present"
        c = ssl.Connector(host, port, factory, contextFactory, timeout, bindAddress, self)
        c.connect()
        return c

    def listenSSL(self, port, factory, contextFactory, backlog=50, interface=''):
        assert sslEnabled, "SSL support is not present"
        p = ssl.Port(port, factory, contextFactory, backlog, interface, self)
        p.startListening()
        return p

    def listenWith(self, portType, *args, **kw):
        warnings.warn(
            "listenWith is deprecated since Twisted 10.1.  "
            "See IReactorFDSet.",
            category=DeprecationWarning,
            stacklevel=2)
        kw['reactor'] = self
        p = portType(*args, **kw)
        p.startListening()
        return p

    def connectWith(self, connectorType, *args, **kw):
        warnings.warn(
            "connectWith is deprecated since Twisted 10.1.  "
            "See IReactorFDSet.",
            category=DeprecationWarning,
            stacklevel=2)
        kw['reactor'] = self
        c = connectorType(*args, **kw)
        c.connect()
        return c

    def _removeAll(self, readers, writers):
        removedReaders = set(readers) - self._internalReaders
        for reader in removedReaders:
            self.removeReader(reader)

        removedWriters = set(writers)
        for writer in removedWriters:
            self.removeWriter(writer)

        return list(removedReaders | removedWriters)

if sslEnabled:
    classImplements(PosixReactorBase, IReactorSSL)
if unixEnabled:
    classImplements(PosixReactorBase, IReactorUNIX, IReactorUNIXDatagram)
if processEnabled:
    classImplements(PosixReactorBase, IReactorProcess)

__all__ = ["PosixReactorBase"]
