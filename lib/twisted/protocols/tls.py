# -*- test-case-name: lib.twisted.protocols.test.test_tls,lib.twisted.internet.test.test_tls,lib.twisted.test.test_sslverify -*-
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.
from OpenSSL.SSL import Error, ZeroReturnError, WantReadError
from OpenSSL.SSL import TLSv1_METHOD, Context, Connection
try:
    Connection(Context(TLSv1_METHOD), None)
except TypeError, e:
    if str(e) != "argument must be an int, or have a fileno() method.":
        raise
    raise ImportError("lib.twisted.protocols.tls requires pyOpenSSL 0.10 or newer.")
from lib.zope.interface import implements
from lib.twisted.python.failure import Failure
from lib.twisted.internet.interfaces import ISystemHandle, ISSLTransport
from lib.twisted.internet.main import CONNECTION_DONE, CONNECTION_LOST
from lib.twisted.internet.protocol import Protocol
from lib.twisted.protocols.policies import ProtocolWrapper, WrappingFactory

class TLSMemoryBIOProtocol(ProtocolWrapper):
    implements(ISystemHandle, ISSLTransport)
    _reason = None
    _handshakeDone = False
    _lostConnection = False
    _writeBlockedOnRead = False

    def __init__(self, factory, wrappedProtocol, _connectWrapped=True):
        ProtocolWrapper.__init__(self, factory, wrappedProtocol)
        self._connectWrapped = _connectWrapped

    def getHandle(self):
        return self._tlsConnection

    def makeConnection(self, transport):
        tlsContext = self.factory._contextFactory.getContext()
        self._tlsConnection = Connection(tlsContext, None)
        if self.factory._isClient:
            self._tlsConnection.set_connect_state()
        else:
            self._tlsConnection.set_accept_state()
        self._appSendBuffer = []
        Protocol.makeConnection(self, transport)
        self.factory.registerProtocol(self)
        if self._connectWrapped:
            ProtocolWrapper.makeConnection(self, transport)
        try:
            self._tlsConnection.do_handshake()
        except WantReadError:
            self._flushSendBIO()

    def _flushSendBIO(self):
        try:
            bytes = self._tlsConnection.bio_read(2 ** 15)
        except WantReadError:
            pass
        else:
            self.transport.write(bytes)

    def _flushReceiveBIO(self):
        while not self._lostConnection:
            try:
                bytes = self._tlsConnection.recv(2 ** 15)
            except WantReadError:
                break
            except ZeroReturnError:
                self._lostConnection = True
                self.transport.loseConnection()
                if not self._handshakeDone and self._reason is not None:
                    failure = self._reason
                else:
                    failure = Failure(CONNECTION_DONE)
                self._reason = None
                ProtocolWrapper.connectionLost(self, failure)
            except Error, e:
                self._flushSendBIO()
                self._lostConnection = True
                if e.args[0] == -1 and e.args[1] == 'Unexpected EOF':
                    failure = Failure(CONNECTION_LOST)
                else:
                    failure = Failure()
                ProtocolWrapper.connectionLost(self, failure)
                self.transport.loseConnection()
            else:
                self._handshakeDone = True
                ProtocolWrapper.dataReceived(self, bytes)
        self._flushSendBIO()


    def dataReceived(self, bytes):
        self._tlsConnection.bio_write(bytes)
        if self._writeBlockedOnRead:
            self._writeBlockedOnRead = False
            appSendBuffer = self._appSendBuffer
            self._appSendBuffer = []
            for bytes in appSendBuffer:
                self.write(bytes)
            if not self._writeBlockedOnRead and self.disconnecting:
                self.loseConnection()
        self._flushReceiveBIO()

    def connectionLost(self, reason):
        if not self._lostConnection:
            self._tlsConnection.bio_shutdown()
            self._flushReceiveBIO()

    def loseConnection(self):
        self.disconnecting = True
        if not self._writeBlockedOnRead:
            self._tlsConnection.shutdown()
            self._flushSendBIO()
            self.transport.loseConnection()

    def write(self, bytes):
        if self._lostConnection:
            return

        leftToSend = bytes
        while leftToSend:
            try:
                sent = self._tlsConnection.send(leftToSend)
            except WantReadError:
                self._writeBlockedOnRead = True
                self._appSendBuffer.append(leftToSend)
                break
            except Error, e:
                self._reason = Failure()
                self.transport.loseConnection()
                break
            else:
                self._handshakeDone = True
                self._flushSendBIO()
                leftToSend = leftToSend[sent:]

    def writeSequence(self, iovec):
        self.write("".join(iovec))

    def getPeerCertificate(self):
        return self._tlsConnection.get_peer_certificate()

class TLSMemoryBIOFactory(WrappingFactory):
    protocol = TLSMemoryBIOProtocol

    def __init__(self, contextFactory, isClient, wrappedFactory):
        WrappingFactory.__init__(self, wrappedFactory)
        self._contextFactory = contextFactory
        self._isClient = isClient
