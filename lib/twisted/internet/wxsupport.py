# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import warnings
warnings.warn("wxsupport is not fully functional on Windows, wxreactor is better.")
from wxPython.wx import wxApp
from lib.twisted.internet import reactor
from lib.twisted.python.runtime import platformType

class wxRunner:
    def __init__(self, app):
        self.app = app
        
    def run(self):
        while self.app.Pending():
            self.app.Dispatch()
        self.app.ProcessIdle()
        reactor.callLater(0.02, self.run)

def install(app):
    runner = wxRunner(app)
    reactor.callLater(0.02, runner.run)

__all__ = ["install"]
