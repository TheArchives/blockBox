# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import errno, sys
from lib.zope.interface import implements
from kqsyscall import EVFILT_READ, EVFILT_WRITE, EV_DELETE, EV_ADD
from kqsyscall import kqueue, kevent
from lib.twisted.internet.interfaces import IReactorFDSet
from lib.twisted.python import log, failure
from lib.twisted.internet import main, posixbase

class KQueueReactor(posixbase.PosixReactorBase):
    implements(IReactorFDSet)

    def __init__(self):
        self._kq = kqueue()
        self._reads = {}
        self._writes = {}
        self._selectables = {}
        posixbase.PosixReactorBase.__init__(self)

    def _updateRegistration(self, *args):
        self._kq.kevent([kevent(*args)], 0, 0)

    def addReader(self, reader):
        fd = reader.fileno()
        if fd not in self._reads:
            self._selectables[fd] = reader
            self._reads[fd] = 1
            self._updateRegistration(fd, EVFILT_READ, EV_ADD)

    def addWriter(self, writer):
        fd = writer.fileno()
        if fd not in self._writes:
            self._selectables[fd] = writer
            self._writes[fd] = 1
            self._updateRegistration(fd, EVFILT_WRITE, EV_ADD)

    def removeReader(self, reader):
        fd = reader.fileno()
        if fd in self._reads:
            del self._reads[fd]
            if fd not in self._writes:
                del self._selectables[fd]
            self._updateRegistration(fd, EVFILT_READ, EV_DELETE)

    def removeWriter(self, writer):
        fd = writer.fileno()
        if fd in self._writes:
            del self._writes[fd]
            if fd not in self._reads:
                del self._selectables[fd]
            self._updateRegistration(fd, EVFILT_WRITE, EV_DELETE)

    def removeAll(self):
        return self._removeAll(
            [self._selectables[fd] for fd in self._reads],
            [self._selectables[fd] for fd in self._writes])

    def getReaders(self):
        return [self._selectables[fd] for fd in self._reads]

    def getWriters(self):
        return [self._selectables[fd] for fd in self._writes]

    def doKEvent(self, timeout):
        if timeout is None:
            timeout = 1000
        else:
            timeout = int(timeout * 1000)

        try:
            l = self._kq.kevent([], len(self._selectables), timeout)
        except OSError, e:
            if e[0] == errno.EINTR:
                return
            else:
                raise
        _drdw = self._doWriteOrRead
        for event in l:
            why = None
            fd, filter = event.ident, event.filter
            try:
                selectable = self._selectables[fd]
            except KeyError:
                continue
            log.callWithLogger(selectable, _drdw, selectable, fd, filter)

    def _doWriteOrRead(self, selectable, fd, filter):
        try:
            if filter == EVFILT_READ:
                why = selectable.doRead()
            if filter == EVFILT_WRITE:
                why = selectable.doWrite()
            if not selectable.fileno() == fd:
                why = main.CONNECTION_LOST
        except:
            why = sys.exc_info()[1]
            log.deferr()

        if why:
            self.removeReader(selectable)
            self.removeWriter(selectable)
            selectable.connectionLost(failure.Failure(why))

    doIteration = doKEvent

def install():
    k = KQueueReactor()
    main.installReactor(k)

__all__ = ["KQueueReactor", "install"]
