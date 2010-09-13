# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import pyui
def _guiUpdate(reactor, delay):
    pyui.draw()
    if pyui.update() == 0:
        pyui.quit()
        reactor.stop()
    else:
        reactor.callLater(delay, _guiUpdate, reactor, delay)

def install(ms=10, reactor=None, args=(), kw={}):
    d = pyui.init(*args, **kw)

    if reactor is None:
        from lib.twisted.internet import reactor
    _guiUpdate(reactor, ms / 1000.0)
    return d

__all__ = ["install"]
