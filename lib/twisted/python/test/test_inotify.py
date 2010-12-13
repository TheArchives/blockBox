# Copyright (c) 2010 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for L{twisted.python._inotify}.
"""

from lib.twisted.trial.unittest import TestCase
from lib.twisted.python.runtime import platform

if platform.supportsINotify():
    from ctypes import c_int, c_char_p
    from lib.twisted.python import _inotify
    from lib.twisted.python._inotify import (
        INotifyError, initializeModule, init, add)
else:
    _inotify = None



class INotifyTests(TestCase):
    """
    Tests for L{twisted.python._inotify}.
    """
    if _inotify is None:
        skip = "This platform doesn't support INotify."

    def test_missingInit(self):
        """
        If the I{libc} object passed to L{initializeModule} has no
        C{inotify_init} attribute, L{ImportError} is raised.
        """
        class libc:
            def inotify_add_watch(self):
                pass
            def inotify_rm_watch(self):
                pass
        self.assertRaises(ImportError, initializeModule, libc())


    def test_missingAdd(self):
        """
        If the I{libc} object passed to L{initializeModule} has no
        C{inotify_add_watch} attribute, L{ImportError} is raised.
        """
        class libc:
            def inotify_init(self):
                pass
            def inotify_rm_watch(self):
                pass
        self.assertRaises(ImportError, initializeModule, libc())


    def test_missingRemove(self):
        """
        If the I{libc} object passed to L{initializeModule} has no
        C{inotify_rm_watch} attribute, L{ImportError} is raised.
        """
        class libc:
            def inotify_init(self):
                pass
            def inotify_add_watch(self):
                pass
        self.assertRaises(ImportError, initializeModule, libc())


    def test_setAddArgtypes(self):
        """
        If the I{libc} object passed to L{initializeModule} has all
        of the necessary attributes, it sets the C{argtypes} attribute
        of the C{inotify_add_watch} attribute to a list describing the
        argument types.
        """
        class libc:
            def inotify_init(self):
                pass
            def inotify_rm_watch(self):
                pass
            def inotify_add_watch(self):
                pass
            inotify_add_watch = staticmethod(inotify_add_watch)
        c = libc()
        initializeModule(c)
        self.assertEquals(
            c.inotify_add_watch.argtypes, [c_int, c_char_p, c_int])


    def test_failedInit(self):
        """
        If C{inotify_init} returns a negative number, L{init} raises
        L{INotifyError}.
        """
        class libc:
            def inotify_init(self):
                return -1
        self.patch(_inotify, 'libc', libc())
        self.assertRaises(INotifyError, init)


    def test_failedAddWatch(self):
        """
        If C{inotify_add_watch} returns a negative number, L{add}
        raises L{INotifyError}.
        """
        class libc:
            def inotify_add_watch(self, fd, path, mask):
                return -1
        self.patch(_inotify, 'libc', libc())
        self.assertRaises(INotifyError, add, 3, '/foo', 0)
