# -*- test-case-name: lib.twisted.internet.test.test_inotify -*-
# Copyright (c) 2008-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

import os
import struct
from lib.twisted.internet import fdesc
from lib.twisted.internet.abstract import FileDescriptor
from lib.twisted.python import log, _inotify

IN_ACCESS = 0x00000001L
IN_MODIFY = 0x00000002L
IN_ATTRIB = 0x00000004L
IN_CLOSE_WRITE = 0x00000008L
IN_CLOSE_NOWRITE = 0x00000010L
IN_OPEN = 0x00000020L
IN_MOVED_FROM = 0x00000040L
IN_MOVED_TO = 0x00000080L
IN_CREATE = 0x00000100L
IN_DELETE = 0x00000200L
IN_DELETE_SELF = 0x00000400L
IN_MOVE_SELF = 0x00000800L
IN_UNMOUNT = 0x00002000L
IN_Q_OVERFLOW = 0x00004000L
IN_IGNORED = 0x00008000L
IN_ONLYDIR = 0x01000000
IN_DONT_FOLLOW = 0x02000000
IN_MASK_ADD = 0x20000000
IN_ISDIR = 0x40000000
IN_ONESHOT = 0x80000000

IN_CLOSE = IN_CLOSE_WRITE | IN_CLOSE_NOWRITE
IN_MOVED = IN_MOVED_FROM | IN_MOVED_TO
IN_CHANGED = IN_MODIFY | IN_ATTRIB
IN_WATCH_MASK = (IN_MODIFY | IN_ATTRIB |
                 IN_CREATE | IN_DELETE |
                 IN_DELETE_SELF | IN_MOVE_SELF |
                 IN_UNMOUNT | IN_MOVED_FROM | IN_MOVED_TO)
_FLAG_TO_HUMAN = [
    (IN_ACCESS, 'access'),
    (IN_MODIFY, 'modify'),
    (IN_ATTRIB, 'attrib'),
    (IN_CLOSE_WRITE, 'close_write'),
    (IN_CLOSE_NOWRITE, 'close_nowrite'),
    (IN_OPEN, 'open'),
    (IN_MOVED_FROM, 'moved_from'),
    (IN_MOVED_TO, 'moved_to'),
    (IN_CREATE, 'create'),
    (IN_DELETE, 'delete'),
    (IN_DELETE_SELF, 'delete_self'),
    (IN_MOVE_SELF, 'move_self'),
    (IN_UNMOUNT, 'unmount'),
    (IN_Q_OVERFLOW, 'queue_overflow'),
    (IN_IGNORED, 'ignored'),
    (IN_ONLYDIR, 'only_dir'),
    (IN_DONT_FOLLOW, 'dont_follow'),
    (IN_MASK_ADD, 'mask_add'),
    (IN_ISDIR, 'is_dir'),
    (IN_ONESHOT, 'one_shot')
]

def humanReadableMask(mask):
    s = []
    for k, v in _FLAG_TO_HUMAN:
        if k & mask:
            s.append(v)
    return s

class _Watch(object):
    def __init__(self, path, mask=IN_WATCH_MASK, autoAdd=False,
                 callbacks=None):
        self.path = path
        self.mask = mask
        self.autoAdd = autoAdd
        if callbacks is None:
            callbacks = []
        self.callbacks = callbacks

    def _notify(self, filepath, events):
        """
        Callback function used by L{INotify} to dispatch an event.
        """
        for callback in self.callbacks:
            callback(self, filepath, events)

class INotify(FileDescriptor, object):
    _inotify = _inotify

    def __init__(self, reactor=None):
        FileDescriptor.__init__(self, reactor=reactor)
        self._fd = self._inotify.init()

        fdesc.setNonBlocking(self._fd)
        fdesc._setCloseOnExec(self._fd)
        self.connected = 1
        self._writeDisconnected = True
        self._buffer = ''
        self._watchpoints = {}
        self._watchpaths = {}

    def _addWatch(self, path, mask, autoAdd, callbacks):
        wd = self._inotify.add(self._fd, path.path, mask)
        iwp = _Watch(path, mask, autoAdd, callbacks)
        self._watchpoints[wd] = iwp
        self._watchpaths[path] = wd
        return wd

    def _rmWatch(self, wd):
        self._inotify.remove(self._fd, wd)
        iwp = self._watchpoints.pop(wd)
        self._watchpaths.pop(iwp.path)

    def connectionLost(self, reason):
        FileDescriptor.connectionLost(self, reason)
        if self._fd >= 0:
            try:
                os.close(self._fd)
            except OSError, e:
                log.err(e, "Couldn't close INotify file descriptor.")

    def fileno(self):
        return self._fd

    def doRead(self):
        fdesc.readFromFD(self._fd, self._doRead)

    def _doRead(self, in_):
        self._buffer += in_
        while len(self._buffer) >= 16:

            wd, mask, cookie, size = struct.unpack("=LLLL", self._buffer[0:16])

            if size:
                name = self._buffer[16:16 + size].rstrip('\0')
            else:
                name = None

            self._buffer = self._buffer[16 + size:]

            try:
                iwp = self._watchpoints[wd]
            except KeyError:
                continue

            path = iwp.path
            if name:
                path = path.child(name)
            iwp._notify(path, mask)

            if (iwp.autoAdd and mask & IN_ISDIR and mask & IN_CREATE):
                new_wd = self.watch(
                    path, mask=iwp.mask, autoAdd=True,
                    callbacks=iwp.callbacks
                )
                self.reactor.callLater(0,
                    self._addChildren, self._watchpoints[new_wd])
            if mask & IN_DELETE_SELF:
                self._rmWatch(wd)

    def _addChildren(self, iwp):
        try:
            listdir = iwp.path.children()
        except OSError:
            return

        for f in listdir:
            if f.isdir():
                wd = self.watch(
                    f, mask=iwp.mask, autoAdd=True,
                    callbacks=iwp.callbacks
                )
                iwp._notify(f, IN_ISDIR|IN_CREATE)
                self.reactor.callLater(0,
                    self._addChildren, self._watchpoints[wd])
            if f.isfile():
                iwp._notify(f, IN_CREATE|IN_CLOSE_WRITE)

    def watch(self, path, mask=IN_WATCH_MASK, autoAdd=False,
              callbacks=None, recursive=False):
        if recursive:
            for child in path.walk():
                if child.isdir():
                    self.watch(child, mask, autoAdd, callbacks,
                               recursive=False)
        else:
            wd = self._isWatched(path)
            if wd:
                return wd

            mask = mask | IN_DELETE_SELF
            return self._addWatch(path, mask, autoAdd, callbacks)

    def ignore(self, path):
        wd = self._isWatched(path)
        if wd is not False:
            self._rmWatch(wd)

    def _isWatched(self, path):
        return path in self._watchpaths

INotifyError = _inotify.INotifyError
__all__ = ["INotify", "humanReadableMask", "IN_WATCH_MASK", "IN_ACCESS",
           "IN_MODIFY", "IN_ATTRIB", "IN_CLOSE_NOWRITE", "IN_CLOSE_WRITE",
           "IN_OPEN", "IN_MOVED_FROM", "IN_MOVED_TO", "IN_CREATE",
           "IN_DELETE", "IN_DELETE_SELF", "IN_MOVE_SELF", "IN_UNMOUNT",
           "IN_Q_OVERFLOW", "IN_IGNORED", "IN_ONLYDIR", "IN_DONT_FOLLOW",
           "IN_MASK_ADD", "IN_ISDIR", "IN_ONESHOT", "IN_CLOSE",
           "IN_MOVED", "IN_CHANGED"]
