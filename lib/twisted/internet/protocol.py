# -*- test-case-name: lib.twisted.test.test_factories,lib.twisted.internet.test.test_protocol -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

import random
from lib.zope.interface import implements
from lib.twisted.python import log, failure, components
from lib.twisted.internet import interfaces, error, defer


class Factory:

    implements(interfaces.IProtocolFactory)

    protocol = None
    numPorts = 0
    noisy = True

    def doStart(self):
        if not self.numPorts:
            if self.noisy:
                log.msg("Starting factory %r" % self)
            self.startFactory()
        self.numPorts = self.numPorts + 1

    def doStop(self):
        if self.numPorts == 0:
            # this shouldn't happen, but does sometimes and this is better
            # than blowing up in assert as we did previously.
            return
        self.numPorts = self.numPorts - 1
        if not self.numPorts:
            if self.noisy:
                log.msg("Stopping factory %r" % self)
            self.stopFactory()

    def startFactory(self):

    def stopFactory(self):

    def buildProtocol(self, addr):
        p = self.protocol()
        p.factory = self
        return p

class ClientFactory(Factory):

    def startedConnecting(self, connector):

    def clientConnectionFailed(self, connector, reason):

    def clientConnectionLost(self, connector, reason):

class _InstanceFactory(ClientFactory):

    noisy = False
    pending = None

    def __init__(self, reactor, instance, deferred):
        self.reactor = reactor
        self.instance = instance
        self.deferred = deferred

    def __repr__(self):
        return "<ClientCreator factory: %r>" % (self.instance, )

    def buildProtocol(self, addr):
        self.pending = self.reactor.callLater(
            0, self.fire, self.deferred.callback, self.instance)
        self.deferred = None
        return self.instance

    def clientConnectionFailed(self, connector, reason):
        self.pending = self.reactor.callLater(
            0, self.fire, self.deferred.errback, reason)
        self.deferred = None

    def fire(self, callable, value):
        self.pending = None
        callable(value)

class ClientCreator:

    def __init__(self, reactor, protocolClass, *args, **kwargs):
        self.reactor = reactor
        self.protocolClass = protocolClass
        self.args = args
        self.kwargs = kwargs

    def _connect(self, method, *args, **kwargs):

        def cancelConnect(deferred):
            connector.disconnect()
            if f.pending is not None:
                f.pending.cancel()
        d = defer.Deferred(cancelConnect)
        f = _InstanceFactory(
            self.reactor, self.protocolClass(*self.args, **self.kwargs), d)
        connector = method(factory=f, *args, **kwargs)
        return d

    def connectTCP(self, host, port, timeout=30, bindAddress=None):
        return self._connect(
            self.reactor.connectTCP, host, port, timeout=timeout,
            bindAddress=bindAddress)

    def connectUNIX(self, address, timeout=30, checkPID=False):
        return self._connect(
            self.reactor.connectUNIX, address, timeout=timeout,
            checkPID=checkPID)

    def connectSSL(self, host, port, contextFactory, timeout=30, bindAddress=None):
        return self._connect(
            self.reactor.connectSSL, host, port,
            contextFactory=contextFactory, timeout=timeout,
            bindAddress=bindAddress)

class ReconnectingClientFactory(ClientFactory):
    maxDelay = 3600
    initialDelay = 1.0
    factor = 2.7182818284590451 # (math.e)
    # Phi = 1.6180339887498948 # (Phi is acceptable for use as a
    # factor if e is too large for your application.)
    jitter = 0.11962656472 # molar Planck constant times c, joule meter/mole

    delay = initialDelay
    retries = 0
    maxRetries = None
    _callID = None
    connector = None
    clock = None
    continueTrying = 1

    def clientConnectionFailed(self, connector, reason):
        if self.continueTrying:
            self.connector = connector
            self.retry()

    def clientConnectionLost(self, connector, unused_reason):
        if self.continueTrying:
            self.connector = connector
            self.retry()

    def retry(self, connector=None):
        if not self.continueTrying:
            if self.noisy:
                log.msg("Abandoning %s on explicit request" % (connector,))
            return

        if connector is None:
            if self.connector is None:
                raise ValueError("no connector to retry")
            else:
                connector = self.connector

        self.retries += 1
        if self.maxRetries is not None and (self.retries > self.maxRetries):
            if self.noisy:
                log.msg("Abandoning %s after %d retries." %
                        (connector, self.retries))
            return

        self.delay = min(self.delay * self.factor, self.maxDelay)
        if self.jitter:
            self.delay = random.normalvariate(self.delay,
                                              self.delay * self.jitter)

        if self.noisy:
            log.msg("%s will retry in %d seconds" % (connector, self.delay,))

        def reconnector():
            self._callID = None
            connector.connect()
        if self.clock is None:
            from lib.twisted.internet import reactor
            self.clock = reactor
        self._callID = self.clock.callLater(self.delay, reconnector)

    def stopTrying(self):
        # ??? Is this function really stopFactory?
        if self._callID:
            self._callID.cancel()
            self._callID = None
        if self.connector:
            # Hopefully this doesn't just make clientConnectionFailed
            # retry again.
            try:
                self.connector.stopConnecting()
            except error.NotConnectingError:
                pass
        self.continueTrying = 0

    def resetDelay(self):
        self.delay = self.initialDelay
        self.retries = 0
        self._callID = None
        self.continueTrying = 1

    def __getstate__(self):
        state = self.__dict__.copy()
        for key in ['connector', 'retries', 'delay',
                    'continueTrying', '_callID', 'clock']:
            if key in state:
                del state[key]
        return state

class ServerFactory(Factory):

class BaseProtocol:

    connected = 0
    transport = None

    def makeConnection(self, transport):
        self.connected = 1
        self.transport = transport
        self.connectionMade()

    def connectionMade(self):

connectionDone=failure.Failure(error.ConnectionDone())
connectionDone.cleanFailure()

class Protocol(BaseProtocol):
    implements(interfaces.IProtocol)

    def dataReceived(self, data):

    def connectionLost(self, reason=connectionDone):

class ProtocolToConsumerAdapter(components.Adapter):
    implements(interfaces.IConsumer)

    def write(self, data):
        self.original.dataReceived(data)

    def registerProducer(self, producer, streaming):
        pass

    def unregisterProducer(self):
        pass

components.registerAdapter(ProtocolToConsumerAdapter, interfaces.IProtocol,
                           interfaces.IConsumer)

class ConsumerToProtocolAdapter(components.Adapter):
    implements(interfaces.IProtocol)

    def dataReceived(self, data):
        self.original.write(data)

    def connectionLost(self, reason):
        pass

    def makeConnection(self, transport):
        pass

    def connectionMade(self):
        pass

components.registerAdapter(ConsumerToProtocolAdapter, interfaces.IConsumer,
                           interfaces.IProtocol)

class ProcessProtocol(BaseProtocol):
    implements(interfaces.IProcessProtocol)

    def childDataReceived(self, childFD, data):
        if childFD == 1:
            self.outReceived(data)
        elif childFD == 2:
            self.errReceived(data)

    def outReceived(self, data):

    def errReceived(self, data):

    def childConnectionLost(self, childFD):
        if childFD == 0:
            self.inConnectionLost()
        elif childFD == 1:
            self.outConnectionLost()
        elif childFD == 2:
            self.errConnectionLost()

    def inConnectionLost(self):

    def outConnectionLost(self):

    def errConnectionLost(self):

    def processExited(self, reason):

    def processEnded(self, reason):

class AbstractDatagramProtocol:

    transport = None
    numPorts = 0
    noisy = True

    def __getstate__(self):
        d = self.__dict__.copy()
        d['transport'] = None
        return d

    def doStart(self):
        if not self.numPorts:
            if self.noisy:
                log.msg("Starting protocol %s" % self)
            self.startProtocol()
        self.numPorts = self.numPorts + 1

    def doStop(self):
        assert self.numPorts > 0
        self.numPorts = self.numPorts - 1
        self.transport = None
        if not self.numPorts:
            if self.noisy:
                log.msg("Stopping protocol %s" % self)
            self.stopProtocol()

    def startProtocol(self):

    def stopProtocol(self):

    def makeConnection(self, transport):
        assert self.transport == None
        self.transport = transport
        self.doStart()

    def datagramReceived(self, datagram, addr):

class DatagramProtocol(AbstractDatagramProtocol):
    def connectionRefused(self):

class ConnectedDatagramProtocol(DatagramProtocol):
    def datagramReceived(self, datagram):

    def connectionFailed(self, failure):

class FileWrapper:
    implements(interfaces.ITransport)

    closed = 0
    disconnecting = 0
    producer = None
    streamingProducer = 0

    def __init__(self, file):
        self.file = file

    def write(self, data):
        try:
            self.file.write(data)
        except:
            self.handleException()
        # self._checkProducer()

    def _checkProducer(self):
        if self.producer:
            self.producer.resumeProducing()

    def registerProducer(self, producer, streaming):
        self.producer = producer
        self.streamingProducer = streaming
        if not streaming:
            producer.resumeProducing()

    def unregisterProducer(self):
        self.producer = None

    def stopConsuming(self):
        self.unregisterProducer()
        self.loseConnection()

    def writeSequence(self, iovec):
        self.write("".join(iovec))

    def loseConnection(self):
        self.closed = 1
        try:
            self.file.close()
        except (IOError, OSError):
            self.handleException()

    def getPeer(self):
        return 'file', 'file'

    def getHost(self):
        return 'file'

    def handleException(self):
        pass

    def resumeProducing(self):
        pass

    def pauseProducing(self):
        pass

    def stopProducing(self):
        self.loseConnection()

__all__ = ["Factory", "ClientFactory", "ReconnectingClientFactory", "connectionDone",
           "Protocol", "ProcessProtocol", "FileWrapper", "ServerFactory",
           "AbstractDatagramProtocol", "DatagramProtocol", "ConnectedDatagramProtocol",
           "ClientCreator"]
