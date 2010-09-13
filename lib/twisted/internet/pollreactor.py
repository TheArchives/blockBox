# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import errno, sys
from select import error as SelectError, poll
from select import POLLIN, POLLOUT, POLLHUP, POLLERR, POLLNVAL
from lib.zope.interface import implements
from lib.twisted.python import log
from lib.twisted.internet import main, posixbase, error
from lib.twisted.internet.interfaces import IReactorFDSet
POLL_DISCONNECTED = (POLLHUP | POLLERR | POLLNVAL)

class PollReactor(posixbase.PosixReactorBase):
    implements(IReactorFDSet)

    def __init__(self):
        self._poller = poll()
        self._selectables = {}
        self._reads = {}
        self._writes = {}
        posixbase.PosixReactorBase.__init__(self)

    def _updateRegistration(self, fd):
        try:
            self._poller.unregister(fd)
        except KeyError:
            pass

        mask = 0
        if fd in self._reads:
            mask = mask | POLLIN
        if fd in self._writes:
            mask = mask | POLLOUT
        if mask != 0:
            self._poller.register(fd, mask)
        else:
            if fd in self._selectables:
                del self._selectables[fd]

    def _dictRemove(self, selectable, mdict):
        try:
            fd = selectable.fileno()
            mdict[fd]
        except:
            for fd, fdes in self._selectables.items():
                if selectable is fdes:
                    break
            else:
                return
        if fd in mdict:
            del mdict[fd]
            self._updateRegistration(fd)

    def addReader(self, reader):
        fd = reader.fileno()
        if fd not in self._reads:
            self._selectables[fd] = reader
            self._reads[fd] =  1
            self._updateRegistration(fd)

    def addWriter(self, writer):
        fd = writer.fileno()
        if fd not in self._writes:
            self._selectables[fd] = writer
            self._writes[fd] =  1
            self._updateRegistration(fd)

    def removeReader(self, reader):
        return self._dictRemove(reader, self._reads)

    def removeWriter(self, writer):
        return self._dictRemove(writer, self._writes)

    def removeAll(self):
        return self._removeAll(
            [self._selectables[fd] for fd in self._reads],
            [self._selectables[fd] for fd in self._writes])

    def doPoll(self, timeout):
        if timeout is not None:
            timeout = int(timeout * 1000)
        try:
            l = self._poller.poll(timeout)
        except SelectError, e:
            if e[0] == errno.EINTR:
                return
            else:
                raise
        _drdw = self._doReadOrWrite
        for fd, event in l:
            try:
                selectable = self._selectables[fd]
            except KeyError:
                continue
            log.callWithLogger(selectable, _drdw, selectable, fd, event)

    doIteration = doPoll

    def _doReadOrWrite(self, selectable, fd, event):
        why = None
        inRead = False
        if event & POLL_DISCONNECTED and not (event & POLLIN):
            if fd in self._reads:
                why = main.CONNECTION_DONE
                inRead = True
            else:
                why = main.CONNECTION_LOST
        else:
            try:
                if event & POLLIN:
                    why = selectable.doRead()
                    inRead = True
                if not why and event & POLLOUT:
                    why = selectable.doWrite()
                    inRead = False
                if not selectable.fileno() == fd:
                    why = error.ConnectionFdescWentAway('Filedescriptor went away')
                    inRead = False
            except:
                log.deferr()
                why = sys.exc_info()[1]
        if why:
            self._disconnectSelectable(selectable, why, inRead)

    def getReaders(self):
        return [self._selectables[fd] for fd in self._reads]

    def getWriters(self):
        return [self._selectables[fd] for fd in self._writes]

def install():
    """Install the poll() reactor."""
    p = PollReactor()
    from lib.twisted.internet.main import installReactor
    installReactor(p)

__all__ = ["PollReactor", "install"]
