# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import sys
try:
    import pygtk
    pygtk.require('1.2')
except ImportError, AttributeError:
    pass
import gtk
from lib.zope.interface import implements
from lib.twisted.python import log, runtime, deprecate, versions
from lib.twisted.internet.interfaces import IReactorFDSet
from lib.twisted.internet import posixbase, selectreactor
deprecatedSince = versions.Version("Twisted", 10, 1, 0)
deprecationMessage = ("All new applications should be written with gtk 2.x, "
                      "which is supported by lib.twisted.internet.gtk2reactor.")
class GtkReactor(posixbase.PosixReactorBase):
    implements(IReactorFDSet)
    deprecate.deprecatedModuleAttribute(deprecatedSince, deprecationMessage,
                                        __name__, "GtkReactor")
    def __init__(self):
        self._simtag = None
        self._reads = {}
        self._writes = {}
        posixbase.PosixReactorBase.__init__(self)

    def addReader(self, reader):
        if reader not in self._reads:
            self._reads[reader] = gtk.input_add(reader, gtk.GDK.INPUT_READ, self.callback)

    def addWriter(self, writer):
        if writer not in self._writes:
            self._writes[writer] = gtk.input_add(writer, gtk.GDK.INPUT_WRITE, self.callback)

    def getReaders(self):
        return self._reads.keys()

    def getWriters(self):
        return self._writes.keys()

    def removeAll(self):
        return self._removeAll(self._reads, self._writes)

    def removeReader(self, reader):
        if reader in self._reads:
            gtk.input_remove(self._reads[reader])
            del self._reads[reader]

    def removeWriter(self, writer):
        if writer in self._writes:
            gtk.input_remove(self._writes[writer])
            del self._writes[writer]

    doIterationTimer = None

    def doIterationTimeout(self, *args):
        self.doIterationTimer = None
        return 0
    def doIteration(self, delay):
        log.msg(channel='system', event='iteration', reactor=self)
        if gtk.events_pending():
            gtk.mainiteration(0)
            return
        if delay == 0:
            return
        self.doIterationTimer = gtk.timeout_add(int(delay * 1000),
                                                self.doIterationTimeout)
        gtk.mainiteration(1)
        if self.doIterationTimer:
            gtk.timeout_remove(self.doIterationTimer)
            self.doIterationTimer = None

    def crash(self):
        posixbase.PosixReactorBase.crash(self)
        gtk.mainquit()

    def run(self, installSignalHandlers=1):
        self.startRunning(installSignalHandlers=installSignalHandlers)
        gtk.timeout_add(0, self.simulate)
        gtk.mainloop()

    def _readAndWrite(self, source, condition):
        why = None
        didRead = None
        try:
            if condition & gtk.GDK.INPUT_READ:
                why = source.doRead()
                didRead = source.doRead
            if not why and condition & gtk.GDK.INPUT_WRITE:
                if not source.disconnected and source.doWrite != didRead:
                    why = source.doWrite()
                    didRead = source.doWrite
        except:
            why = sys.exc_info()[1]
            log.msg('Error In %s' % source)
            log.deferr()

        if why:
            self._disconnectSelectable(source, why, didRead == source.doRead)

    def callback(self, source, condition):
        log.callWithLogger(source, self._readAndWrite, source, condition)
        self.simulate()
        return 1

    def simulate(self):
        if self._simtag is not None:
            gtk.timeout_remove(self._simtag)
        self.runUntilCurrent()
        timeout = min(self.timeout(), 0.1)
        if timeout is None:
            timeout = 0.1
        self._simtag = gtk.timeout_add(int(timeout * 1010), self.simulate)

class PortableGtkReactor(selectreactor.SelectReactor):
    _simtag = None
    deprecate.deprecatedModuleAttribute(deprecatedSince, deprecationMessage,
                                        __name__, "PortableGtkReactor")
    def crash(self):
        selectreactor.SelectReactor.crash(self)
        gtk.mainquit()

    def run(self, installSignalHandlers=1):
        self.startRunning(installSignalHandlers=installSignalHandlers)
        self.simulate()
        gtk.mainloop()

    def simulate(self):
        if self._simtag is not None:
            gtk.timeout_remove(self._simtag)
        self.iterate()
        timeout = min(self.timeout(), 0.1)
        if timeout is None:
            timeout = 0.1
        self._simtag = gtk.timeout_add((timeout * 1010), self.simulate)

def install():
    reactor = GtkReactor()
    from lib.twisted.internet.main import installReactor
    installReactor(reactor)
    return reactor
deprecate.deprecatedModuleAttribute(deprecatedSince, deprecationMessage,
                                    __name__, "install")

def portableInstall():
    reactor = PortableGtkReactor()
    from lib.twisted.internet.main import installReactor
    installReactor(reactor)
    return reactor
deprecate.deprecatedModuleAttribute(deprecatedSince, deprecationMessage,
                                    __name__, "portableInstall")

if runtime.platform.getType() != 'posix':
    install = portableInstall
__all__ = ['install']
