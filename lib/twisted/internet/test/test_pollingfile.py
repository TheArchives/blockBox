# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for L{twisted.internet._pollingfile}.
"""

from lib.twisted.python.runtime import platform
from lib.twisted.trial.unittest import TestCase

if platform.isWindows():
    from lib.twisted.internet import _pollingfile
else:
    _pollingfile = None



class TestPollableWritePipe(TestCase):
    """
    Tests for L{_pollingfile._PollableWritePipe}.
    """

    def test_checkWorkUnicode(self):
        """
        When one tries to pass unicode to L{_pollingfile._PollableWritePipe}, a
        C{TypeError} is raised instead of passing the data to C{WriteFile}
        call which is going to mangle it.
        """
        p = _pollingfile._PollableWritePipe(1, lambda: None)
        p.write("test")
        p.checkWork()

        p.write(u"test")
        self.assertRaises(TypeError, p.checkWork)



if _pollingfile is None:
    TestPollableWritePipe.skip = "_pollingfile is only avalable under Windows."
