# -*- test-case-name: twisted -*-

# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Twisted: The Framework Of Your Internet.
"""

# Ensure the user is running the version of python we require.
import sys
if not hasattr(sys, "version_info") or sys.version_info < (2, 4):
	raise RuntimeError("Twisted requires Python 2.4 or later.")
del sys

# Ensure compat gets imported
from lib.twisted.python import compat
del compat

# setup version
from lib.twisted._version import version
__version__ = version.short()

