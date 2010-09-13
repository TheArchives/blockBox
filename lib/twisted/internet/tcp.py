# -*- test-case-name: lib.twisted.test.test_tcp -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.

# System Imports
import os
import types
import socket
import sys
import operator

from lib.zope.interface import implements, classImplements

try:
    from OpenSSL import SSL
except ImportError:
    SSL = None

from lib.twisted.python.runtime import platformType

if platformType == 'win32':
    EPERM = object()
    from errno import WSAEINVAL as EINVAL
    from errno import WSAEWOULDBLOCK as EWOULDBLOCK
    from errno import WSAEINPROGRESS as EINPROGRESS
    from errno import WSAEALREADY as EALREADY
    from errno import WSAECONNRESET as ECONNRESET
    from errno import WSAEISCONN as EISCONN
    from errno import WSAENOTCONN as ENOTCONN
    from errno import WSAEINTR as EINTR
    from errno import WSAENOBUFS as ENOBUFS
    from errno import WSAEMFILE as EMFILE
    ENFILE = object()
    ENOMEM = object()
    EAGAIN = EWOULDBLOCK
    from errno import WSAECONNRESET as ECONNABORTED

    from lib.twisted.python.win32 import formatError as strerror
else:
    from errno import EPERM
    from errno import EINVAL
    from errno import EWOULDBLOCK
    from errno import EINPROGRESS
    from errno import EALREADY
    from errno import ECONNRESET
    from errno import EISCONN
    from errno import ENOTCONN
    from errno import EINTR
    from errno import ENOBUFS
    from errno import EMFILE
    from errno import ENFILE
    from errno import ENOMEM
    from errno import EAGAIN
    from errno import ECONNABORTED
    from os import strerror
from errno import errorcode
from lib.twisted.internet import defer, base, address, fdesc
from lib.twisted.internet.task import deferLater
from lib.twisted.python import log, failure, reflect
from lib.twisted.python.util import unsignedID
from lib.twisted.internet.error import CannotListenError
from lib.twisted.internet import abstract, main, interfaces, error

class _SocketCloser:
    _socketShutdownMethod = 'shutdown'

    def _closeSocket(self):
        skt = self.socket
        try:
            getattr(skt, self._socketShutdownMethod)(2)
        except socket.error:
            pass
        try:
            skt.close()
        except socket.error:
            pass

class _TLSMixin:
    _socketShutdownMethod = 'sock_shutdown'

    writeBlockedOnRead = 0
    readBlockedOnWrite = 0
    _userWantRead = _userWantWrite = True

    def getPeerCertificate(self):
        return self.socket.get_peer_certificate()

    def doRead(self):
        if self.disconnected:
            return main.CONNECTION_DONE
        if self.writeBlockedOnRead:
            self.writeBlockedOnRead = 0
            self._resetReadWrite()
        try:
            return Connection.doRead(self)
        except SSL.ZeroReturnError:
            return main.CONNECTION_DONE
        except SSL.WantReadError:
            return
        except SSL.WantWriteError:
            self.readBlockedOnWrite = 1
            Connection.startWriting(self)
            Connection.stopReading(self)
            return
        except SSL.SysCallError, (retval, desc):
            if ((retval == -1 and desc == 'Unexpected EOF')
                or retval > 0):
                return main.CONNECTION_LOST
            log.err()
            return main.CONNECTION_LOST
        except SSL.Error, e:
            return e

    def doWrite(self):
        if self.disconnected:
            return self._postLoseConnection()
        if self._writeDisconnected:
            return self._closeWriteConnection()

        if self.readBlockedOnWrite:
            self.readBlockedOnWrite = 0
            self._resetReadWrite()
        return Connection.doWrite(self)

    def writeSomeData(self, data):
        try:
            return Connection.writeSomeData(self, data)
        except SSL.WantWriteError:
            return 0
        except SSL.WantReadError:
            self.writeBlockedOnRead = 1
            Connection.stopWriting(self)
            Connection.startReading(self)
            return 0
        except SSL.ZeroReturnError:
            return main.CONNECTION_LOST
        except SSL.SysCallError, e:
            if e[0] == -1 and data == "":
                return 0
            else:
                return main.CONNECTION_LOST
        except SSL.Error, e:
            return e

    def _postLoseConnection(self):
        self.disconnected = True
        if hasattr(self.socket, 'set_shutdown'):
            self.socket.set_shutdown(SSL.RECEIVED_SHUTDOWN)
        return self._sendCloseAlert()

    def _sendCloseAlert(self):
        try:
            os.write(self.socket.fileno(), '')
        except OSError, se:
            if se.args[0] in (EINTR, EWOULDBLOCK, ENOBUFS):
                return 0
            return main.CONNECTION_LOST

        try:
            if hasattr(self.socket, 'set_shutdown'):
                laststate = self.socket.get_shutdown()
                self.socket.set_shutdown(laststate | SSL.RECEIVED_SHUTDOWN)
                done = self.socket.shutdown()
                if not (laststate & SSL.RECEIVED_SHUTDOWN):
                    self.socket.set_shutdown(SSL.SENT_SHUTDOWN)
            else:
                #warnings.warn("SSL connection shutdown possibly unreliable, "
                #              "please upgrade to ver 0.XX", category=UserWarning)
                self.socket.shutdown()
                done = True
        except SSL.Error, e:
            return e

        if done:
            self.stopWriting()
            return main.CONNECTION_DONE
        else:
            self.startWriting()
            self.startReading()
            return None

    def _closeWriteConnection(self):
        result = self._sendCloseAlert()

        if result is main.CONNECTION_DONE:
            return Connection._closeWriteConnection(self)

        return result

    def startReading(self):
        self._userWantRead = True
        if not self.readBlockedOnWrite:
            return Connection.startReading(self)

    def stopReading(self):
        self._userWantRead = False
        if not self.writeBlockedOnRead:
            return Connection.stopReading(self)

    def startWriting(self):
        self._userWantWrite = True
        if not self.writeBlockedOnRead:
            return Connection.startWriting(self)

    def stopWriting(self):
        self._userWantWrite = False
        if not self.readBlockedOnWrite:
            return Connection.stopWriting(self)

    def _resetReadWrite(self):
        if self._userWantWrite:
            self.startWriting()
        else:
            self.stopWriting()

        if self._userWantRead:
            self.startReading()
        else:
            self.stopReading()

class _TLSDelayed(object):
    def __init__(self, bufferedData, context, extra):
        self.bufferedData = bufferedData
        self.context = context
        self.extra = extra

def _getTLSClass(klass, _existing={}):
    if klass not in _existing:
        class TLSConnection(_TLSMixin, klass):
            implements(interfaces.ISSLTransport)
        _existing[klass] = TLSConnection
    return _existing[klass]

class Connection(abstract.FileDescriptor, _SocketCloser):
    implements(interfaces.ITCPTransport, interfaces.ISystemHandle)
    TLS = 0

    def __init__(self, skt, protocol, reactor=None):
        abstract.FileDescriptor.__init__(self, reactor=reactor)
        self.socket = skt
        self.socket.setblocking(0)
        self.fileno = skt.fileno
        self.protocol = protocol

    if SSL:
        _tlsWaiting = None
        def startTLS(self, ctx, extra):
            assert not self.TLS
            if self.dataBuffer or self._tempDataBuffer:
                self._tlsWaiting = _TLSDelayed([], ctx, extra)
                return False

            self.stopReading()
            self.stopWriting()
            self._startTLS()
            self.socket = SSL.Connection(ctx.getContext(), self.socket)
            self.fileno = self.socket.fileno
            self.startReading()
            return True

        def _startTLS(self):
            self.TLS = 1
            self.__class__ = _getTLSClass(self.__class__)

        def write(self, bytes):
            if self._tlsWaiting is not None:
                self._tlsWaiting.bufferedData.append(bytes)
            else:
                abstract.FileDescriptor.write(self, bytes)

        def writeSequence(self, iovec):
            if self._tlsWaiting is not None:
                self._tlsWaiting.bufferedData.extend(iovec)
            else:
                abstract.FileDescriptor.writeSequence(self, iovec)

        def doWrite(self):
            result = abstract.FileDescriptor.doWrite(self)
            if self._tlsWaiting is not None:
                if not self.dataBuffer and not self._tempDataBuffer:
                    waiting = self._tlsWaiting
                    self._tlsWaiting = None
                    self.startTLS(waiting.context, waiting.extra)
                    self.writeSequence(waiting.bufferedData)
            return result

    def getHandle(self):
        return self.socket

    def doRead(self):
        try:
            data = self.socket.recv(self.bufferSize)
        except socket.error, se:
            if se.args[0] == EWOULDBLOCK:
                return
            else:
                return main.CONNECTION_LOST
        if not data:
            return main.CONNECTION_DONE
        return self.protocol.dataReceived(data)


    def writeSomeData(self, data):
        try:
            return self.socket.send(buffer(data, 0, self.SEND_LIMIT))
        except socket.error, se:
            if se.args[0] == EINTR:
                return self.writeSomeData(data)
            elif se.args[0] in (EWOULDBLOCK, ENOBUFS):
                return 0
            else:
                return main.CONNECTION_LOST

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
        abstract.FileDescriptor.connectionLost(self, reason)
        self._closeSocket()
        protocol = self.protocol
        del self.protocol
        del self.socket
        del self.fileno
        protocol.connectionLost(reason)

    logstr = "Uninitialized"

    def logPrefix(self):
        return self.logstr

    def getTcpNoDelay(self):
        return operator.truth(self.socket.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY))

    def setTcpNoDelay(self, enabled):
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, enabled)

    def getTcpKeepAlive(self):
        return operator.truth(self.socket.getsockopt(socket.SOL_SOCKET,
                                                     socket.SO_KEEPALIVE))

    def setTcpKeepAlive(self, enabled):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, enabled)

if SSL:
    classImplements(Connection, interfaces.ITLSTransport)

class BaseClient(Connection):
    addressFamily = socket.AF_INET
    socketType = socket.SOCK_STREAM

    def _finishInit(self, whenDone, skt, error, reactor):
        if whenDone:
            Connection.__init__(self, skt, None, reactor)
            self.doWrite = self.doConnect
            self.doRead = self.doConnect
            reactor.callLater(0, whenDone)
        else:
            reactor.callLater(0, self.failIfNotConnected, error)

    def startTLS(self, ctx, client=1):
        if Connection.startTLS(self, ctx, client):
            if client:
                self.socket.set_connect_state()
            else:
                self.socket.set_accept_state()

    def stopConnecting(self):
        self.failIfNotConnected(error.UserError())

    def failIfNotConnected(self, err):
        if (self.connected or self.disconnected or
            not hasattr(self, "connector")):
            return

        self.connector.connectionFailed(failure.Failure(err))
        if hasattr(self, "reactor"):
            self.stopReading()
            self.stopWriting()
            del self.connector

        try:
            self._closeSocket()
        except AttributeError:
            pass
        else:
            del self.socket, self.fileno

    def createInternetSocket(self):
        s = socket.socket(self.addressFamily, self.socketType)
        s.setblocking(0)
        fdesc._setCloseOnExec(s.fileno())
        return s

    def resolveAddress(self):
        if abstract.isIPAddress(self.addr[0]):
            self._setRealAddress(self.addr[0])
        else:
            d = self.reactor.resolve(self.addr[0])
            d.addCallbacks(self._setRealAddress, self.failIfNotConnected)

    def _setRealAddress(self, address):
        self.realAddress = (address, self.addr[1])
        self.doConnect()

    def doConnect(self):
        if not hasattr(self, "connector"):
            return

        err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err:
            self.failIfNotConnected(error.getConnectError((err, strerror(err))))
            return

        try:
            connectResult = self.socket.connect_ex(self.realAddress)
        except socket.error, se:
            connectResult = se.args[0]
        if connectResult:
            if connectResult == EISCONN:
                pass
            elif ((connectResult in (EWOULDBLOCK, EINPROGRESS, EALREADY)) or
                  (connectResult == EINVAL and platformType == "win32")):
                self.startReading()
                self.startWriting()
                return
            else:
                self.failIfNotConnected(error.getConnectError((connectResult, strerror(connectResult))))
                return
        del self.doWrite
        del self.doRead
        self.stopReading()
        self.stopWriting()
        self._connectDone()

    def _connectDone(self):
        self.protocol = self.connector.buildProtocol(self.getPeer())
        self.connected = 1
        self.logstr = self.protocol.__class__.__name__ + ",client"
        self.startReading()
        self.protocol.makeConnection(self)

    def connectionLost(self, reason):
        if not self.connected:
            self.failIfNotConnected(error.ConnectError(string=reason))
        else:
            Connection.connectionLost(self, reason)
            self.connector.connectionLost(reason)

class Client(BaseClient):

    def __init__(self, host, port, bindAddress, connector, reactor=None):
        self.connector = connector
        self.addr = (host, port)

        whenDone = self.resolveAddress
        err = None
        skt = None

        try:
            skt = self.createInternetSocket()
        except socket.error, se:
            err = error.ConnectBindError(se[0], se[1])
            whenDone = None
        if whenDone and bindAddress is not None:
            try:
                skt.bind(bindAddress)
            except socket.error, se:
                err = error.ConnectBindError(se[0], se[1])
                whenDone = None
        self._finishInit(whenDone, skt, err, reactor)

    def getHost(self):
        return address.IPv4Address('TCP', *(self.socket.getsockname() + ('INET',)))

    def getPeer(self):
        return address.IPv4Address('TCP', *(self.realAddress + ('INET',)))

    def __repr__(self):
        s = '<%s to %s at %x>' % (self.__class__, self.addr, unsignedID(self))
        return s

class Server(Connection):

    def __init__(self, sock, protocol, client, server, sessionno, reactor):
        Connection.__init__(self, sock, protocol, reactor)
        self.server = server
        self.client = client
        self.sessionno = sessionno
        self.hostname = client[0]
        self.logstr = "%s,%s,%s" % (self.protocol.__class__.__name__,
                                    sessionno,
                                    self.hostname)
        self.repstr = "<%s #%s on %s>" % (self.protocol.__class__.__name__,
                                          self.sessionno,
                                          self.server._realPortNumber)
        self.startReading()
        self.connected = 1

    def __repr__(self):
        return self.repstr

    def startTLS(self, ctx, server=1):
        if Connection.startTLS(self, ctx, server):
            if server:
                self.socket.set_accept_state()
            else:
                self.socket.set_connect_state()

    def getHost(self):
        return address.IPv4Address('TCP', *(self.socket.getsockname() + ('INET',)))

    def getPeer(self):
        return address.IPv4Address('TCP', *(self.client + ('INET',)))

class Port(base.BasePort, _SocketCloser):
    implements(interfaces.IListeningPort)

    addressFamily = socket.AF_INET
    socketType = socket.SOCK_STREAM

    transport = Server
    sessionno = 0
    interface = ''
    backlog = 50

    _realPortNumber = None

    def __init__(self, port, factory, backlog=50, interface='', reactor=None):
        base.BasePort.__init__(self, reactor=reactor)
        self.port = port
        self.factory = factory
        self.backlog = backlog
        self.interface = interface

    def __repr__(self):
        if self._realPortNumber is not None:
            return "<%s of %s on %s>" % (self.__class__, self.factory.__class__,
                                         self._realPortNumber)
        else:
            return "<%s of %s (not listening)>" % (self.__class__, self.factory.__class__)

    def createInternetSocket(self):
        s = base.BasePort.createInternetSocket(self)
        if platformType == "posix" and sys.platform != "cygwin":
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s

    def startListening(self):
        try:
            skt = self.createInternetSocket()
            skt.bind((self.interface, self.port))
        except socket.error, le:
            raise CannotListenError, (self.interface, self.port, le)
        self._realPortNumber = skt.getsockname()[1]

        log.msg("%s starting on %s" % (self.factory.__class__, self._realPortNumber))

        self.factory.doStart()
        skt.listen(self.backlog)
        self.connected = True
        self.socket = skt
        self.fileno = self.socket.fileno
        self.numberAccepts = 100

        self.startReading()

    def _buildAddr(self, (host, port)):
        return address._ServerFactoryIPv4Address('TCP', host, port)

    def doRead(self):
        try:
            if platformType == "posix":
                numAccepts = self.numberAccepts
            else:
                numAccepts = 1
            for i in range(numAccepts):
                if self.disconnecting:
                    return
                try:
                    skt, addr = self.socket.accept()
                except socket.error, e:
                    if e.args[0] in (EWOULDBLOCK, EAGAIN):
                        self.numberAccepts = i
                        break
                    elif e.args[0] == EPERM:
                        continue
                    elif e.args[0] in (EMFILE, ENOBUFS, ENFILE, ENOMEM, ECONNABORTED):
                        log.msg("Could not accept new connection (%s)" % (
                            errorcode[e.args[0]],))
                        break
                    raise

                fdesc._setCloseOnExec(skt.fileno())
                protocol = self.factory.buildProtocol(self._buildAddr(addr))
                if protocol is None:
                    skt.close()
                    continue
                s = self.sessionno
                self.sessionno = s+1
                transport = self.transport(skt, protocol, addr, self, s, self.reactor)
                transport = self._preMakeConnection(transport)
                protocol.makeConnection(transport)
            else:
                self.numberAccepts = self.numberAccepts+20
        except:
            log.deferr()

    def _preMakeConnection(self, transport):
        return transport

    def loseConnection(self, connDone=failure.Failure(main.CONNECTION_DONE)):
        self.disconnecting = True
        self.stopReading()
        if self.connected:
            self.deferred = deferLater(
                self.reactor, 0, self.connectionLost, connDone)
            return self.deferred

    stopListening = loseConnection

    def connectionLost(self, reason):
        log.msg('(Port %s Closed)' % self._realPortNumber)
        self._realPortNumber = None

        base.BasePort.connectionLost(self, reason)
        self.connected = False
        self._closeSocket()
        del self.socket
        del self.fileno

        try:
            self.factory.doStop()
        finally:
            self.disconnecting = False

    def logPrefix(self):
        return reflect.qual(self.factory.__class__)

    def getHost(self):
        return address.IPv4Address('TCP', *(self.socket.getsockname() + ('INET',)))

class Connector(base.BaseConnector):
    def __init__(self, host, port, factory, timeout, bindAddress, reactor=None):
        self.host = host
        if isinstance(port, types.StringTypes):
            try:
                port = socket.getservbyname(port, 'tcp')
            except socket.error, e:
                raise error.ServiceNameUnknownError(string="%s (%r)" % (e, port))
        self.port = port
        self.bindAddress = bindAddress
        base.BaseConnector.__init__(self, factory, timeout, reactor)

    def _makeTransport(self):
        return Client(self.host, self.port, self.bindAddress, self, self.reactor)

    def getDestination(self):
        return address.IPv4Address('TCP', self.host, self.port, 'INET')
