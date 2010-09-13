# -*- test-case-name: lib.twisted.internet.test.test_qtreactor -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.

try:
    install = __import__('qtreactor').install
except ImportError:
    from lib.twisted.plugins.twisted_qtstub import errorMessage
    raise ImportError(errorMessage)
else:
    import warnings
    warnings.warn("Please use qtreactor instead of lib.twisted.internet.qtreactor",
                  category=DeprecationWarning)

__all__ = ['install']

