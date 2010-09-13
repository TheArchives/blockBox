# -*- test-case-name: lib.twisted.test.test_internet -*-
# Copyright (c) 2001-2007 Twisted Matrix Laboratories.
# See LICENSE for details.
from time import sleep
import sys
import select
from errno import EINTR, EBADF
from lib.zope.interface import implements
from lib.twisted.internet.interfaces import IReactorFDSet
from lib.twisted.internet import error
from lib.twisted.internet import posixbase
from lib.twisted.python import log
from lib.twisted.python.runtime import platformType

def win32select(r, w, e, timeout=None):
    """Win32 select wrapper."""
    if not (r or w):
        if timeout is None:
            timeout = 0.01
        else:
            timeout = min(timeout, 0.001)
        sleep(timeout)
        return [], [], []
    if timeout is None or timeout > 0.5:
        timeout = 0.5
    r, w, e = select.select(r, w, w, timeout)
    return r, w + e, []
if platformType == "win32":
    _select = win32select
else:
    _select = select.select
_NO_FILENO = error.ConnectionFdescWentAway('Handler has no fileno method')
_NO_FILEDESC = error.ConnectionFdescWentAway('Filedescriptor went away')

class SelectReactor(posixbase.PosixReactorBase):
    implements(IReactorFDSet)

    def __init__(self):
        self._reads = {}
        self._writes = {}
        posixbase.PosixReactorBase.__init__(self)

    def _preenDescriptors(self):
        log.msg("Malformed file descriptor found.  Preening lists.")
        readers = self._reads.keys()
        writers = self._writes.keys()
        self._reads.clear()
        self._writes.clear()
        for selDict, selList in ((self._reads, readers),
                                 (self._writes, writers)):
            for selectable in selList:
                try:
                    select.select([selectable], [selectable], [selectable], 0)
                except Exception, e:
                    log.msg("bad descriptor %s" % selectable)
                    self._disconnectSelectable(selectable, e, False)
                else:
                    selDict[selectable] = 1

    def doSelect(self, timeout):
        while 1:
            try:
                r, w, ignored = _select(self._reads.keys(),
                                        self._writes.keys(),
                                        [], timeout)
                break
            except ValueError, ve:
                log.err()
                self._preenDescriptors()
            except TypeError, te:
                log.err()
                self._preenDescriptors()
            except (select.error, IOError), se:
                if se.args[0] in (0, 2):
                    if (not self._reads) and (not self._writes):
                        return
                    else:
                        raise
                elif se.args[0] == EINTR:
                    return
                elif se.args[0] == EBADF:
                    self._preenDescriptors()
                else:
                    raise
        _drdw = self._doReadOrWrite
        _logrun = log.callWithLogger
        for selectables, method, fdset in ((r, "doRead", self._reads),
                                           (w,"doWrite", self._writes)):
            for selectable in selectables:
                if selectable not in fdset:
                    continue
                _logrun(selectable, _drdw, selectable, method, dict)

    doIteration = doSelect

    def _doReadOrWrite(self, selectable, method, dict):
        try:
            why = getattr(selectable, method)()
            handfn = getattr(selectable, 'fileno', None)
            if not handfn:
                why = _NO_FILENO
            elif handfn() == -1:
                why = _NO_FILEDESC
        except:
            why = sys.exc_info()[1]
            log.err()
        if why:
            self._disconnectSelectable(selectable, why, method=="doRead")

    def addReader(self, reader):
        self._reads[reader] = 1

    def addWriter(self, writer):
        self._writes[writer] = 1

    def removeReader(self, reader):
        if reader in self._reads:
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

def install():
    reactor = SelectReactor()
    from lib.twisted.internet.main import installReactor
    installReactor(reactor)

__all__ = ['install']
