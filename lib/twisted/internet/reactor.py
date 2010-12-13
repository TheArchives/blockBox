# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
The reactor is the Twisted event loop within Twisted, the loop which drives
applications using lib.twisted. The reactor provides APIs for networking,
threading, dispatching events, and more.

The default reactor is based on C{select(2)} and will be installed if this
module is imported without another reactor being explicitly installed.
Regardless of which reactor is installed, importing this module is the correct
way to get a reference to it.

New application code should prefer to pass and accept the reactor as a
parameter where it is needed, rather than relying on being able to import this
module to get a reference.  This simplifies unit testing and may make it easier
to one day support multiple reactors (as a performance enhancement), though
this is not currently possible.

@see: L{IReactorCore<lib.twisted.internet.interfaces.IReactorCore>}
@see: L{IReactorTime<lib.twisted.internet.interfaces.IReactorTime>}
@see: L{IReactorProcess<lib.twisted.internet.interfaces.IReactorProcess>}
@see: L{IReactorTCP<lib.twisted.internet.interfaces.IReactorTCP>}
@see: L{IReactorSSL<lib.twisted.internet.interfaces.IReactorSSL>}
@see: L{IReactorUDP<lib.twisted.internet.interfaces.IReactorUDP>}
@see: L{IReactorMulticast<lib.twisted.internet.interfaces.IReactorMulticast>}
@see: L{IReactorUNIX<lib.twisted.internet.interfaces.IReactorUNIX>}
@see: L{IReactorUNIXDatagram<lib.twisted.internet.interfaces.IReactorUNIXDatagram>}
@see: L{IReactorFDSet<lib.twisted.internet.interfaces.IReactorFDSet>}
@see: L{IReactorThreads<lib.twisted.internet.interfaces.IReactorThreads>}
@see: L{IReactorArbitrary<lib.twisted.internet.interfaces.IReactorArbitrary>}
@see: L{IReactorPluggableResolver<lib.twisted.internet.interfaces.IReactorPluggableResolver>}
"""

import sys
del sys.modules['lib.twisted.internet.reactor']
from lib.twisted.internet import selectreactor
selectreactor.install()
