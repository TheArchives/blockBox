# -*- test-case-name: lib.twisted.internet.test.test_endpoints -*-
# Copyright (c) 2007-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

from lib.zope.interface import implements, directlyProvides
from lib.twisted.internet import interfaces, defer, error
from lib.twisted.internet.protocol import ClientFactory, Protocol

__all__ = ["TCP4ServerEndpoint", "TCP4ClientEndpoint",
           "UNIXServerEndpoint", "UNIXClientEndpoint",
           "SSL4ServerEndpoint", "SSL4ClientEndpoint"]

class _WrappingProtocol(Protocol):
    def __init__(self, connectedDeferred, wrappedProtocol):
        self._connectedDeferred = connectedDeferred
        self._wrappedProtocol = wrappedProtocol

        if interfaces.IHalfCloseableProtocol.providedBy(
            self._wrappedProtocol):
            directlyProvides(self, interfaces.IHalfCloseableProtocol)

    def connectionMade(self):
        self._wrappedProtocol.makeConnection(self.transport)
        self._connectedDeferred.callback(self._wrappedProtocol)

    def dataReceived(self, data):
        return self._wrappedProtocol.dataReceived(data)

    def connectionLost(self, reason):
        return self._wrappedProtocol.connectionLost(reason)

    def readConnectionLost(self):
        self._wrappedProtocol.readConnectionLost()

    def writeConnectionLost(self):
        self._wrappedProtocol.writeConnectionLost()

class _WrappingFactory(ClientFactory):
    protocol = _WrappingProtocol

    def __init__(self, wrappedFactory, canceller):
        self._wrappedFactory = wrappedFactory
        self._onConnection = defer.Deferred(canceller=canceller)

    def buildProtocol(self, addr):
        try:
            proto = self._wrappedFactory.buildProtocol(addr)
        except:
            self._onConnection.errback()
        else:
            return self.protocol(self._onConnection, proto)

    def clientConnectionFailed(self, connector, reason):
        self._onConnection.errback(reason)

class TCP4ServerEndpoint(object):
    implements(interfaces.IStreamServerEndpoint)

    def __init__(self, reactor, port, backlog=50, interface=''):
        self._reactor = reactor
        self._port = port
        self._listenArgs = dict(backlog=50, interface='')
        self._backlog = backlog
        self._interface = interface

    def listen(self, protocolFactory):
        return defer.execute(self._reactor.listenTCP,
                             self._port,
                             protocolFactory,
                             backlog=self._backlog,
                             interface=self._interface)

class TCP4ClientEndpoint(object):
    implements(interfaces.IStreamClientEndpoint)

    def __init__(self, reactor, host, port, timeout=30, bindAddress=None):
        self._reactor = reactor
        self._host = host
        self._port = port
        self._timeout = timeout
        self._bindAddress = bindAddress

    def connect(self, protocolFactory):
        def _canceller(deferred):
            connector.stopConnecting()
            deferred.errback(
                error.ConnectingCancelledError(connector.getDestination()))

        try:
            wf = _WrappingFactory(protocolFactory, _canceller)
            connector = self._reactor.connectTCP(
                self._host, self._port, wf,
                timeout=self._timeout, bindAddress=self._bindAddress)
            return wf._onConnection
        except:
            return defer.fail()

class SSL4ServerEndpoint(object):
    implements(interfaces.IStreamServerEndpoint)

    def __init__(self, reactor, port, sslContextFactory,
                 backlog=50, interface=''):
        self._reactor = reactor
        self._port = port
        self._sslContextFactory = sslContextFactory
        self._backlog = backlog
        self._interface = interface

    def listen(self, protocolFactory):
        return defer.execute(self._reactor.listenSSL, self._port,
                             protocolFactory,
                             contextFactory=self._sslContextFactory,
                             backlog=self._backlog,
                             interface=self._interface)

class SSL4ClientEndpoint(object):
    implements(interfaces.IStreamClientEndpoint)

    def __init__(self, reactor, host, port, sslContextFactory,
                 timeout=30, bindAddress=None):
        self._reactor = reactor
        self._host = host
        self._port = port
        self._sslContextFactory = sslContextFactory
        self._timeout = timeout
        self._bindAddress = bindAddress

    def connect(self, protocolFactory):
        def _canceller(deferred):
            connector.stopConnecting()
            deferred.errback(
                error.ConnectingCancelledError(connector.getDestination()))

        try:
            wf = _WrappingFactory(protocolFactory, _canceller)
            connector = self._reactor.connectSSL(
                self._host, self._port, wf, self._sslContextFactory,
                timeout=self._timeout, bindAddress=self._bindAddress)
            return wf._onConnection
        except:
            return defer.fail()

class UNIXServerEndpoint(object):
    implements(interfaces.IStreamServerEndpoint)

    def __init__(self, reactor, address, backlog=50, mode=0666, wantPID=0):
        self._reactor = reactor
        self._address = address
        self._backlog = backlog
        self._mode = mode
        self._wantPID = wantPID

    def listen(self, protocolFactory):
        return defer.execute(self._reactor.listenUNIX, self._address,
                             protocolFactory,
                             backlog=self._backlog,
                             mode=self._mode,
                             wantPID=self._wantPID)

class UNIXClientEndpoint(object):
    implements(interfaces.IStreamClientEndpoint)

    def __init__(self, reactor, path, timeout=30, checkPID=0):
        self._reactor = reactor
        self._path = path
        self._timeout = timeout
        self._checkPID = checkPID

    def connect(self, protocolFactory):
        def _canceller(deferred):
            connector.stopConnecting()
            deferred.errback(
                error.ConnectingCancelledError(connector.getDestination()))

        try:
            wf = _WrappingFactory(protocolFactory, _canceller)
            connector = self._reactor.connectUNIX(
                self._path, wf,
                timeout=self._timeout,
                checkPID=self._checkPID)
            return wf._onConnection
        except:
            return defer.fail()
