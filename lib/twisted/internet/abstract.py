# -*- test-case-name: lib.twisted.test.test_abstract -*-
# Copyright (c) 2001-2007 Twisted Matrix Laboratories.
# See LICENSE for details.

from lib.zope.interface import implements
from lib.twisted.python import log, reflect, failure
from lib.twisted.persisted import styles
from lib.twisted.internet import interfaces, main

class FileDescriptor(object):
    connected = 0
    producerPaused = 0
    streamingProducer = 0
    producer = None
    disconnected = 0
    disconnecting = 0
    _writeDisconnecting = False
    _writeDisconnected = False
    dataBuffer = ""
    offset = 0
    SEND_LIMIT = 128*1024
    implements(interfaces.IProducer, interfaces.IReadWriteDescriptor,
               interfaces.IConsumer, interfaces.ITransport, interfaces.IHalfCloseableDescriptor)

    def logPrefix(self):
        return "-"

    def __init__(self, reactor=None):
        if not reactor:
            from lib.twisted.internet import reactor
        self.reactor = reactor
        self._tempDataBuffer = []
        self._tempDataLen = 0

    def connectionLost(self, reason):
        self.disconnected = 1
        self.connected = 0
        if self.producer is not None:
            self.producer.stopProducing()
            self.producer = None
        self.stopReading()
        self.stopWriting()

    def writeSomeData(self, data):
        raise NotImplementedError("%s does not implement writeSomeData" %
                                  reflect.qual(self.__class__))

    def doRead(self):
        raise NotImplementedError("%s does not implement doRead" %
                                  reflect.qual(self.__class__))

    def doWrite(self):
        if len(self.dataBuffer) - self.offset < self.SEND_LIMIT:
            self.dataBuffer = buffer(self.dataBuffer, self.offset) + "".join(self._tempDataBuffer)
            self.offset = 0
            self._tempDataBuffer = []
            self._tempDataLen = 0

        if self.offset:
            l = self.writeSomeData(buffer(self.dataBuffer, self.offset))
        else:
            l = self.writeSomeData(self.dataBuffer)

        if l < 0 or isinstance(l, Exception):
            return l
        if l == 0 and self.dataBuffer:
            result = 0
        else:
            result = None
        self.offset += l
        if self.offset == len(self.dataBuffer) and not self._tempDataLen:
            self.dataBuffer = ""
            self.offset = 0
            self.stopWriting()
            if self.producer is not None and ((not self.streamingProducer)
                                              or self.producerPaused):
                self.producerPaused = 0
                self.producer.resumeProducing()
            elif self.disconnecting:
                return self._postLoseConnection()
            elif self._writeDisconnecting:
                result = self._closeWriteConnection()
                self._writeDisconnected = True
                return result
        return result

    def _postLoseConnection(self):
        return main.CONNECTION_DONE

    def _closeWriteConnection(self):
        pass

    def writeConnectionLost(self, reason):
        self.connectionLost(reason)

    def readConnectionLost(self, reason):
        self.connectionLost(reason)

    def write(self, data):
        if isinstance(data, unicode): 
            raise TypeError("Data must not be unicode")
        if not self.connected or self._writeDisconnected:
            return
        if data:
            self._tempDataBuffer.append(data)
            self._tempDataLen += len(data)
            if self.producer is not None and self.streamingProducer:
                if len(self.dataBuffer) + self._tempDataLen > self.bufferSize:
                    self.producerPaused = 1
                    self.producer.pauseProducing()
            self.startWriting()

    def writeSequence(self, iovec):
        if not self.connected or not iovec or self._writeDisconnected:
            return
        self._tempDataBuffer.extend(iovec)
        for i in iovec:
            self._tempDataLen += len(i)
        if self.producer is not None and self.streamingProducer:
            if len(self.dataBuffer) + self._tempDataLen > self.bufferSize:
                self.producerPaused = 1
                self.producer.pauseProducing()
        self.startWriting()

    def loseConnection(self, _connDone=failure.Failure(main.CONNECTION_DONE)):
        if self.connected and not self.disconnecting:
            if self._writeDisconnected:
                self.stopReading()
                self.stopWriting()
                self.connectionLost(_connDone)
            else:
                self.stopReading()
                self.startWriting()
                self.disconnecting = 1

    def loseWriteConnection(self):
        self._writeDisconnecting = True
        self.startWriting()

    def stopReading(self):
        self.reactor.removeReader(self)

    def stopWriting(self):
        self.reactor.removeWriter(self)

    def startReading(self):
        self.reactor.addReader(self)

    def startWriting(self):
        self.reactor.addWriter(self)

    producer = None
    bufferSize = 2**2**2**2

    def registerProducer(self, producer, streaming):
        if self.producer is not None:
            raise RuntimeError("Cannot register producer %s, because producer %s was never unregistered." % (producer, self.producer))
        if self.disconnected:
            producer.stopProducing()
        else:
            self.producer = producer
            self.streamingProducer = streaming
            if not streaming:
                producer.resumeProducing()

    def unregisterProducer(self):
        self.producer = None

    def stopConsuming(self):
        self.unregisterProducer()
        self.loseConnection()

    def resumeProducing(self):
        assert self.connected and not self.disconnecting
        self.startReading()

    def pauseProducing(self):
        self.stopReading()

    def stopProducing(self):
        self.loseConnection()

    def fileno(self):
        return -1

def isIPAddress(addr):
    dottedParts = addr.split('.')
    if len(dottedParts) == 4:
        for octet in dottedParts:
            try:
                value = int(octet)
            except ValueError:
                return False
            else:
                if value < 0 or value > 255:
                    return False
        return True
    return False

__all__ = ["FileDescriptor"]
