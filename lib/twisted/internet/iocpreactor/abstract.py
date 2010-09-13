# Copyright (c) 2008 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.twisted.internet import main, error, interfaces
from lib.twisted.python import log, failure
from lib.twisted.persisted import styles
from lib.zope.interface import implements
import errno
from lib.twisted.internet.iocpreactor.const import ERROR_HANDLE_EOF
from lib.twisted.internet.iocpreactor.const import ERROR_IO_PENDING
from lib.twisted.internet.iocpreactor import iocpsupport as _iocp

class FileHandle(log.Logger, styles.Ephemeral, object):
    implements(interfaces.IProducer, interfaces.IConsumer,
               interfaces.ITransport, interfaces.IHalfCloseableDescriptor)
    maxReadBuffers = 16
    readBufferSize = 4096
    reading = False
    dynamicReadBuffers = True
    _readNextBuffer = 0
    _readSize = 0
    _readScheduled = None
    _readScheduledInOS = False

    def startReading(self):
        self.reactor.addActiveHandle(self)
        if not self._readScheduled and not self.reading:
            self.reading = True
            self._readScheduled = self.reactor.callLater(0,
                                                         self._resumeReading)

    def stopReading(self):
        if self._readScheduled:
            self._readScheduled.cancel()
            self._readScheduled = None
        self.reading = False

    def _resumeReading(self):
        self._readScheduled = None
        if self._dispatchData() and not self._readScheduledInOS:
            self.doRead()

    def _dispatchData(self):
        if not self._readSize:
            return self.reading
        size = self._readSize
        full_buffers = size // self.readBufferSize
        while self._readNextBuffer < full_buffers:
            self.dataReceived(self._readBuffers[self._readNextBuffer])
            self._readNextBuffer += 1
            if not self.reading:
                return False
        remainder = size % self.readBufferSize
        if remainder:
            self.dataReceived(buffer(self._readBuffers[full_buffers],
                                     0, remainder))
        if self.dynamicReadBuffers:
            total_buffer_size = self.readBufferSize * len(self._readBuffers)
            if size < total_buffer_size - self.readBufferSize:
                del self._readBuffers[-1]
            elif (size == total_buffer_size and
                  len(self._readBuffers) < self.maxReadBuffers):
                self._readBuffers.append(_iocp.AllocateReadBuffer(
                                            self.readBufferSize))
        self._readNextBuffer = 0
        self._readSize = 0
        return self.reading

    def _cbRead(self, rc, bytes, evt):
        self._readScheduledInOS = False
        if self._handleRead(rc, bytes, evt):
            self.doRead()

    def _handleRead(self, rc, bytes, evt):
        if self.disconnected:
            return False
        if (not (rc or bytes)) or rc in (errno.WSAEDISCON, ERROR_HANDLE_EOF):
            self.reactor.removeActiveHandle(self)
            self.readConnectionLost(failure.Failure(main.CONNECTION_DONE))
            return False
        elif rc:
            self.connectionLost(failure.Failure(
                                error.ConnectionLost("read error -- %s (%s)" %
                                    (errno.errorcode.get(rc, 'unknown'), rc))))
            return False
        else:
            assert self._readSize == 0
            assert self._readNextBuffer == 0
            self._readSize = bytes
            return self._dispatchData()

    def doRead(self):
        numReads = 0
        while 1:
            evt = _iocp.Event(self._cbRead, self)

            evt.buff = buff = self._readBuffers
            rc, bytes = self.readFromHandle(buff, evt)

            if (rc == ERROR_IO_PENDING
                or (not rc and numReads >= self.maxReads)):
                self._readScheduledInOS = True
                break
            else:
                evt.ignore = True
                if not self._handleRead(rc, bytes, evt):
                    break
            numReads += 1

    def readFromHandle(self, bufflist, evt):
        raise NotImplementedError()

    def dataReceived(self, data):
        raise NotImplementedError

    def readConnectionLost(self, reason):
        self.connectionLost(reason)

    dataBuffer = ''
    offset = 0
    writing = False
    _writeScheduled = None
    _writeDisconnecting = False
    _writeDisconnected = False
    writeBufferSize = 2**2**2**2
    maxWrites = 5

    def loseWriteConnection(self):
        self._writeDisconnecting = True
        self.startWriting()

    def _closeWriteConnection(self):
        pass

    def writeConnectionLost(self, reason):
        self.connectionLost(reason)

    def startWriting(self):
        self.reactor.addActiveHandle(self)
        self.writing = True
        if not self._writeScheduled:
            self._writeScheduled = self.reactor.callLater(0,
                                                          self._resumeWriting)

    def stopWriting(self):
        if self._writeScheduled:
            self._writeScheduled.cancel()
            self._writeScheduled = None
        self.writing = False

    def _resumeWriting(self):
        self._writeScheduled = None
        self.doWrite()

    def _cbWrite(self, rc, bytes, evt):
        if self._handleWrite(rc, bytes, evt):
            self.doWrite()

    def _handleWrite(self, rc, bytes, evt):
        """
        Returns false if we should stop writing for now
        """
        if self.disconnected or self._writeDisconnected:
            return False
        if rc:
            self.connectionLost(failure.Failure(
                                error.ConnectionLost("write error -- %s (%s)" %
                                    (errno.errorcode.get(rc, 'unknown'), rc))))
            return False
        else:
            self.offset += bytes
            if self.offset == len(self.dataBuffer) and not self._tempDataLen:
                self.dataBuffer = ""
                self.offset = 0
                self.stopWriting()
                if self.producer is not None and ((not self.streamingProducer)
                                                  or self.producerPaused):
                    self.producerPaused = True
                    self.producer.resumeProducing()
                elif self.disconnecting:
                    self.connectionLost(failure.Failure(main.CONNECTION_DONE))
                elif self._writeDisconnecting:
                    self._closeWriteConnection()
                    self._writeDisconnected = True
                return False
            else:
                return True

    def doWrite(self):
        numWrites = 0
        while 1:
            if len(self.dataBuffer) - self.offset < self.SEND_LIMIT:
                self.dataBuffer = (buffer(self.dataBuffer, self.offset) +
                                   "".join(self._tempDataBuffer))
                self.offset = 0
                self._tempDataBuffer = []
                self._tempDataLen = 0
            evt = _iocp.Event(self._cbWrite, self)
            if self.offset:
                evt.buff = buff = buffer(self.dataBuffer, self.offset)
            else:
                evt.buff = buff = self.dataBuffer
            rc, bytes = self.writeToHandle(buff, evt)
            if (rc == ERROR_IO_PENDING
                or (not rc and numWrites >= self.maxWrites)):
                break
            else:
                evt.ignore = True
                if not self._handleWrite(rc, bytes, evt):
                    break
            numWrites += 1

    def writeToHandle(self, buff, evt):
        raise NotImplementedError()

    def write(self, data):
        if isinstance(data, unicode):
            raise TypeError("Data must not be unicode")
        if not self.connected or self._writeDisconnected:
            return
        if data:
            self._tempDataBuffer.append(data)
            self._tempDataLen += len(data)
            if self.producer is not None:
                if (len(self.dataBuffer) + self._tempDataLen
                    > self.writeBufferSize):
                    self.producerPaused = True
                    self.producer.pauseProducing()
            self.startWriting()

    def writeSequence(self, iovec):
        if not self.connected or not iovec or self._writeDisconnected:
            return
        self._tempDataBuffer.extend(iovec)
        for i in iovec:
            self._tempDataLen += len(i)
        if self.producer is not None:
            if len(self.dataBuffer) + self._tempDataLen > self.writeBufferSize:
                self.producerPaused = True
                self.producer.pauseProducing()
        self.startWriting()

    connected = False
    disconnected = False
    disconnecting = False
    logstr = "Uninitialized"
    SEND_LIMIT = 128*1024
    maxReads = 5

    def __init__(self, reactor = None):
        if not reactor:
            from lib.twisted.internet import reactor
        self.reactor = reactor
        self._tempDataBuffer = []
        self._tempDataLen = 0
        self._readBuffers = [_iocp.AllocateReadBuffer(self.readBufferSize)]

    def connectionLost(self, reason):
        self.disconnected = True
        self.connected = False
        if self.producer is not None:
            self.producer.stopProducing()
            self.producer = None
        self.stopReading()
        self.stopWriting()
        self.reactor.removeActiveHandle(self)

    def getFileHandle(self):
        return -1

    def loseConnection(self, _connDone=failure.Failure(main.CONNECTION_DONE)):
        if self.connected and not self.disconnecting:
            if self._writeDisconnected:
                self.stopReading()
                self.stopWriting
                self.connectionLost(_connDone)
            else:
                self.stopReading()
                self.startWriting()
                self.disconnecting = 1

    producerPaused = False
    streamingProducer = False
    producer = None

    def registerProducer(self, producer, streaming):
        if self.producer is not None:
            raise RuntimeError(
                "Cannot register producer %s, because producer "
                "%s was never unregistered." % (producer, self.producer))
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

__all__ = ['FileHandle']

