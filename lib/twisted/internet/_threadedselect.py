# -*- test-case-name: twisted.test.test_internet -*-
# $Id: default.py,v 1.90 2004/01/06 22:35:22 warner Exp $
#
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

from __future__ import generators
from threading import Thread
from Queue import Queue, Empty
from time import sleep
import sys
from zope.interface import implements
from twisted.internet.interfaces import IReactorFDSet
from twisted.internet import error
from twisted.internet import posixbase
from twisted.python import log, failure, threadable
from twisted.persisted import styles
from twisted.python.runtime import platformType
import select
from errno import EINTR, EBADF
from twisted.internet.selectreactor import _select
_NO_FILENO = error.ConnectionFdescWentAway('Handler has no fileno method')
_NO_FILEDESC = error.ConnectionFdescWentAway('Filedescriptor went away')

def dictRemove(dct, value):
    try:
        del dct[value]
    except KeyError:
        pass

def raiseException(e):
    raise e

class ThreadedSelectReactor(posixbase.PosixReactorBase):
    implements(IReactorFDSet)

    def __init__(self):
        threadable.init(1)
        self.reads = {}
        self.writes = {}
        self.toThreadQueue = Queue()
        self.toMainThread = Queue()
        self.workerThread = None
        self.mainWaker = None
        posixbase.PosixReactorBase.__init__(self)
        self.addSystemEventTrigger('after', 'shutdown', self._mainLoopShutdown)

    def wakeUp(self):
        self.waker.wakeUp()

    def callLater(self, *args, **kw):
        tple = posixbase.PosixReactorBase.callLater(self, *args, **kw)
        self.wakeUp()
        return tple

    def _sendToMain(self, msg, *args):
        self.toMainThread.put((msg, args))
        if self.mainWaker is not None:
            self.mainWaker()

    def _sendToThread(self, fn, *args):
        self.toThreadQueue.put((fn, args))

    def _preenDescriptorsInThread(self):
        log.msg("Malformed file descriptor found.  Preening lists.")
        readers = self.reads.keys()
        writers = self.writes.keys()
        self.reads.clear()
        self.writes.clear()
        for selDict, selList in ((self.reads, readers), (self.writes, writers)):
            for selectable in selList:
                try:
                    select.select([selectable], [selectable], [selectable], 0)
                except:
                    log.msg("bad descriptor %s" % selectable)
                else:
                    selDict[selectable] = 1

    def _workerInThread(self):
        try:
            while 1:
                fn, args = self.toThreadQueue.get()
                fn(*args)
        except SystemExit:
            pass
        except:
            f = failure.Failure()
            self._sendToMain('Failure', f)

    def _doSelectInThread(self, timeout):
        reads = self.reads
        writes = self.writes
        while 1:
            try:
                r, w, ignored = _select(reads.keys(),
                                        writes.keys(),
                                        [], timeout)
                break
            except ValueError, ve:
                log.err()
                self._preenDescriptorsInThread()
            except TypeError, te:
                log.err()
                self._preenDescriptorsInThread()
            except (select.error, IOError), se:
                if se.args[0] in (0, 2):
                    if (not reads) and (not writes):
                        return
                    else:
                        raise
                elif se.args[0] == EINTR:
                    return
                elif se.args[0] == EBADF:
                    self._preenDescriptorsInThread()
                else:
                    raise
        self._sendToMain('Notify', r, w)

    def _process_Notify(self, r, w):
        reads = self.reads
        writes = self.writes

        _drdw = self._doReadOrWrite
        _logrun = log.callWithLogger
        for selectables, method, dct in ((r, "doRead", reads), (w, "doWrite", writes)):
            for selectable in selectables:
                if selectable not in dct:
                    continue
                _logrun(selectable, _drdw, selectable, method, dct)

    def _process_Failure(self, f):
        f.raiseException()

    _doIterationInThread = _doSelectInThread

    def ensureWorkerThread(self):
        if self.workerThread is None or not self.workerThread.isAlive():
            self.workerThread = Thread(target=self._workerInThread)
            self.workerThread.start()

    def doThreadIteration(self, timeout):
        self._sendToThread(self._doIterationInThread, timeout)
        self.ensureWorkerThread()
        msg, args = self.toMainThread.get()
        getattr(self, '_process_' + msg)(*args)

    doIteration = doThreadIteration

    def _interleave(self):
        while self.running:
            self.runUntilCurrent()
            t2 = self.timeout()
            t = self.running and t2
            self._sendToThread(self._doIterationInThread, t)
            yield None
            msg, args = self.toMainThread.get_nowait()
            getattr(self, '_process_' + msg)(*args)

    def interleave(self, waker, *args, **kw):
        self.startRunning(*args, **kw)
        loop = self._interleave()
        def mainWaker(waker=waker, loop=loop):
            waker(loop.next)
        self.mainWaker = mainWaker
        loop.next()
        self.ensureWorkerThread()

    def _mainLoopShutdown(self):
        self.mainWaker = None
        if self.workerThread is not None:
            self._sendToThread(raiseException, SystemExit)
            self.wakeUp()
            try:
                while 1:
                    msg, args = self.toMainThread.get_nowait()
            except Empty:
                pass
            self.workerThread.join()
            self.workerThread = None
        try:
            while 1:
                fn, args = self.toThreadQueue.get_nowait()
                if fn is self._doIterationInThread:
                    log.msg('Iteration is still in the thread queue!')
                elif fn is raiseException and args[0] is SystemExit:
                    pass
                else:
                    fn(*args)
        except Empty:
            pass

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
            self._disconnectSelectable(selectable, why, method == "doRead")

    def addReader(self, reader):
        self._sendToThread(self.reads.__setitem__, reader, 1)
        self.wakeUp()

    def addWriter(self, writer):
        self._sendToThread(self.writes.__setitem__, writer, 1)
        self.wakeUp()

    def removeReader(self, reader):
        self._sendToThread(dictRemove, self.reads, reader)

    def removeWriter(self, writer):
        self._sendToThread(dictRemove, self.writes, writer)

    def removeAll(self):
        return self._removeAll(self.reads, self.writes)

    def getReaders(self):
        return self.reads.keys()

    def getWriters(self):
        return self.writes.keys()

    def run(self, installSignalHandlers=1):
        self.startRunning(installSignalHandlers=installSignalHandlers)
        self.mainLoop()

    def mainLoop(self):
        q = Queue()
        self.interleave(q.put)
        while self.running:
            try:
                q.get()()
            except StopIteration:
                break

def install():
    reactor = ThreadedSelectReactor()
    from twisted.internet.main import installReactor
    installReactor(reactor)
    return reactor

__all__ = ['install']
