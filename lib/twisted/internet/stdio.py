# -*- test-case-name: lib.twisted.test.test_stdio -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.twisted.python.runtime import platform
if platform.isWindows():
    from lib.twisted.internet._win32stdio import StandardIO
else:
    from lib.twisted.internet._posixstdio import StandardIO

__all__ = ['StandardIO']
