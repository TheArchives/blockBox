
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.twisted.internet import protocol
from lib.twisted.python import log

class Proxy(protocol.Protocol):
    noisy = True
    peer = None
    def setPeer(self, peer):
        self.peer = peer

    def connectionLost(self, reason):
        if self.peer is not None:
            self.peer.transport.loseConnection()
            self.peer = None
        elif self.noisy:
            log.msg("Unable to connect to peer: %s" % (reason,))

    def dataReceived(self, data):
        self.peer.transport.write(data)

class ProxyClient(Proxy):
    def connectionMade(self):
        self.peer.setPeer(self)
        self.peer.transport.resumeProducing()

class ProxyClientFactory(protocol.ClientFactory):
    protocol = ProxyClient

    def setServer(self, server):
        self.server = server

    def buildProtocol(self, *args, **kw):
        prot = protocol.ClientFactory.buildProtocol(self, *args, **kw)
        prot.setPeer(self.server)
        return prot

    def clientConnectionFailed(self, connector, reason):
        self.server.transport.loseConnection()

class ProxyServer(Proxy):
    clientProtocolFactory = ProxyClientFactory

    def connectionMade(self):
        self.transport.pauseProducing()
        client = self.clientProtocolFactory()
        client.setServer(self)
        from lib.twisted.internet import reactor
        reactor.connectTCP(self.factory.host, self.factory.port, client)

class ProxyFactory(protocol.Factory):
    protocol = ProxyServer

    def __init__(self, host, port):
        self.host = host
        self.port = port
