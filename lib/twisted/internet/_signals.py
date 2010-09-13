# -*- test-case-name: twisted.test.test_process,twisted.internet.test.test_process -*-
# Copyright (c) 2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import os
try:
    from signal import set_wakeup_fd, siginterrupt
except ImportError:
    set_wakeup_fd = siginterrupt = None
try:
    import signal
except ImportError:
    signal = None
from twisted.python.log import msg
try:
    from twisted.internet._sigchld import installHandler as _extInstallHandler, \
        isDefaultHandler as _extIsDefaultHandler
except ImportError:
    _extInstallHandler = _extIsDefaultHandler = None

class _Handler(object):
    def __init__(self, fd):
        self.fd = fd

    def __call__(self, *args):
        if self.fd is not None:
            try:
                os.write(self.fd, '\0')
            except:
                pass

def _installHandlerUsingSignal(fd):
    if fd == -1:
        previous = signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    else:
        previous = signal.signal(signal.SIGCHLD, _Handler(fd))
    if isinstance(previous, _Handler):
        return previous.fd
    return -1

def _installHandlerUsingSetWakeup(fd):
    if fd == -1:
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    else:
        signal.signal(signal.SIGCHLD, _Handler(None))
        siginterrupt(signal.SIGCHLD, False)
    return set_wakeup_fd(fd)

def _isDefaultHandler():
    return signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL

def _cannotInstallHandler(fd):
    raise RuntimeError("Cannot install a SIGCHLD handler")

def _cannotDetermineDefault():
    raise RuntimeError("No usable signal API available")

if set_wakeup_fd is not None:
    msg('using set_wakeup_fd')
    installHandler = _installHandlerUsingSetWakeup
    isDefaultHandler = _isDefaultHandler
elif _extInstallHandler is not None:
    msg('using _sigchld')
    installHandler = _extInstallHandler
    isDefaultHandler = _extIsDefaultHandler
elif signal is not None:
    msg('using signal module')
    installHandler = _installHandlerUsingSignal
    isDefaultHandler = _isDefaultHandler
else:
    msg('nothing unavailable')
    installHandler = _cannotInstallHandler
    isDefaultHandler = _cannotDetermineDefault
