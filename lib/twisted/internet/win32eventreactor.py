# Copyright (c) 2001-2007 Twisted Matrix Laboratories.
# See LICENSE for details.
import time
import sys
from lib.zope.interface import implements
from win32file import WSAEventSelect, FD_READ, FD_CLOSE, FD_ACCEPT, FD_CONNECT
from win32event import CreateEvent, MsgWaitForMultipleObjects
from win32event import WAIT_OBJECT_0, WAIT_TIMEOUT, QS_ALLINPUT, QS_ALLEVENTS
import win32gui
from lib.twisted.internet import posixbase
from lib.twisted.python import log, threadable, failure
from lib.twisted.internet.interfaces import IReactorFDSet, IReactorProcess
from lib.twisted.internet._dumbwin32proc import Process

class Win32Reactor(posixbase.PosixReactorBase):
    implements(IReactorFDSet, IReactorProcess)
    dummyEvent = CreateEvent(None, 0, 0, None)
    def __init__(self):
        self._reads = {}
        self._writes = {}
        self._events = {}
        posixbase.PosixReactorBase.__init__(self)

    def _makeSocketEvent(self, fd, action, why):
        event = CreateEvent(None, 0, 0, None)
        WSAEventSelect(fd, event, why)
        self._events[event] = (fd, action)
        return event

    def addEvent(self, event, fd, action):
        self._events[event] = (fd, action)

    def removeEvent(self, event):
        del self._events[event]

    def addReader(self, reader):
        if reader not in self._reads:
            self._reads[reader] = self._makeSocketEvent(
                reader, 'doRead', FD_READ | FD_ACCEPT | FD_CONNECT | FD_CLOSE)

    def addWriter(self, writer):
        if writer not in self._writes:
            self._writes[writer] = 1

    def removeReader(self, reader):
        if reader in self._reads:
            del self._events[self._reads[reader]]
            del self._reads[reader]

    def removeWriter(self, writer):
        if writer in self._writes:
            del self._writes[writer]

    def removeAll(self):
        return self._removeAll(self._reads, self._writes)

    def getReaders(self):
        return self._reads.keys()

    def getWriters(self):
        return self._writes.keys()

    def doWaitForMultipleEvents(self, timeout):
        log.msg(channel='system', event='iteration', reactor=self)
        if timeout is None:
            timeout = 100
        else:
            timeout = int(timeout * 1000)

        if not (self._events or self._writes):
            time.sleep(timeout / 1000.0)
            return

        canDoMoreWrites = 0
        for fd in self._writes.keys():
            if log.callWithLogger(fd, self._runWrite, fd):
                canDoMoreWrites = 1

        if canDoMoreWrites:
            timeout = 0
        handles = self._events.keys() or [self.dummyEvent]
        val = MsgWaitForMultipleObjects(handles, 0, timeout, QS_ALLINPUT | QS_ALLEVENTS)
        if val == WAIT_TIMEOUT:
            return
        elif val == WAIT_OBJECT_0 + len(handles):
            exit = win32gui.PumpWaitingMessages()
            if exit:
                self.callLater(0, self.stop)
                return
        elif val >= WAIT_OBJECT_0 and val < WAIT_OBJECT_0 + len(handles):
            fd, action = self._events[handles[val - WAIT_OBJECT_0]]
            log.callWithLogger(fd, self._runAction, action, fd)

    def _runWrite(self, fd):
        closed = 0
        try:
            closed = fd.doWrite()
        except:
            closed = sys.exc_info()[1]
            log.deferr()

        if closed:
            self.removeReader(fd)
            self.removeWriter(fd)
            try:
                fd.connectionLost(failure.Failure(closed))
            except:
                log.deferr()
        elif closed is None:
            return 1

    def _runAction(self, action, fd):
        try:
            closed = getattr(fd, action)()
        except:
            closed = sys.exc_info()[1]
            log.deferr()

        if closed:
            self._disconnectSelectable(fd, closed, action == 'doRead')

    doIteration = doWaitForMultipleEvents

    def spawnProcess(self, processProtocol, executable, args=(), env={}, path=None, uid=None, gid=None, usePTY=0, childFDs=None):
        if uid is not None:
            raise ValueError("Setting UID is unsupported on this platform.")
        if gid is not None:
            raise ValueError("Setting GID is unsupported on this platform.")
        if usePTY:
            raise ValueError("PTYs are unsupported on this platform.")
        if childFDs is not None:
            raise ValueError(
                "Custom child file descriptor mappings are unsupported on "
                "this platform.")
        args, env = self._checkProcessArgs(args, env)
        return Process(self, processProtocol, executable, args, env, path)

def install():
    threadable.init(1)
    r = Win32Reactor()
    import main
    main.installReactor(r)
__all__ = ["Win32Reactor", "install"]
