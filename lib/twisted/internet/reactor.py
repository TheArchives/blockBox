# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.
import sys
del sys.modules['lib.twisted.internet.reactor']
from lib.twisted.internet import selectreactor
selectreactor.install()