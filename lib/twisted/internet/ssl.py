# -*- test-case-name: lib.twisted.test.test_ssl -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
supported = False
from OpenSSL import SSL
from lib.zope.interface import implements, implementsOnly, implementedBy
from lib.twisted.internet import tcp, interfaces, base, address

class ContextFactory:
    isClient = 0

    def getContext(self):
        raise NotImplementedError

class DefaultOpenSSLContextFactory(ContextFactory):
    _context = None

    def __init__(self, privateKeyFileName, certificateFileName,
                 sslmethod=SSL.SSLv23_METHOD, _contextFactory=SSL.Context):
        self.privateKeyFileName = privateKeyFileName
        self.certificateFileName = certificateFileName
        self.sslmethod = sslmethod
        self._contextFactory = _contextFactory
        self.cacheContext()

    def cacheContext(self):
        if self._context is None:
            ctx = self._contextFactory(self.sslmethod)
            ctx.set_options(SSL.OP_NO_SSLv2)
            ctx.use_certificate_file(self.certificateFileName)
            ctx.use_privatekey_file(self.privateKeyFileName)
            self._context = ctx

    def __getstate__(self):
        d = self.__dict__.copy()
        del d['_context']
        return d

    def __setstate__(self, state):
        self.__dict__ = state

    def getContext(self):
        return self._context

class ClientContextFactory:
    isClient = 1
    method = SSL.SSLv23_METHOD
    _contextFactory = SSL.Context

    def getContext(self):
        ctx = self._contextFactory(self.method)
        ctx.set_options(SSL.OP_NO_SSLv2)
        return ctx

class Client(tcp.Client):
    implementsOnly(interfaces.ISSLTransport,
                   *[i for i in implementedBy(tcp.Client) if i != interfaces.ITLSTransport])
    
    def __init__(self, host, port, bindAddress, ctxFactory, connector, reactor=None):
        self.ctxFactory = ctxFactory
        tcp.Client.__init__(self, host, port, bindAddress, connector, reactor)

    def getHost(self):
        h, p = self.socket.getsockname()
        return address.IPv4Address('TCP', h, p, 'SSL')

    def getPeer(self):
        return address.IPv4Address('TCP', self.addr[0], self.addr[1], 'SSL')

    def _connectDone(self):
        self.startTLS(self.ctxFactory)
        self.startWriting()
        tcp.Client._connectDone(self)

class Server(tcp.Server):
    implements(interfaces.ISSLTransport)
    
    def getHost(self):
        h, p = self.socket.getsockname()
        return address.IPv4Address('TCP', h, p, 'SSL')

    def getPeer(self):
        h, p = self.client
        return address.IPv4Address('TCP', h, p, 'SSL')

class Port(tcp.Port):
    _socketShutdownMethod = 'sock_shutdown'
    
    transport = Server

    def __init__(self, port, factory, ctxFactory, backlog=50, interface='', reactor=None):
        tcp.Port.__init__(self, port, factory, backlog, interface, reactor)
        self.ctxFactory = ctxFactory

    def createInternetSocket(self):
        sock = tcp.Port.createInternetSocket(self)
        return SSL.Connection(self.ctxFactory.getContext(), sock)

    def _preMakeConnection(self, transport):
        transport._startTLS()
        return tcp.Port._preMakeConnection(self, transport)

class Connector(base.BaseConnector):
    def __init__(self, host, port, factory, contextFactory, timeout, bindAddress, reactor=None):
        self.host = host
        self.port = port
        self.bindAddress = bindAddress
        self.contextFactory = contextFactory
        base.BaseConnector.__init__(self, factory, timeout, reactor)

    def _makeTransport(self):
        return Client(self.host, self.port, self.bindAddress, self.contextFactory, self, self.reactor)

    def getDestination(self):
        return address.IPv4Address('TCP', self.host, self.port, 'SSL')

from lib.twisted.internet._sslverify import DistinguishedName, DN, Certificate
from lib.twisted.internet._sslverify import CertificateRequest, PrivateCertificate
from lib.twisted.internet._sslverify import KeyPair
from lib.twisted.internet._sslverify import OpenSSLCertificateOptions as CertificateOptions
__all__ = [
    "ContextFactory", "DefaultOpenSSLContextFactory", "ClientContextFactory",

    'DistinguishedName', 'DN',
    'Certificate', 'CertificateRequest', 'PrivateCertificate',
    'KeyPair',
    'CertificateOptions',
    ]
supported = True
