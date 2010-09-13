# -*- test-case-name: lib.twisted.test.test_fdesc -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import os
import errno
try:
    import fcntl
except ImportError:
    fcntl = None
from lib.twisted.internet.main import CONNECTION_LOST, CONNECTION_DONE
from lib.twisted.python.runtime import platformType

def setNonBlocking(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)

def setBlocking(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags & ~os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)

if fcntl is None:
    _setCloseOnExec = _unsetCloseOnExec = lambda fd: None
else:
    def _setCloseOnExec(fd):
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        flags = flags | fcntl.FD_CLOEXEC
        fcntl.fcntl(fd, fcntl.F_SETFD, flags)

    def _unsetCloseOnExec(fd):
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        flags = flags & ~fcntl.FD_CLOEXEC
        fcntl.fcntl(fd, fcntl.F_SETFD, flags)

def readFromFD(fd, callback):
    try:
        output = os.read(fd, 8192)
    except (OSError, IOError), ioe:
        if ioe.args[0] in (errno.EAGAIN, errno.EINTR):
            return
        else:
            return CONNECTION_LOST
    if not output:
        return CONNECTION_DONE
    callback(output)

def writeToFD(fd, data):
    try:
        return os.write(fd, data)
    except (OSError, IOError), io:
        if io.errno in (errno.EAGAIN, errno.EINTR):
            return 0
        return CONNECTION_LOST

__all__ = ["setNonBlocking", "setBlocking", "readFromFD", "writeToFD"]
