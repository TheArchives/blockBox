# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.
import Queue
try:
    from wx import PySimpleApp as wxPySimpleApp, CallAfter as wxCallAfter, \
         Timer as wxTimer
except ImportError:
    from wxPython.wx import wxPySimpleApp, wxCallAfter, wxTimer
from lib.twisted.python import log, runtime
from lib.twisted.internet import _threadedselect

class ProcessEventsTimer(wxTimer):
    def __init__(self, wxapp):
        wxTimer.__init__(self)
        self.wxapp = wxapp
    
    def Notify(self):
        self.wxapp.ProcessPendingEvents()

class WxReactor(_threadedselect.ThreadedSelectReactor):
    _stopping = False

    def registerWxApp(self, wxapp):
        self.wxapp = wxapp

    def _installSignalHandlersAgain(self):
        try:
            import signal
            signal.signal(signal.SIGINT, signal.default_int_handler)
        except ImportError:
            return
        self._handleSignals()

    def stop(self):
        if self._stopping:
            return
        self._stopping = True
        _threadedselect.ThreadedSelectReactor.stop(self)

    def _runInMainThread(self, f):
        if hasattr(self, "wxapp"):
            wxCallAfter(f)
        else:
            self._postQueue.put(f)

    def _stopWx(self):
        if hasattr(self, "wxapp"):
            self.wxapp.ExitMainLoop()

    def run(self, installSignalHandlers=True):
        self._postQueue = Queue.Queue()
        if not hasattr(self, "wxapp"):
            log.msg("registerWxApp() was not called on reactor, "
                    "registering my own wxApp instance.")
            self.registerWxApp(wxPySimpleApp())

        self.interleave(self._runInMainThread,
                        installSignalHandlers=installSignalHandlers)
        if installSignalHandlers:
            self.callLater(0, self._installSignalHandlersAgain)

        self.addSystemEventTrigger("after", "shutdown", self._stopWx)
        self.addSystemEventTrigger("after", "shutdown",
                                   lambda: self._postQueue.put(None))

        if runtime.platform.isMacOSX():
            t = ProcessEventsTimer(self.wxapp)
            t.Start(2)
        
        self.wxapp.MainLoop()
        wxapp = self.wxapp
        del self.wxapp
        if not self._stopping:
            self.stop()
            wxapp.ProcessPendingEvents()
            while 1:
                try:
                    f = self._postQueue.get(timeout=0.01)
                except Queue.Empty:
                    continue
                else:
                    if f is None:
                        break
                    try:
                        f()
                    except:
                        log.err()

def install():
    reactor = WxReactor()
    from lib.twisted.internet.main import installReactor
    installReactor(reactor)
    return reactor

__all__ = ['install']
