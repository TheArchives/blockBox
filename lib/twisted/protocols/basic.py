# -*- test-case-name: lib.twisted.test.test_protocols -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import re
import struct
import warnings
from lib.zope.interface import implements
from lib.twisted.internet import protocol, defer, interfaces, error
from lib.twisted.python import log
LENGTH, DATA, COMMA = range(3)
NUMBER = re.compile('(\d*)(:?)')
DEBUG = 0

class NetstringParseError(ValueError):
    pass

class NetstringReceiver(protocol.Protocol):
    MAX_LENGTH = 99999
    brokenPeer = 0
    _readerState = LENGTH
    _readerLength = 0

    def stringReceived(self, line):
        raise NotImplementedError

    def doData(self):
        buffer,self.__data = self.__data[:int(self._readerLength)],self.__data[int(self._readerLength):]
        self._readerLength = self._readerLength - len(buffer)
        self.__buffer = self.__buffer + buffer
        if self._readerLength != 0:
            return
        self.stringReceived(self.__buffer)
        self._readerState = COMMA

    def doComma(self):
        self._readerState = LENGTH
        if self.__data[0] != ',':
            if DEBUG:
                raise NetstringParseError(repr(self.__data))
            else:
                raise NetstringParseError
        self.__data = self.__data[1:]

    def doLength(self):
        m = NUMBER.match(self.__data)
        if not m.end():
            if DEBUG:
                raise NetstringParseError(repr(self.__data))
            else:
                raise NetstringParseError
        self.__data = self.__data[m.end():]
        if m.group(1):
            try:
                self._readerLength = self._readerLength * (10**len(m.group(1))) + long(m.group(1))
            except OverflowError:
                raise NetstringParseError, "netstring too long"
            if self._readerLength > self.MAX_LENGTH:
                raise NetstringParseError, "netstring too long"
        if m.group(2):
            self.__buffer = ''
            self._readerState = DATA

    def dataReceived(self, data):
        self.__data = data
        try:
            while self.__data:
                if self._readerState == DATA:
                    self.doData()
                elif self._readerState == COMMA:
                    self.doComma()
                elif self._readerState == LENGTH:
                    self.doLength()
                else:
                    raise RuntimeError, "mode is not DATA, COMMA or LENGTH"
        except NetstringParseError:
            self.transport.loseConnection()
            self.brokenPeer = 1

    def sendString(self, data):
        if not isinstance(data, str):
            warnings.warn(
                "data passed to sendString() must be a string. Non-string "
                "support is deprecated since Twisted 10.0",
                DeprecationWarning, 2)
            data = str(data)
        self.transport.write('%d:%s,' % (len(data), data))

class SafeNetstringReceiver(NetstringReceiver):

class LineOnlyReceiver(protocol.Protocol):
    _buffer = ''
    delimiter = '\r\n'
    MAX_LENGTH = 16384

    def dataReceived(self, data):
        """Translates bytes into lines, and calls lineReceived."""
        lines  = (self._buffer+data).split(self.delimiter)
        self._buffer = lines.pop(-1)
        for line in lines:
            if self.transport.disconnecting:
                return
            if len(line) > self.MAX_LENGTH:
                return self.lineLengthExceeded(line)
            else:
                self.lineReceived(line)
        if len(self._buffer) > self.MAX_LENGTH:
            return self.lineLengthExceeded(self._buffer)

    def lineReceived(self, line):
        raise NotImplementedError

    def sendLine(self, line):
        return self.transport.writeSequence((line,self.delimiter))

    def lineLengthExceeded(self, line):
        return error.ConnectionLost('Line length exceeded')

class _PauseableMixin:
    paused = False

    def pauseProducing(self):
        self.paused = True
        self.transport.pauseProducing()

    def resumeProducing(self):
        self.paused = False
        self.transport.resumeProducing()
        self.dataReceived('')

    def stopProducing(self):
        self.paused = True
        self.transport.stopProducing()

class LineReceiver(protocol.Protocol, _PauseableMixin):
    line_mode = 1
    __buffer = ''
    delimiter = '\r\n'
    MAX_LENGTH = 16384

    def clearLineBuffer(self):
        b = self.__buffer
        self.__buffer = ""
        return b

    def dataReceived(self, data):
        self.__buffer = self.__buffer+data
        while self.line_mode and not self.paused:
            try:
                line, self.__buffer = self.__buffer.split(self.delimiter, 1)
            except ValueError:
                if len(self.__buffer) > self.MAX_LENGTH:
                    line, self.__buffer = self.__buffer, ''
                    return self.lineLengthExceeded(line)
                break
            else:
                linelength = len(line)
                if linelength > self.MAX_LENGTH:
                    exceeded = line + self.__buffer
                    self.__buffer = ''
                    return self.lineLengthExceeded(exceeded)
                why = self.lineReceived(line)
                if why or self.transport and self.transport.disconnecting:
                    return why
        else:
            if not self.paused:
                data=self.__buffer
                self.__buffer=''
                if data:
                    return self.rawDataReceived(data)

    def setLineMode(self, extra=''):
        self.line_mode = 1
        if extra:
            return self.dataReceived(extra)

    def setRawMode(self):
        self.line_mode = 0

    def rawDataReceived(self, data):
        raise NotImplementedError

    def lineReceived(self, line):
        raise NotImplementedError

    def sendLine(self, line):
        return self.transport.write(line + self.delimiter)

    def lineLengthExceeded(self, line):
        return self.transport.loseConnection()


class StringTooLongError(AssertionError):

class IntNStringReceiver(protocol.Protocol, _PauseableMixin):
    MAX_LENGTH = 99999
    recvd = ""

    def stringReceived(self, msg):
        raise NotImplementedError

    def lengthLimitExceeded(self, length):
        self.transport.loseConnection()

    def dataReceived(self, recd):
        self.recvd = self.recvd + recd
        while len(self.recvd) >= self.prefixLength and not self.paused:
            length ,= struct.unpack(
                self.structFormat, self.recvd[:self.prefixLength])
            if length > self.MAX_LENGTH:
                self.lengthLimitExceeded(length)
                return
            if len(self.recvd) < length + self.prefixLength:
                break
            packet = self.recvd[self.prefixLength:length + self.prefixLength]
            self.recvd = self.recvd[length + self.prefixLength:]
            self.stringReceived(packet)

    def sendString(self, data):
        if len(data) >= 2 ** (8 * self.prefixLength):
            raise StringTooLongError(
                "Try to send %s bytes whereas maximum is %s" % (
                len(data), 2 ** (8 * self.prefixLength)))
        self.transport.write(struct.pack(self.structFormat, len(data)) + data)

class Int32StringReceiver(IntNStringReceiver):
    structFormat = "!I"
    prefixLength = struct.calcsize(structFormat)

class Int16StringReceiver(IntNStringReceiver):
    structFormat = "!H"
    prefixLength = struct.calcsize(structFormat)

class Int8StringReceiver(IntNStringReceiver):
    structFormat = "!B"
    prefixLength = struct.calcsize(structFormat)

class StatefulStringProtocol:
    state = 'init'

    def stringReceived(self,string):
        try:
            pto = 'proto_'+self.state
            statehandler = getattr(self,pto)
        except AttributeError:
            log.msg('callback',self.state,'not found')
        else:
            self.state = statehandler(string)
            if self.state == 'done':
                self.transport.loseConnection()

class FileSender:
    implements(interfaces.IProducer)
    CHUNK_SIZE = 2 ** 14
    lastSent = ''
    deferred = None

    def beginFileTransfer(self, file, consumer, transform = None):
        self.file = file
        self.consumer = consumer
        self.transform = transform

        self.deferred = deferred = defer.Deferred()
        self.consumer.registerProducer(self, False)
        return deferred

    def resumeProducing(self):
        chunk = ''
        if self.file:
            chunk = self.file.read(self.CHUNK_SIZE)
        if not chunk:
            self.file = None
            self.consumer.unregisterProducer()
            if self.deferred:
                self.deferred.callback(self.lastSent)
                self.deferred = None
            return

        if self.transform:
            chunk = self.transform(chunk)
        self.consumer.write(chunk)
        self.lastSent = chunk[-1]

    def pauseProducing(self):
        pass

    def stopProducing(self):
        if self.deferred:
            self.deferred.errback(Exception("Consumer asked us to stop producing"))
            self.deferred = None
