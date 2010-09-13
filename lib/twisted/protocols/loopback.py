# -*- test-case-name: lib.twisted.test.test_loopback -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import tempfile
from lib.zope.interface import implements
from lib.twisted.protocols import policies
from lib.twisted.internet import interfaces, protocol, main, defer
from lib.twisted.internet.task import deferLater
from lib.twisted.python import failure
from lib.twisted.internet.interfaces import IAddress

class _LoopbackQueue(object):
    _notificationDeferred = None
    disconnect = False

    def __init__(self):
        self._queue = []

    def put(self, v):
        self._queue.append(v)
        if self._notificationDeferred is not None:
            d, self._notificationDeferred = self._notificationDeferred, None
            d.callback(None)

    def __nonzero__(self):
        return bool(self._queue)

    def get(self):
        return self._queue.pop(0)

class _LoopbackAddress(object):
    implements(IAddress)

class _LoopbackTransport(object):
    implements(interfaces.ITransport, interfaces.IConsumer)
    disconnecting = False
    producer = None

    def __init__(self, q):
        self.q = q

    def write(self, bytes):
        self.q.put(bytes)

    def writeSequence(self, iovec):
        self.q.put(''.join(iovec))

    def loseConnection(self):
        self.q.disconnect = True
        self.q.put(None)

    def getPeer(self):
        return _LoopbackAddress()

    def getHost(self):
        return _LoopbackAddress()

    def registerProducer(self, producer, streaming):
        assert self.producer is None
        self.producer = producer
        self.streamingProducer = streaming
        self._pollProducer()

    def unregisterProducer(self):
        assert self.producer is not None
        self.producer = None

    def _pollProducer(self):
        if self.producer is not None and not self.streamingProducer:
            self.producer.resumeProducing()

def identityPumpPolicy(queue, target):
    while queue:
        bytes = queue.get()
        if bytes is None:
            break
        target.dataReceived(bytes)

def collapsingPumpPolicy(queue, target):
    bytes = []
    while queue:
        chunk = queue.get()
        if chunk is None:
            break
        bytes.append(chunk)
    if bytes:
        target.dataReceived(''.join(bytes))

def loopbackAsync(server, client, pumpPolicy=identityPumpPolicy):
    serverToClient = _LoopbackQueue()
    clientToServer = _LoopbackQueue()

    server.makeConnection(_LoopbackTransport(serverToClient))
    client.makeConnection(_LoopbackTransport(clientToServer))

    return _loopbackAsyncBody(
        server, serverToClient, client, clientToServer, pumpPolicy)

def _loopbackAsyncBody(server, serverToClient, client, clientToServer,
                       pumpPolicy):
    def pump(source, q, target):
        sent = False
        if q:
            pumpPolicy(q, target)
            sent = True
        if sent and not q:
            source.transport._pollProducer()

        return sent

    while 1:
        disconnect = clientSent = serverSent = False
        serverSent = pump(server, serverToClient, client)
        clientSent = pump(client, clientToServer, server)

        if not clientSent and not serverSent:
            d = defer.Deferred()
            clientToServer._notificationDeferred = d
            serverToClient._notificationDeferred = d
            d.addCallback(
                _loopbackAsyncContinue,
                server, serverToClient, client, clientToServer, pumpPolicy)
            return d
        if serverToClient.disconnect:
            disconnect = True
            pump(server, serverToClient, client)
        elif clientToServer.disconnect:
            disconnect = True
            pump(client, clientToServer, server)
        if disconnect:
            server.connectionLost(failure.Failure(main.CONNECTION_DONE))
            client.connectionLost(failure.Failure(main.CONNECTION_DONE))
            return defer.succeed(None)

def _loopbackAsyncContinue(ignored, server, serverToClient, client,
                           clientToServer, pumpPolicy):
    clientToServer._notificationDeferred = None
    serverToClient._notificationDeferred = None
    from lib.twisted.internet import reactor
    return deferLater(
        reactor, 0,
        _loopbackAsyncBody,
        server, serverToClient, client, clientToServer, pumpPolicy)

class LoopbackRelay:

    implements(interfaces.ITransport, interfaces.IConsumer)
    buffer = ''
    shouldLose = 0
    disconnecting = 0
    producer = None

    def __init__(self, target, logFile=None):
        self.target = target
        self.logFile = logFile

    def write(self, data):
        self.buffer = self.buffer + data
        if self.logFile:
            self.logFile.write("loopback writing %s\n" % repr(data))

    def writeSequence(self, iovec):
        self.write("".join(iovec))

    def clearBuffer(self):
        if self.shouldLose == -1:
            return

        if self.producer:
            self.producer.resumeProducing()
        if self.buffer:
            if self.logFile:
                self.logFile.write("loopback receiving %s\n" % repr(self.buffer))
            buffer = self.buffer
            self.buffer = ''
            self.target.dataReceived(buffer)
        if self.shouldLose == 1:
            self.shouldLose = -1
            self.target.connectionLost(failure.Failure(main.CONNECTION_DONE))

    def loseConnection(self):
        if self.shouldLose != -1:
            self.shouldLose = 1

    def getHost(self):
        return 'loopback'

    def getPeer(self):
        return 'loopback'

    def registerProducer(self, producer, streaming):
        self.producer = producer

    def unregisterProducer(self):
        self.producer = None

    def logPrefix(self):
        return 'Loopback(%r)' % (self.target.__class__.__name__,)

def loopback(server, client, logFile=None):
    import warnings
    warnings.warn('loopback() is deprecated (since Twisted 2.5). '
                  'Use loopbackAsync() instead.',
                  stacklevel=2, category=DeprecationWarning)
    from lib.twisted.internet import reactor
    serverToClient = LoopbackRelay(client, logFile)
    clientToServer = LoopbackRelay(server, logFile)
    server.makeConnection(serverToClient)
    client.makeConnection(clientToServer)
    while 1:
        reactor.iterate(0.01) # this is to clear any deferreds
        serverToClient.clearBuffer()
        clientToServer.clearBuffer()
        if serverToClient.shouldLose:
            serverToClient.clearBuffer()
            server.connectionLost(failure.Failure(main.CONNECTION_DONE))
            break
        elif clientToServer.shouldLose:
            client.connectionLost(failure.Failure(main.CONNECTION_DONE))
            break
    reactor.iterate() # last gasp before I go away

class LoopbackClientFactory(protocol.ClientFactory):
    def __init__(self, protocol):
        self.disconnected = 0
        self.deferred = defer.Deferred()
        self.protocol = protocol

    def buildProtocol(self, addr):
        return self.protocol

    def clientConnectionLost(self, connector, reason):
        self.disconnected = 1
        self.deferred.callback(None)


class _FireOnClose(policies.ProtocolWrapper):
    def __init__(self, protocol, factory):
        policies.ProtocolWrapper.__init__(self, protocol, factory)
        self.deferred = defer.Deferred()

    def connectionLost(self, reason):
        policies.ProtocolWrapper.connectionLost(self, reason)
        self.deferred.callback(None)

def loopbackTCP(server, client, port=0, noisy=True):
    from lib.twisted.internet import reactor
    f = policies.WrappingFactory(protocol.Factory())
    serverWrapper = _FireOnClose(f, server)
    f.noisy = noisy
    f.buildProtocol = lambda addr: serverWrapper
    serverPort = reactor.listenTCP(port, f, interface='127.0.0.1')
    clientF = LoopbackClientFactory(client)
    clientF.noisy = noisy
    reactor.connectTCP('127.0.0.1', serverPort.getHost().port, clientF)
    d = clientF.deferred
    d.addCallback(lambda x: serverWrapper.deferred)
    d.addCallback(lambda x: serverPort.stopListening())
    return d


def loopbackUNIX(server, client, noisy=True):
    """Run session between server and client protocol instances over UNIX socket."""
    path = tempfile.mktemp()
    from lib.twisted.internet import reactor
    f = policies.WrappingFactory(protocol.Factory())
    serverWrapper = _FireOnClose(f, server)
    f.noisy = noisy
    f.buildProtocol = lambda addr: serverWrapper
    serverPort = reactor.listenUNIX(path, f)
    clientF = LoopbackClientFactory(client)
    clientF.noisy = noisy
    reactor.connectUNIX(path, clientF)
    d = clientF.deferred
    d.addCallback(lambda x: serverWrapper.deferred)
    d.addCallback(lambda x: serverPort.stopListening())
    return d