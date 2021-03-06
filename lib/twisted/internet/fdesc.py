# -*- test-case-name: twisted.test.test_fdesc -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Utility functions for dealing with POSIX file descriptors.
"""

import os
import errno
try:
    import fcntl
except ImportError:
    fcntl = None

# twisted imports
from lib.twisted.internet.main import CONNECTION_LOST, CONNECTION_DONE
from lib.twisted.python.runtime import platformType

def setNonBlocking(fd):
    """
    Make a file descriptor non-blocking.
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)


def setBlocking(fd):
    """
    Make a file descriptor blocking.
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags & ~os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)


if fcntl is None:
    # fcntl isn't available on Windows.  By default, handles aren't
    # inherited on Windows, so we can do nothing here.
    _setCloseOnExec = _unsetCloseOnExec = lambda fd: None
else:
    def _setCloseOnExec(fd):
        """
        Make a file descriptor close-on-exec.
        """
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        flags = flags | fcntl.FD_CLOEXEC
        fcntl.fcntl(fd, fcntl.F_SETFD, flags)


    def _unsetCloseOnExec(fd):
        """
        Make a file descriptor close-on-exec.
        """
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        flags = flags & ~fcntl.FD_CLOEXEC
        fcntl.fcntl(fd, fcntl.F_SETFD, flags)


def readFromFD(fd, callback):
    """
    Read from file descriptor, calling callback with resulting data.

    If successful, call 'callback' with a single argument: the
    resulting data.

    Returns same thing FileDescriptor.doRead would: CONNECTION_LOST,
    CONNECTION_DONE, or None.

    @type fd: C{int}
    @param fd: non-blocking file descriptor to be read from.
    @param callback: a callable which accepts a single argument. If
    data is read from the file descriptor it will be called with this
    data. Handling exceptions from calling the callback is up to the
    caller.

    Note that if the descriptor is still connected but no data is read,
    None will be returned but callback will not be called.

    @return: CONNECTION_LOST on error, CONNECTION_DONE when fd is
    closed, otherwise None.
    """
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
    """
    Write data to file descriptor.

    Returns same thing FileDescriptor.writeSomeData would.

    @type fd: C{int}
    @param fd: non-blocking file descriptor to be written to.
    @type data: C{str} or C{buffer}
    @param data: bytes to write to fd.

    @return: number of bytes written, or CONNECTION_LOST.
    """
    try:
        return os.write(fd, data)
    except (OSError, IOError), io:
        if io.errno in (errno.EAGAIN, errno.EINTR):
            return 0
        return CONNECTION_LOST


__all__ = ["setNonBlocking", "setBlocking", "readFromFD", "writeToFD"]
