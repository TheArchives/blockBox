# -*- test-case-name: twisted -*-

# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import sys
if not hasattr(sys, "version_info") or sys.version_info < (2, 4):
    raise RuntimeError("Twisted requires Python 2.4 or later.")
del sys
from lib.twisted.python import compat
del compat
from lib.twisted._version import version
__version__ = version.short()