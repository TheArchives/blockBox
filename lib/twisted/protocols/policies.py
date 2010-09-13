# -*- test-case-name: lib.twisted.test.test_policies -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import sys, operator
from lib.zope.interface import directlyProvides, providedBy
from lib.twisted.internet.protocol import ServerFactory, Protocol, ClientFactory
from lib.twisted.internet import error
from lib.twisted.python import log

class ProtocolWrapper(Protocol):
    disconnecting = 0

    def __init__(self, factory, wrappedProtocol):
        self.wrappedProtocol = wrappedProtocol
        self.factory = factory

    def makeConnection(self, transport):
        directlyProvides(self, providedBy(transport))
        Protocol.makeConnection(self, transport)
        self.factory.registerProtocol(self)
        self.wrappedProtocol.makeConnection(self)

    def write(self, data):
        self.transport.write(data)

    def writeSequence(self, data):
        self.transport.writeSequence(data)

    def loseConnection(self):
        self.disconnecting = 1
        self.transport.loseConnection()

    def getPeer(self):
        return self.transport.getPeer()

    def getHost(self):
        return self.transport.getHost()

    def registerProducer(self, producer, streaming):
        self.transport.registerProducer(producer, streaming)

    def unregisterProducer(self):
        self.transport.unregisterProducer()

    def stopConsuming(self):
        self.transport.stopConsuming()

    def __getattr__(self, name):
        return getattr(self.transport, name)

    def dataReceived(self, data):
        self.wrappedProtocol.dataReceived(data)

    def connectionLost(self, reason):
        self.factory.unregisterProtocol(self)
        self.wrappedProtocol.connectionLost(reason)

class WrappingFactory(ClientFactory):
    protocol = ProtocolWrapper

    def __init__(self, wrappedFactory):
        self.wrappedFactory = wrappedFactory
        self.protocols = {}

    def doStart(self):
        self.wrappedFactory.doStart()
        ClientFactory.doStart(self)

    def doStop(self):
        self.wrappedFactory.doStop()
        ClientFactory.doStop(self)

    def startedConnecting(self, connector):
        self.wrappedFactory.startedConnecting(connector)

    def clientConnectionFailed(self, connector, reason):
        self.wrappedFactory.clientConnectionFailed(connector, reason)

    def clientConnectionLost(self, connector, reason):
        self.wrappedFactory.clientConnectionLost(connector, reason)

    def buildProtocol(self, addr):
        return self.protocol(self, self.wrappedFactory.buildProtocol(addr))

    def registerProtocol(self, p):
        self.protocols[p] = 1

    def unregisterProtocol(self, p):
        del self.protocols[p]

class ThrottlingProtocol(ProtocolWrapper):
    def write(self, data):
        self.factory.registerWritten(len(data))
        ProtocolWrapper.write(self, data)

    def writeSequence(self, seq):
        self.factory.registerWritten(reduce(operator.add, map(len, seq)))
        ProtocolWrapper.writeSequence(self, seq)

    def dataReceived(self, data):
        self.factory.registerRead(len(data))
        ProtocolWrapper.dataReceived(self, data)

    def registerProducer(self, producer, streaming):
        self.producer = producer
        ProtocolWrapper.registerProducer(self, producer, streaming)

    def unregisterProducer(self):
        del self.producer
        ProtocolWrapper.unregisterProducer(self)

    def throttleReads(self):
        self.transport.pauseProducing()

    def unthrottleReads(self):
        self.transport.resumeProducing()

    def throttleWrites(self):
        if hasattr(self, "producer"):
            self.producer.pauseProducing()

    def unthrottleWrites(self):
        if hasattr(self, "producer"):
            self.producer.resumeProducing()

class ThrottlingFactory(WrappingFactory):
    protocol = ThrottlingProtocol

    def __init__(self, wrappedFactory, maxConnectionCount=sys.maxint,
                 readLimit=None, writeLimit=None):
        WrappingFactory.__init__(self, wrappedFactory)
        self.connectionCount = 0
        self.maxConnectionCount = maxConnectionCount
        self.readLimit = readLimit # max bytes we should read per second
        self.writeLimit = writeLimit # max bytes we should write per second
        self.readThisSecond = 0
        self.writtenThisSecond = 0
        self.unthrottleReadsID = None
        self.checkReadBandwidthID = None
        self.unthrottleWritesID = None
        self.checkWriteBandwidthID = None

    def callLater(self, period, func):
        from lib.twisted.internet import reactor
        return reactor.callLater(period, func)

    def registerWritten(self, length):
        self.writtenThisSecond += length

    def registerRead(self, length):
        self.readThisSecond += length

    def checkReadBandwidth(self):
        if self.readThisSecond > self.readLimit:
            self.throttleReads()
            throttleTime = (float(self.readThisSecond) / self.readLimit) - 1.0
            self.unthrottleReadsID = self.callLater(throttleTime,
                                                    self.unthrottleReads)
        self.readThisSecond = 0
        self.checkReadBandwidthID = self.callLater(1, self.checkReadBandwidth)

    def checkWriteBandwidth(self):
        if self.writtenThisSecond > self.writeLimit:
            self.throttleWrites()
            throttleTime = (float(self.writtenThisSecond) / self.writeLimit) - 1.0
            self.unthrottleWritesID = self.callLater(throttleTime,
                                                        self.unthrottleWrites)
        self.writtenThisSecond = 0
        self.checkWriteBandwidthID = self.callLater(1, self.checkWriteBandwidth)

    def throttleReads(self):
        log.msg("Throttling reads on %s" % self)
        for p in self.protocols.keys():
            p.throttleReads()

    def unthrottleReads(self):
        self.unthrottleReadsID = None
        log.msg("Stopped throttling reads on %s" % self)
        for p in self.protocols.keys():
            p.unthrottleReads()

    def throttleWrites(self):
        log.msg("Throttling writes on %s" % self)
        for p in self.protocols.keys():
            p.throttleWrites()

    def unthrottleWrites(self):
        self.unthrottleWritesID = None
        log.msg("Stopped throttling writes on %s" % self)
        for p in self.protocols.keys():
            p.unthrottleWrites()

    def buildProtocol(self, addr):
        if self.connectionCount == 0:
            if self.readLimit is not None:
                self.checkReadBandwidth()
            if self.writeLimit is not None:
                self.checkWriteBandwidth()

        if self.connectionCount < self.maxConnectionCount:
            self.connectionCount += 1
            return WrappingFactory.buildProtocol(self, addr)
        else:
            log.msg("Max connection count reached!")
            return None

    def unregisterProtocol(self, p):
        WrappingFactory.unregisterProtocol(self, p)
        self.connectionCount -= 1
        if self.connectionCount == 0:
            if self.unthrottleReadsID is not None:
                self.unthrottleReadsID.cancel()
            if self.checkReadBandwidthID is not None:
                self.checkReadBandwidthID.cancel()
            if self.unthrottleWritesID is not None:
                self.unthrottleWritesID.cancel()
            if self.checkWriteBandwidthID is not None:
                self.checkWriteBandwidthID.cancel()

class SpewingProtocol(ProtocolWrapper):
    def dataReceived(self, data):
        log.msg("Received: %r" % data)
        ProtocolWrapper.dataReceived(self,data)

    def write(self, data):
        log.msg("Sending: %r" % data)
        ProtocolWrapper.write(self,data)

class SpewingFactory(WrappingFactory):
    protocol = SpewingProtocol

class LimitConnectionsByPeer(WrappingFactory):
    maxConnectionsPerPeer = 5

    def startFactory(self):
        self.peerConnections = {}

    def buildProtocol(self, addr):
        peerHost = addr[0]
        connectionCount = self.peerConnections.get(peerHost, 0)
        if connectionCount >= self.maxConnectionsPerPeer:
            return None
        self.peerConnections[peerHost] = connectionCount + 1
        return WrappingFactory.buildProtocol(self, addr)

    def unregisterProtocol(self, p):
        peerHost = p.getPeer()[1]
        self.peerConnections[peerHost] -= 1
        if self.peerConnections[peerHost] == 0:
            del self.peerConnections[peerHost]

class LimitTotalConnectionsFactory(ServerFactory):
    connectionCount = 0
    connectionLimit = None
    overflowProtocol = None

    def buildProtocol(self, addr):
        if (self.connectionLimit is None or
            self.connectionCount < self.connectionLimit):
                wrappedProtocol = self.protocol()
        elif self.overflowProtocol is None:
            return None
        else:
            wrappedProtocol = self.overflowProtocol()

        wrappedProtocol.factory = self
        protocol = ProtocolWrapper(self, wrappedProtocol)
        self.connectionCount += 1
        return protocol

    def registerProtocol(self, p):
        pass

    def unregisterProtocol(self, p):
        self.connectionCount -= 1

class TimeoutProtocol(ProtocolWrapper):
    def __init__(self, factory, wrappedProtocol, timeoutPeriod):
        ProtocolWrapper.__init__(self, factory, wrappedProtocol)
        self.timeoutCall = None
        self.setTimeout(timeoutPeriod)

    def setTimeout(self, timeoutPeriod=None):
        self.cancelTimeout()
        if timeoutPeriod is not None:
            self.timeoutPeriod = timeoutPeriod
        self.timeoutCall = self.factory.callLater(self.timeoutPeriod, self.timeoutFunc)

    def cancelTimeout(self):
        if self.timeoutCall:
            try:
                self.timeoutCall.cancel()
            except error.AlreadyCalled:
                pass
            self.timeoutCall = None

    def resetTimeout(self):
        if self.timeoutCall:
            self.timeoutCall.reset(self.timeoutPeriod)

    def write(self, data):
        self.resetTimeout()
        ProtocolWrapper.write(self, data)

    def writeSequence(self, seq):
        self.resetTimeout()
        ProtocolWrapper.writeSequence(self, seq)

    def dataReceived(self, data):
        self.resetTimeout()
        ProtocolWrapper.dataReceived(self, data)

    def connectionLost(self, reason):
        self.cancelTimeout()
        ProtocolWrapper.connectionLost(self, reason)

    def timeoutFunc(self):
        self.loseConnection()

class TimeoutFactory(WrappingFactory):
    protocol = TimeoutProtocol

    def __init__(self, wrappedFactory, timeoutPeriod=30*60):
        self.timeoutPeriod = timeoutPeriod
        WrappingFactory.__init__(self, wrappedFactory)

    def buildProtocol(self, addr):
        return self.protocol(self, self.wrappedFactory.buildProtocol(addr),
                             timeoutPeriod=self.timeoutPeriod)

    def callLater(self, period, func):
        from lib.twisted.internet import reactor
        return reactor.callLater(period, func)

class TrafficLoggingProtocol(ProtocolWrapper):
    def __init__(self, factory, wrappedProtocol, logfile, lengthLimit=None,
                 number=0):
        ProtocolWrapper.__init__(self, factory, wrappedProtocol)
        self.logfile = logfile
        self.lengthLimit = lengthLimit
        self._number = number

    def _log(self, line):
        self.logfile.write(line + '\n')
        self.logfile.flush()

    def _mungeData(self, data):
        if self.lengthLimit and len(data) > self.lengthLimit:
            data = data[:self.lengthLimit - 12] + '<... elided>'
        return data

    def connectionMade(self):
        self._log('*')
        return ProtocolWrapper.connectionMade(self)

    def dataReceived(self, data):
        self._log('C %d: %r' % (self._number, self._mungeData(data)))
        return ProtocolWrapper.dataReceived(self, data)

    def connectionLost(self, reason):
        self._log('C %d: %r' % (self._number, reason))
        return ProtocolWrapper.connectionLost(self, reason)

    def write(self, data):
        self._log('S %d: %r' % (self._number, self._mungeData(data)))
        return ProtocolWrapper.write(self, data)

    def writeSequence(self, iovec):
        self._log('SV %d: %r' % (self._number, [self._mungeData(d) for d in iovec]))
        return ProtocolWrapper.writeSequence(self, iovec)

    def loseConnection(self):
        self._log('S %d: *' % (self._number,))
        return ProtocolWrapper.loseConnection(self)

class TrafficLoggingFactory(WrappingFactory):
    protocol = TrafficLoggingProtocol
    _counter = 0

    def __init__(self, wrappedFactory, logfilePrefix, lengthLimit=None):
        self.logfilePrefix = logfilePrefix
        self.lengthLimit = lengthLimit
        WrappingFactory.__init__(self, wrappedFactory)

    def open(self, name):
        return file(name, 'w')

    def buildProtocol(self, addr):
        self._counter += 1
        logfile = self.open(self.logfilePrefix + '-' + str(self._counter))
        return self.protocol(self, self.wrappedFactory.buildProtocol(addr),
                             logfile, self.lengthLimit, self._counter)

    def resetCounter(self):
        self._counter = 0

class TimeoutMixin:
    timeOut = None
    __timeoutCall = None

    def callLater(self, period, func):
        from lib.twisted.internet import reactor
        return reactor.callLater(period, func)

    def resetTimeout(self):
        if self.__timeoutCall is not None and self.timeOut is not None:
            self.__timeoutCall.reset(self.timeOut)

    def setTimeout(self, period):
        prev = self.timeOut
        self.timeOut = period
        if self.__timeoutCall is not None:
            if period is None:
                self.__timeoutCall.cancel()
                self.__timeoutCall = None
            else:
                self.__timeoutCall.reset(period)
        elif period is not None:
            self.__timeoutCall = self.callLater(period, self.__timedOut)
        return prev

    def __timedOut(self):
        self.__timeoutCall = None
        self.timeoutConnection()

    def timeoutConnection(self):
        self.transport.loseConnection()