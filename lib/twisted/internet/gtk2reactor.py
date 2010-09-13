# -*- test-case-name: lib.twisted.internet.test -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

import sys, signal
from lib.zope.interface import implements
try:
    if not hasattr(sys, 'frozen'):
        import pygtk
        pygtk.require('2.0')
except (ImportError, AttributeError):
    pass
import gobject
if hasattr(gobject, "threads_init"):
    gobject.threads_init()
from lib.twisted.python import log, runtime, failure
from lib.twisted.python.compat import set
from lib.twisted.internet.interfaces import IReactorFDSet
from lib.twisted.internet import main, base, posixbase, error, selectreactor
POLL_DISCONNECTED = gobject.IO_HUP | gobject.IO_ERR | gobject.IO_NVAL
INFLAGS = gobject.IO_IN | POLL_DISCONNECTED
OUTFLAGS = gobject.IO_OUT | POLL_DISCONNECTED

def _our_mainquit():
    import gtk
    if gtk.main_level():
        gtk.main_quit()

class Gtk2Reactor(posixbase.PosixReactorBase):
    implements(IReactorFDSet)

    def __init__(self, useGtk=True):
        self._simtag = None
        self._reads = set()
        self._writes = set()
        self._sources = {}
        posixbase.PosixReactorBase.__init__(self)
        if getattr(gobject, "pygtk_version", ()) >= (2, 3, 91) and not useGtk:
            self.context = gobject.main_context_default()
            self.__pending = self.context.pending
            self.__iteration = self.context.iteration
            self.loop = gobject.MainLoop()
            self.__crash = self.loop.quit
            self.__run = self.loop.run
        else:
            import gtk
            self.__pending = gtk.events_pending
            self.__iteration = gtk.main_iteration
            self.__crash = _our_mainquit
            self.__run = gtk.main

    if runtime.platformType == 'posix':
        def _handleSignals(self):
            from lib.twisted.internet.process import reapAllProcesses as _reapAllProcesses
            base._SignalReactorMixin._handleSignals(self)
            signal.signal(signal.SIGCHLD, lambda *a: self.callFromThread(_reapAllProcesses))
            if getattr(signal, "siginterrupt", None) is not None:
                signal.siginterrupt(signal.SIGCHLD, False)
            _reapAllProcesses()

    def input_add(self, source, condition, callback):
        if hasattr(source, 'fileno'):
            def wrapper(source, condition, real_s=source, real_cb=callback):
                return real_cb(real_s, condition)
            return gobject.io_add_watch(source.fileno(), condition, wrapper)
        else:
            return gobject.io_add_watch(source, condition, callback)

    def _add(self, source, primary, other, primaryFlag, otherFlag):
        if source in primary:
            return
        flags = primaryFlag
        if source in other:
            gobject.source_remove(self._sources[source])
            flags |= otherFlag
        self._sources[source] = self.input_add(source, flags, self.callback)
        primary.add(source)

    def addReader(self, reader):
        self._add(reader, self._reads, self._writes, INFLAGS, OUTFLAGS)

    def addWriter(self, writer):
        self._add(writer, self._writes, self._reads, OUTFLAGS, INFLAGS)

    def getReaders(self):
        return list(self._reads)

    def getWriters(self):
        return list(self._writes)

    def removeAll(self):
        return self._removeAll(self._reads, self._writes)

    def _remove(self, source, primary, other, flags):
        if source not in primary:
            return
        gobject.source_remove(self._sources[source])
        primary.remove(source)
        if source in other:
            self._sources[source] = self.input_add(
                source, flags, self.callback)
        else:
            self._sources.pop(source)

    def removeReader(self, reader):
        self._remove(reader, self._reads, self._writes, OUTFLAGS)

    def removeWriter(self, writer):
        self._remove(writer, self._writes, self._reads, INFLAGS)

    doIterationTimer = None

    def doIterationTimeout(self, *args):
        self.doIterationTimer = None
        return 0

    def doIteration(self, delay):
        log.msg(channel='system', event='iteration', reactor=self)
        if self.__pending():
            self.__iteration(0)
            return
        if delay == 0:
            return
        self.doIterationTimer = gobject.timeout_add(int(delay * 1000),
                                                self.doIterationTimeout)
        self.__iteration(1)
        if self.doIterationTimer:
            gobject.source_remove(self.doIterationTimer)
            self.doIterationTimer = None

    def crash(self):
        posixbase.PosixReactorBase.crash(self)
        self.__crash()

    def run(self, installSignalHandlers=1):
        self.startRunning(installSignalHandlers=installSignalHandlers)
        gobject.timeout_add(0, self.simulate)
        if self._started:
            self.__run()

    def _doReadOrWrite(self, source, condition, faildict={
        error.ConnectionDone: failure.Failure(error.ConnectionDone()),
        error.ConnectionLost: failure.Failure(error.ConnectionLost()),
        }):
        why = None
        inRead = False
        if condition & POLL_DISCONNECTED and not (condition & gobject.IO_IN):
            if source in self._reads:
                why = main.CONNECTION_DONE
                inRead = True
            else:
                why = main.CONNECTION_LOST
        else:
            try:
                if condition & gobject.IO_IN:
                    why = source.doRead()
                    inRead = True
                if not why and condition & gobject.IO_OUT:
                    if not source.disconnected:
                        why = source.doWrite()
            except:
                why = sys.exc_info()[1]
                log.msg('Error In %s' % source)
                log.deferr()
        if why:
            self._disconnectSelectable(source, why, inRead)

    def callback(self, source, condition):
        log.callWithLogger(source, self._doReadOrWrite, source, condition)
        self.simulate()
        return 1

    def simulate(self):
        if self._simtag is not None:
            gobject.source_remove(self._simtag)
        self.runUntilCurrent()
        timeout = min(self.timeout(), 0.1)
        if timeout is None:
            timeout = 0.1
        self._simtag = gobject.timeout_add(int(timeout * 1010), self.simulate)

class PortableGtkReactor(selectreactor.SelectReactor):
    _simtag = None

    def crash(self):
        selectreactor.SelectReactor.crash(self)
        import gtk
        if gtk.main_level():
            if hasattr(gtk, 'main_quit'):
                gtk.main_quit()
            else:
                gtk.mainquit()

    def run(self, installSignalHandlers=1):
        import gtk
        self.startRunning(installSignalHandlers=installSignalHandlers)
        gobject.timeout_add(0, self.simulate)
        if hasattr(gtk, 'main'):
            gtk.main()
        else:
            gtk.mainloop()

    def simulate(self):
        if self._simtag is not None:
            gobject.source_remove(self._simtag)
        self.iterate()
        timeout = min(self.timeout(), 0.1)
        if timeout is None:
            timeout = 0.1
        self._simtag = gobject.timeout_add(int(timeout * 1010), self.simulate)

def install(useGtk=True):
    reactor = Gtk2Reactor(useGtk)
    from lib.twisted.internet.main import installReactor
    installReactor(reactor)
    return reactor

def portableInstall(useGtk=True):
    reactor = PortableGtkReactor()
    from lib.twisted.internet.main import installReactor
    installReactor(reactor)
    return reactor

if runtime.platform.getType() != 'posix':
    install = portableInstall
__all__ = ['install']
