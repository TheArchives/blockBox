# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import sys, errno
from lib.zope.interface import implements
from lib.twisted.internet.interfaces import IReactorFDSet
from lib.twisted.python import _epoll
from lib.twisted.python import log
from lib.twisted.internet import posixbase, error
from lib.twisted.internet.main import CONNECTION_DONE, CONNECTION_LOST
_POLL_DISCONNECTED = (_epoll.HUP | _epoll.ERR)

class EPollReactor(posixbase.PosixReactorBase):
    implements(IReactorFDSet)

    def __init__(self):
        self._poller = _epoll.epoll(1024)
        self._reads = {}
        self._writes = {}
        self._selectables = {}
        posixbase.PosixReactorBase.__init__(self)

    def _add(self, xer, primary, other, selectables, event, antievent):
        fd = xer.fileno()
        if fd not in primary:
            cmd = _epoll.CTL_ADD
            flags = event
            if fd in other:
                flags |= antievent
                cmd = _epoll.CTL_MOD
            self._poller._control(cmd, fd, flags)
            primary[fd] = 1
            selectables[fd] = xer

    def addReader(self, reader):
        self._add(reader, self._reads, self._writes, self._selectables, _epoll.IN, _epoll.OUT)

    def addWriter(self, writer):
        self._add(writer, self._writes, self._reads, self._selectables, _epoll.OUT, _epoll.IN)

    def _remove(self, xer, primary, other, selectables, event, antievent):
        fd = xer.fileno()
        if fd == -1:
            for fd, fdes in selectables.items():
                if xer is fdes:
                    break
            else:
                return
        if fd in primary:
            cmd = _epoll.CTL_DEL
            flags = event
            if fd in other:
                flags = antievent
                cmd = _epoll.CTL_MOD
            else:
                del selectables[fd]
            del primary[fd]
            self._poller._control(cmd, fd, flags)

    def removeReader(self, reader):
        self._remove(reader, self._reads, self._writes, self._selectables, _epoll.IN, _epoll.OUT)

    def removeWriter(self, writer):
        self._remove(writer, self._writes, self._reads, self._selectables, _epoll.OUT, _epoll.IN)

    def removeAll(self):
        return self._removeAll(
            [self._selectables[fd] for fd in self._reads],
            [self._selectables[fd] for fd in self._writes])

    def getReaders(self):
        return [self._selectables[fd] for fd in self._reads]

    def getWriters(self):
        return [self._selectables[fd] for fd in self._writes]

    def doPoll(self, timeout):
        if timeout is None:
            timeout = 1
        timeout = int(timeout * 1000)
        try:
            l = self._poller.wait(len(self._selectables), timeout)
        except IOError, err:
            if err.errno == errno.EINTR:
                return
            raise

        _drdw = self._doReadOrWrite
        for fd, event in l:
            try:
                selectable = self._selectables[fd]
            except KeyError:
                pass
            else:
                log.callWithLogger(selectable, _drdw, selectable, fd, event)
    doIteration = doPoll

    def _doReadOrWrite(self, selectable, fd, event):
        why = None
        inRead = False
        if event & _POLL_DISCONNECTED and not (event & _epoll.IN):
            if fd in self._reads:
                inRead = True
                why = CONNECTION_DONE
            else:
                why = CONNECTION_LOST
        else:
            try:
                if event & _epoll.IN:
                    why = selectable.doRead()
                    inRead = True
                if not why and event & _epoll.OUT:
                    why = selectable.doWrite()
                    inRead = False
                if selectable.fileno() != fd:
                    why = error.ConnectionFdescWentAway(
                          'Filedescriptor went away')
                    inRead = False
            except:
                log.err()
                why = sys.exc_info()[1]
        if why:
            self._disconnectSelectable(selectable, why, inRead)

def install():
    p = EPollReactor()
    from lib.twisted.internet.main import installReactor
    installReactor(p)
__all__ = ["EPollReactor", "install"]
