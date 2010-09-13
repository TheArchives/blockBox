# Copyright (c) 2008-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import socket, operator, errno, struct
from lib.zope.interface import implements, directlyProvides
from lib.twisted.internet import interfaces, error, address, main, defer
from lib.twisted.internet.abstract import isIPAddress
from lib.twisted.internet.tcp import _SocketCloser, Connector as TCPConnector
from lib.twisted.persisted import styles
from lib.twisted.python import log, failure, reflect, util
from lib.twisted.internet.iocpreactor import iocpsupport as _iocp, abstract
from lib.twisted.internet.iocpreactor.interfaces import IReadWriteHandle
from lib.twisted.internet.iocpreactor.const import ERROR_IO_PENDING
from lib.twisted.internet.iocpreactor.const import SO_UPDATE_CONNECT_CONTEXT
from lib.twisted.internet.iocpreactor.const import SO_UPDATE_ACCEPT_CONTEXT
from lib.twisted.internet.iocpreactor.const import ERROR_CONNECTION_REFUSED
from lib.twisted.internet.iocpreactor.const import ERROR_NETWORK_UNREACHABLE
try:
    from lib.twisted.protocols.tls import TLSMemoryBIOFactory, TLSMemoryBIOProtocol
except ImportError:
    TLSMemoryBIOProtocol = TLSMemoryBIOFactory = None
    _extraInterfaces = ()
else:
    _extraInterfaces = (interfaces.ITLSTransport,)
connectExErrors = {
        ERROR_CONNECTION_REFUSED: errno.WSAECONNREFUSED,
        ERROR_NETWORK_UNREACHABLE: errno.WSAENETUNREACH,
        }

class _BypassTLS(object):
    def __init__(self, connection):
        self._connection = connection

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def write(self, data):
        return abstract.FileHandle.write(self._connection, data)

    def writeSequence(self, iovec):
        return abstract.FileHandle.writeSequence(self._connection, iovec)

    def loseConnection(self, reason=None):
        return abstract.FileHandle.loseConnection(self._connection, reason)

class Connection(abstract.FileHandle, _SocketCloser):
    implements(IReadWriteHandle, interfaces.ITCPTransport,
               interfaces.ISystemHandle, *_extraInterfaces)

    _tls = False

    def __init__(self, sock, proto, reactor=None):
        abstract.FileHandle.__init__(self, reactor)
        self.socket = sock
        self.getFileHandle = sock.fileno
        self.protocol = proto

    def getHandle(self):
        return self.socket

    def dataReceived(self, rbuffer):
        self.protocol.dataReceived(str(rbuffer))

    def readFromHandle(self, bufflist, evt):
        return _iocp.recv(self.getFileHandle(), bufflist, evt)

    def writeToHandle(self, buff, evt):
        return _iocp.send(self.getFileHandle(), buff, evt)

    def _closeWriteConnection(self):
        try:
            getattr(self.socket, self._socketShutdownMethod)(1)
        except socket.error:
            pass
        p = interfaces.IHalfCloseableProtocol(self.protocol, None)
        if p:
            try:
                p.writeConnectionLost()
            except:
                f = failure.Failure()
                log.err()
                self.connectionLost(f)

    def readConnectionLost(self, reason):
        p = interfaces.IHalfCloseableProtocol(self.protocol, None)
        if p:
            try:
                p.readConnectionLost()
            except:
                log.err()
                self.connectionLost(failure.Failure())
        else:
            self.connectionLost(reason)

    def connectionLost(self, reason):
        abstract.FileHandle.connectionLost(self, reason)
        self._closeSocket()
        protocol = self.protocol
        del self.protocol
        del self.socket
        del self.getFileHandle
        protocol.connectionLost(reason)

    def logPrefix(self):
        return self.logstr

    def getTcpNoDelay(self):
        return operator.truth(self.socket.getsockopt(socket.IPPROTO_TCP,
                                                     socket.TCP_NODELAY))

    def setTcpNoDelay(self, enabled):
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, enabled)

    def getTcpKeepAlive(self):
        return operator.truth(self.socket.getsockopt(socket.SOL_SOCKET,
                                                     socket.SO_KEEPALIVE))

    def setTcpKeepAlive(self, enabled):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, enabled)

    if TLSMemoryBIOFactory is not None:
        def startTLS(self, contextFactory, normal=True):
            if normal:
                client = self._tlsClientDefault
            else:
                client = not self._tlsClientDefault
            tlsFactory = TLSMemoryBIOFactory(contextFactory, client, None)
            tlsProtocol = TLSMemoryBIOProtocol(tlsFactory, self.protocol, False)
            self.protocol = tlsProtocol
            self.getHandle = tlsProtocol.getHandle
            self.getPeerCertificate = tlsProtocol.getPeerCertificate
            directlyProvides(self, interfaces.ISSLTransport)
            self._tls = True
            self.protocol.makeConnection(_BypassTLS(self))

    def write(self, data):
        if self._tls:
            self.protocol.write(data)
        else:
            abstract.FileHandle.write(self, data)

    def writeSequence(self, iovec):
        if self._tls:
            self.protocol.writeSequence(iovec)
        else:
            abstract.FileHandle.writeSequence(self, iovec)

    def loseConnection(self, reason=None):
        if self._tls:
            if self.connected and not self.disconnecting:
                self.protocol.loseConnection()
        else:
            abstract.FileHandle.loseConnection(self, reason)

class Client(Connection):
    addressFamily = socket.AF_INET
    socketType = socket.SOCK_STREAM

    _tlsClientDefault = True

    def __init__(self, host, port, bindAddress, connector, reactor):
        self.connector = connector
        self.addr = (host, port)
        self.reactor = reactor
        if bindAddress is None:
            bindAddress = ('', 0)
        try:
            try:
                skt = reactor.createSocket(self.addressFamily, self.socketType)
            except socket.error, se:
                raise error.ConnectBindError(se[0], se[1])
            else:
                try:
                    skt.bind(bindAddress)
                except socket.error, se:
                    raise error.ConnectBindError(se[0], se[1])
                self.socket = skt
                Connection.__init__(self, skt, None, reactor)
                reactor.callLater(0, self.resolveAddress)
        except error.ConnectBindError, err:
            reactor.callLater(0, self.failIfNotConnected, err)

    def resolveAddress(self):
        if isIPAddress(self.addr[0]):
            self._setRealAddress(self.addr[0])
        else:
            d = self.reactor.resolve(self.addr[0])
            d.addCallbacks(self._setRealAddress, self.failIfNotConnected)

    def _setRealAddress(self, address):
        self.realAddress = (address, self.addr[1])
        self.doConnect()

    def failIfNotConnected(self, err):
        if (self.connected or self.disconnected or
            not hasattr(self, "connector")):
            return
        try:
            self._closeSocket()
        except AttributeError:
            pass
        else:
            del self.socket, self.getFileHandle
        self.reactor.removeActiveHandle(self)

        self.connector.connectionFailed(failure.Failure(err))
        del self.connector

    def stopConnecting(self):
        self.failIfNotConnected(error.UserError())

    def cbConnect(self, rc, bytes, evt):
        if rc:
            rc = connectExErrors.get(rc, rc)
            self.failIfNotConnected(error.getConnectError((rc,
                                    errno.errorcode.get(rc, 'Unknown error'))))
        else:
            self.socket.setsockopt(socket.SOL_SOCKET,
                                   SO_UPDATE_CONNECT_CONTEXT,
                                   struct.pack('I', self.socket.fileno()))
            self.protocol = self.connector.buildProtocol(self.getPeer())
            self.connected = True
            self.logstr = self.protocol.__class__.__name__+",client"
            self.protocol.makeConnection(self)
            self.startReading()

    def doConnect(self):
        if not hasattr(self, "connector"):
            return
        assert _iocp.have_connectex
        self.reactor.addActiveHandle(self)
        evt = _iocp.Event(self.cbConnect, self)
        rc = _iocp.connect(self.socket.fileno(), self.realAddress, evt)
        if rc == ERROR_IO_PENDING:
            return
        else:
            evt.ignore = True
            self.cbConnect(rc, 0, 0, evt)

    def getHost(self):
        return address.IPv4Address('TCP', *(self.socket.getsockname() +
                                            ('INET',)))

    def getPeer(self):
        return address.IPv4Address('TCP', *(self.realAddress + ('INET',)))

    def __repr__(self):
        s = ('<%s to %s at %x>' %
                (self.__class__, self.addr, util.unsignedID(self)))
        return s

    def connectionLost(self, reason):
        if not self.connected:
            self.failIfNotConnected(error.ConnectError(string=reason))
        else:
            Connection.connectionLost(self, reason)
            self.connector.connectionLost(reason)

class Server(Connection):
    _tlsClientDefault = False

    def __init__(self, sock, protocol, clientAddr, serverAddr, sessionno, reactor):
        Connection.__init__(self, sock, protocol, reactor)
        self.serverAddr = serverAddr
        self.clientAddr = clientAddr
        self.sessionno = sessionno
        self.logstr = "%s,%s,%s" % (self.protocol.__class__.__name__,
                                    sessionno, self.clientAddr.host)
        self.repstr = "<%s #%s on %s>" % (self.protocol.__class__.__name__,
                                          self.sessionno, self.serverAddr.port)
        self.connected = True
        self.startReading()

    def __repr__(self):
        return self.repstr

    def getHost(self):
        return self.serverAddr

    def getPeer(self):
        return self.clientAddr

class Connector(TCPConnector):
    def _makeTransport(self):
        return Client(self.host, self.port, self.bindAddress, self,
                      self.reactor)

class Port(styles.Ephemeral, _SocketCloser):
    implements(interfaces.IListeningPort)

    connected = False
    disconnected = False
    disconnecting = False
    addressFamily = socket.AF_INET
    socketType = socket.SOCK_STREAM
    sessionno = 0
    maxAccepts = 100
    _realPortNumber = None

    def __init__(self, port, factory, backlog=50, interface='', reactor=None):
        self.port = port
        self.factory = factory
        self.backlog = backlog
        self.interface = interface
        self.reactor = reactor

    def __repr__(self):
        if self._realPortNumber is not None:
            return "<%s of %s on %s>" % (self.__class__,
                                         self.factory.__class__,
                                         self._realPortNumber)
        else:
            return "<%s of %s (not listening)>" % (self.__class__,
                                                   self.factory.__class__)

    def startListening(self):
        try:
            skt = self.reactor.createSocket(self.addressFamily,
                                            self.socketType)
            skt.bind((self.interface, self.port))
        except socket.error, le:
            raise error.CannotListenError, (self.interface, self.port, le)
        self.addrLen = _iocp.maxAddrLen(skt.fileno())
        self._realPortNumber = skt.getsockname()[1]
        log.msg("%s starting on %s" % (self.factory.__class__,
                                       self._realPortNumber))
        self.factory.doStart()
        skt.listen(self.backlog)
        self.connected = True
        self.disconnected = False
        self.reactor.addActiveHandle(self)
        self.socket = skt
        self.getFileHandle = self.socket.fileno
        self.doAccept()

    def loseConnection(self, connDone=failure.Failure(main.CONNECTION_DONE)):
        self.disconnecting = True
        if self.connected:
            self.deferred = defer.Deferred()
            self.reactor.callLater(0, self.connectionLost, connDone)
            return self.deferred
    stopListening = loseConnection

    def connectionLost(self, reason):
        log.msg('(Port %s Closed)' % self._realPortNumber)
        self._realPortNumber = None
        d = None
        if hasattr(self, "deferred"):
            d = self.deferred
            del self.deferred
        self.disconnected = True
        self.reactor.removeActiveHandle(self)
        self.connected = False
        self._closeSocket()
        del self.socket
        del self.getFileHandle
        try:
            self.factory.doStop()
        except:
            self.disconnecting = False
            if d is not None:
                d.errback(failure.Failure())
            else:
                raise
        else:
            self.disconnecting = False
            if d is not None:
                d.callback(None)

    def logPrefix(self):
        return reflect.qual(self.factory.__class__)

    def getHost(self):
        return address.IPv4Address('TCP', *(self.socket.getsockname() +
                                            ('INET',)))

    def cbAccept(self, rc, bytes, evt):
        self.handleAccept(rc, evt)
        if not (self.disconnecting or self.disconnected):
            self.doAccept()

    def handleAccept(self, rc, evt):
        if self.disconnecting or self.disconnected:
            return False
        if rc:
            log.msg("Could not accept new connection -- %s (%s)" %
                    (errno.errorcode.get(rc, 'unknown error'), rc))
            return False
        else:
            evt.newskt.setsockopt(socket.SOL_SOCKET, SO_UPDATE_ACCEPT_CONTEXT,
                                  struct.pack('I', self.socket.fileno()))
            family, lAddr, rAddr = _iocp.get_accept_addrs(evt.newskt.fileno(),
                                                          evt.buff)
            assert family == self.addressFamily

            protocol = self.factory.buildProtocol(
                address._ServerFactoryIPv4Address('TCP', rAddr[0], rAddr[1]))
            if protocol is None:
                evt.newskt.close()
            else:
                s = self.sessionno
                self.sessionno = s+1
                transport = Server(evt.newskt, protocol,
                        address.IPv4Address('TCP', rAddr[0], rAddr[1], 'INET'),
                        address.IPv4Address('TCP', lAddr[0], lAddr[1], 'INET'),
                        s, self.reactor)
                protocol.makeConnection(transport)
            return True

    def doAccept(self):
        numAccepts = 0
        while 1:
            evt = _iocp.Event(self.cbAccept, self)
            evt.buff = buff = _iocp.AllocateReadBuffer(2 * (self.addrLen + 16))
            evt.newskt = newskt = self.reactor.createSocket(self.addressFamily,
                                                            self.socketType)
            rc = _iocp.accept(self.socket.fileno(), newskt.fileno(), buff, evt)
            if (rc == ERROR_IO_PENDING
                or (not rc and numAccepts >= self.maxAccepts)):
                break
            else:
                evt.ignore = True
                if not self.handleAccept(rc, evt):
                    break
            numAccepts += 1
