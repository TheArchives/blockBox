# -*- test-case-name: lib.twisted.test.test_pcp -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.zope.interface import implements
from lib.twisted.internet import interfaces

class BasicProducerConsumerProxy:
    implements(interfaces.IProducer, interfaces.IConsumer)
    consumer = None
    producer = None
    producerIsStreaming = None
    iAmStreaming = True
    outstandingPull = False
    paused = False
    stopped = False

    def __init__(self, consumer):
        self._buffer = []
        if consumer is not None:
            self.consumer = consumer
            consumer.registerProducer(self, self.iAmStreaming)

    def pauseProducing(self):
        self.paused = True
        if self.producer:
            self.producer.pauseProducing()

    def resumeProducing(self):
        self.paused = False
        if self._buffer:
            self.consumer.write(''.join(self._buffer))
            self._buffer[:] = []
        else:
            if not self.iAmStreaming:
                self.outstandingPull = True
        if self.producer is not None:
            self.producer.resumeProducing()

    def stopProducing(self):
        if self.producer is not None:
            self.producer.stopProducing()
        if self.consumer is not None:
            del self.consumer

    def write(self, data):
        if self.paused or (not self.iAmStreaming and not self.outstandingPull):
            self._buffer.append(data)

        elif self.consumer is not None:
            self.consumer.write(data)
            self.outstandingPull = False

    def finish(self):
        if self.consumer is not None:
            self.consumer.finish()
        self.unregisterProducer()

    def registerProducer(self, producer, streaming):
        self.producer = producer
        self.producerIsStreaming = streaming

    def unregisterProducer(self):
        if self.producer is not None:
            del self.producer
            del self.producerIsStreaming
        if self.consumer:
            self.consumer.unregisterProducer()

    def __repr__(self):
        return '<%s@%x around %s>' % (self.__class__, id(self), self.consumer)

class ProducerConsumerProxy(BasicProducerConsumerProxy):
    bufferSize = 2**2**2**2
    producerPaused = False
    unregistered = False

    def pauseProducing(self):
        self.paused = True

    def resumeProducing(self):
        self.paused = False
        if self._buffer:
            data = ''.join(self._buffer)
            bytesSent = self._writeSomeData(data)
            if bytesSent < len(data):
                unsent = data[bytesSent:]
                assert not self.iAmStreaming, (
                    "Streaming producer did not write all its data.")
                self._buffer[:] = [unsent]
            else:
                self._buffer[:] = []
        else:
            bytesSent = 0

        if (self.unregistered and bytesSent and not self._buffer and
            self.consumer is not None):
            self.consumer.unregisterProducer()

        if not self.iAmStreaming:
            self.outstandingPull = not bytesSent

        if self.producer is not None:
            bytesBuffered = sum([len(s) for s in self._buffer])
            if self.producerPaused and (bytesBuffered < self.bufferSize):
                self.producerPaused = False
                self.producer.resumeProducing()
            elif self.outstandingPull:
                self.producer.resumeProducing()

    def write(self, data):
        if self.paused or (not self.iAmStreaming and not self.outstandingPull):
            self._buffer.append(data)

        elif self.consumer is not None:
            assert not self._buffer, (
                "Writing fresh data to consumer before my buffer is empty!")
            bytesSent = self._writeSomeData(data)
            self.outstandingPull = False
            if not bytesSent == len(data):
                assert not self.iAmStreaming, (
                    "Streaming producer did not write all its data.")
                self._buffer.append(data[bytesSent:])

        if (self.producer is not None) and self.producerIsStreaming:
            bytesBuffered = sum([len(s) for s in self._buffer])
            if bytesBuffered >= self.bufferSize:
                self.producer.pauseProducing()
                self.producerPaused = True

    def registerProducer(self, producer, streaming):
        self.unregistered = False
        BasicProducerConsumerProxy.registerProducer(self, producer, streaming)
        if not streaming:
            producer.resumeProducing()

    def unregisterProducer(self):
        if self.producer is not None:
            del self.producer
            del self.producerIsStreaming
        self.unregistered = True
        if self.consumer and not self._buffer:
            self.consumer.unregisterProducer()

    def _writeSomeData(self, data):
        if self.consumer is None:
            return 0
        self.consumer.write(data)
        return len(data)
