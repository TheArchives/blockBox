# -*- test-case-name: lib.twisted.internet.test.test_main -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Backwards compatibility, and utility functions.

In general, this module should not be used, other than by reactor authors
who need to use the 'installReactor' method.

Maintainer: Itamar Shtull-Trauring
"""

import error

CONNECTION_DONE = error.ConnectionDone('Connection done')
CONNECTION_LOST = error.ConnectionLost('Connection lost')

def installReactor(reactor):
	"""
	Install reactor C{reactor}.

	@param reactor: An object that provides one or more IReactor* interfaces.
	"""
	# this stuff should be common to all reactors.
	import lib.twisted.internet
	import sys
	if 'lib.twisted.internet.reactor' in sys.modules:
		raise error.ReactorAlreadyInstalledError("reactor already installed")
	lib.twisted.internet.reactor = reactor
	sys.modules['lib.twisted.internet.reactor'] = reactor


__all__ = ["CONNECTION_LOST", "CONNECTION_DONE",
		   "ReactorAlreadyInstalledError", "installReactor"]
