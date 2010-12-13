# Copyright (c) 2008 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for implementations of L{IReactorTCP}.
"""

__metaclass__ = type

import socket

from lib.zope.interface import implements

from lib.twisted.internet.test.reactormixins import ReactorBuilder
from lib.twisted.internet.error import DNSLookupError
from lib.twisted.internet.interfaces import IResolverSimple
from lib.twisted.internet.address import IPv4Address
from lib.twisted.internet.defer import succeed, fail
from lib.twisted.internet.protocol import ServerFactory, ClientFactory, Protocol


class Stop(ClientFactory):
    """
    A client factory which stops a reactor when a connection attempt fails.
    """
    def __init__(self, reactor):
        self.reactor = reactor


    def clientConnectionFailed(self, connector, reason):
        self.reactor.stop()



class FakeResolver:
    """
    A resolver implementation based on a C{dict} mapping names to addresses.
    """
    implements(IResolverSimple)

    def __init__(self, names):
        self.names = names


    def getHostByName(self, name, timeout):
        try:
            return succeed(self.names[name])
        except KeyError:
            return fail(DNSLookupError("FakeResolver couldn't find " + name))



class TCPClientTestsBuilder(ReactorBuilder):
    """
    Builder defining tests relating to L{IReactorTCP.connectTCP}.
    """
    def _freePort(self, interface='127.0.0.1'):
        probe = socket.socket()
        try:
            probe.bind((interface, 0))
            return probe.getsockname()
        finally:
            probe.close()

    def test_clientConnectionFailedStopsReactor(self):
        """
        The reactor can be stopped by a client factory's
        C{clientConnectionFailed} method.
        """
        host, port = self._freePort()
        reactor = self.buildReactor()
        reactor.connectTCP(host, port, Stop(reactor))
        reactor.run()


    def test_addresses(self):
        """
        A client's transport's C{getHost} and C{getPeer} return L{IPv4Address}
        instances which give the dotted-quad string form of the local and
        remote endpoints of the connection respectively.
        """
        host, port = self._freePort()
        reactor = self.buildReactor()

        serverFactory = ServerFactory()
        serverFactory.protocol = Protocol
        server = reactor.listenTCP(0, serverFactory, interface=host)
        serverAddress = server.getHost()

        addresses = {'host': None, 'peer': None}
        class CheckAddress(Protocol):
            def makeConnection(self, transport):
                addresses['host'] = transport.getHost()
                addresses['peer'] = transport.getPeer()
                reactor.stop()

        clientFactory = Stop(reactor)
        clientFactory.protocol = CheckAddress
        client = reactor.connectTCP(
            'localhost', server.getHost().port, clientFactory,
            bindAddress=('127.0.0.1', port))

        reactor.installResolver(FakeResolver({'localhost': '127.0.0.1'}))
        reactor.run() # self.runReactor(reactor)

        self.assertEqual(
            addresses['host'],
            IPv4Address('TCP', '127.0.0.1', port))
        self.assertEqual(
            addresses['peer'],
            IPv4Address('TCP', '127.0.0.1', serverAddress.port))


    def test_connectEvent(self):
        """
        This test checks that we correctly get notifications event for a
        client. This ought to prevent a regression under Windows using the GTK2
        reactor. See #3925.
        """
        reactor = self.buildReactor()

        serverFactory = ServerFactory()
        serverFactory.protocol = Protocol
        server = reactor.listenTCP(0, serverFactory)
        connected = []

        class CheckConnection(Protocol):
            def connectionMade(self):
                connected.append(self)
                reactor.stop()

        clientFactory = Stop(reactor)
        clientFactory.protocol = CheckConnection
        client = reactor.connectTCP(
            '127.0.0.1', server.getHost().port, clientFactory)

        reactor.run()

        self.assertTrue(connected)



globals().update(TCPClientTestsBuilder.makeTestCaseClasses())
