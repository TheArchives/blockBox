# -*- test-case-name: lib.twisted.words.test.test_jabbercomponent -*-
#
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.zope.interface import implements
from lib.twisted.application import service
from lib.twisted.internet import defer
from lib.twisted.python import log
from lib.twisted.words.xish import domish
from lib.twisted.words.protocols.jabber import error, ijabber, jstrports, xmlstream
from lib.twisted.words.protocols.jabber.jid import internJID as JID
NS_COMPONENT_ACCEPT = 'jabber:component:accept'

def componentFactory(componentid, password):
    a = ConnectComponentAuthenticator(componentid, password)
    return xmlstream.XmlStreamFactory(a)

class ComponentInitiatingInitializer(object):
    def __init__(self, xs):
        self.xmlstream = xs
        self._deferred = None

    def initialize(self):
        xs = self.xmlstream
        hs = domish.Element((self.xmlstream.namespace, "handshake"))
        hs.addContent(xmlstream.hashPassword(xs.sid,
                                             unicode(xs.authenticator.password)))

        xs.addOnetimeObserver("/handshake", self._cbHandshake)
        xs.send(hs)
        self._deferred = defer.Deferred()
        return self._deferred

    def _cbHandshake(self, _):
        self.xmlstream.thisEntity = self.xmlstream.otherEntity
        self._deferred.callback(None)

class ConnectComponentAuthenticator(xmlstream.ConnectAuthenticator):
    namespace = NS_COMPONENT_ACCEPT

    def __init__(self, componentjid, password):
        xmlstream.ConnectAuthenticator.__init__(self, componentjid)
        self.password = password

    def associateWithStream(self, xs):
        xs.version = (0, 0)
        xmlstream.ConnectAuthenticator.associateWithStream(self, xs)
        xs.initializers = [ComponentInitiatingInitializer(xs)]

class ListenComponentAuthenticator(xmlstream.ListenAuthenticator):
    namespace = NS_COMPONENT_ACCEPT

    def __init__(self, secret):
        self.secret = secret
        xmlstream.ListenAuthenticator.__init__(self)

    def associateWithStream(self, xs):
        xs.version = (0, 0)
        xmlstream.ListenAuthenticator.associateWithStream(self, xs)

    def streamStarted(self, rootElement):
        xmlstream.ListenAuthenticator.streamStarted(self, rootElement)

        if rootElement.defaultUri != self.namespace:
            exc = error.StreamError('invalid-namespace')
            self.xmlstream.sendStreamError(exc)
            return
        if not self.xmlstream.thisEntity:
            exc = error.StreamError('improper-addressing')
            self.xmlstream.sendStreamError(exc)
            return
        self.xmlstream.sendHeader()
        self.xmlstream.addOnetimeObserver('/*', self.onElement)

    def onElement(self, element):
        if (element.uri, element.name) == (self.namespace, 'handshake'):
            self.onHandshake(unicode(element))
        else:
            exc = error.StreamError('not-authorized')
            self.xmlstream.sendStreamError(exc)

    def onHandshake(self, handshake):
        calculatedHash = xmlstream.hashPassword(self.xmlstream.sid,
                                                unicode(self.secret))
        if handshake != calculatedHash:
            exc = error.StreamError('not-authorized', text='Invalid hash')
            self.xmlstream.sendStreamError(exc)
        else:
            self.xmlstream.send('<handshake/>')
            self.xmlstream.dispatch(self.xmlstream,
                                    xmlstream.STREAM_AUTHD_EVENT)

class Service(service.Service):
    implements(ijabber.IService)

    def componentConnected(self, xs):
        pass

    def componentDisconnected(self):
        pass

    def transportConnected(self, xs):
        pass

    def send(self, obj):
        self.parent.send(obj)

class ServiceManager(service.MultiService):
    def __init__(self, jid, password):
        service.MultiService.__init__(self)
        self.jabberId = jid
        self.xmlstream = None
        self._packetQueue = []
        self._xsFactory = componentFactory(self.jabberId, password)
        self._xsFactory.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT,
                                     self._connected)
        self._xsFactory.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self._authd)
        self._xsFactory.addBootstrap(xmlstream.STREAM_END_EVENT,
                                     self._disconnected)
        self.addBootstrap = self._xsFactory.addBootstrap
        self.removeBootstrap = self._xsFactory.removeBootstrap

    def getFactory(self):
        return self._xsFactory

    def _connected(self, xs):
        self.xmlstream = xs
        for c in self:
            if ijabber.IService.providedBy(c):
                c.transportConnected(xs)

    def _authd(self, xs):
        for p in self._packetQueue:
            self.xmlstream.send(p)
        self._packetQueue = []
        for c in self:
            if ijabber.IService.providedBy(c):
                c.componentConnected(xs)

    def _disconnected(self, _):
        self.xmlstream = None
        for c in self:
            if ijabber.IService.providedBy(c):
                c.componentDisconnected()

    def send(self, obj):
        if self.xmlstream != None:
            self.xmlstream.send(obj)
        else:
            self._packetQueue.append(obj)

def buildServiceManager(jid, password, strport):
    svc = ServiceManager(jid, password)
    client_svc = jstrports.client(strport, svc.getFactory())
    client_svc.setServiceParent(svc)
    return svc



class Router(object):
    def __init__(self):
        self.routes = {}

    def addRoute(self, destination, xs):
        self.routes[destination] = xs
        xs.addObserver('/*', self.route)

    def removeRoute(self, destination, xs):
        xs.removeObserver('/*', self.route)
        if (xs == self.routes[destination]):
            del self.routes[destination]

    def route(self, stanza):
        destination = JID(stanza['to'])

        log.msg("Routing to %s: %r" % (destination.full(), stanza.toXml()))

        if destination.host in self.routes:
            self.routes[destination.host].send(stanza)
        else:
            self.routes[None].send(stanza)

class XMPPComponentServerFactory(xmlstream.XmlStreamServerFactory):
    logTraffic = False

    def __init__(self, router, secret='secret'):
        self.router = router
        self.secret = secret

        def authenticatorFactory():
            return ListenComponentAuthenticator(self.secret)

        xmlstream.XmlStreamServerFactory.__init__(self, authenticatorFactory)
        self.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT,
                          self.onConnectionMade)
        self.addBootstrap(xmlstream.STREAM_AUTHD_EVENT,
                          self.onAuthenticated)

        self.serial = 0

    def onConnectionMade(self, xs):
        xs.serial = self.serial
        self.serial += 1

        def logDataIn(buf):
            log.msg("RECV (%d): %r" % (xs.serial, buf))

        def logDataOut(buf):
            log.msg("SEND (%d): %r" % (xs.serial, buf))

        if self.logTraffic:
            xs.rawDataInFn = logDataIn
            xs.rawDataOutFn = logDataOut

        xs.addObserver(xmlstream.STREAM_ERROR_EVENT, self.onError)

    def onAuthenticated(self, xs):
        destination = xs.thisEntity.host

        self.router.addRoute(destination, xs)
        xs.addObserver(xmlstream.STREAM_END_EVENT, self.onConnectionLost, 0,
                                                   destination, xs)

    def onError(self, reason):
        log.err(reason, "Stream Error")

    def onConnectionLost(self, destination, xs, reason):
        self.router.removeRoute(destination, xs)
