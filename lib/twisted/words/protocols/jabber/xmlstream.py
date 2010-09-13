# -*- test-case-name: lib.twisted.words.test.test_jabberxmlstream -*-
#
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.zope.interface import directlyProvides, implements
from lib.twisted.internet import defer, protocol
from lib.twisted.internet.error import ConnectionLost
from lib.twisted.python import failure, log, randbytes
from lib.twisted.python.hashlib import sha1
from lib.twisted.words.protocols.jabber import error, ijabber, jid
from lib.twisted.words.xish import domish, xmlstream
from lib.twisted.words.xish.xmlstream import STREAM_CONNECTED_EVENT
from lib.twisted.words.xish.xmlstream import STREAM_START_EVENT
from lib.twisted.words.xish.xmlstream import STREAM_END_EVENT
from lib.twisted.words.xish.xmlstream import STREAM_ERROR_EVENT
try:
    from lib.twisted.internet import ssl
except ImportError:
    ssl = None
if ssl and not ssl.supported:
    ssl = None
STREAM_AUTHD_EVENT = intern("//event/stream/authd")
INIT_FAILED_EVENT = intern("//event/xmpp/initfailed")
NS_STREAMS = 'http://etherx.jabber.org/streams'
NS_XMPP_TLS = 'urn:ietf:params:xml:ns:xmpp-tls'
Reset = object()

def hashPassword(sid, password):
    if not isinstance(sid, unicode):
        raise TypeError("The session identifier must be a unicode object")
    if not isinstance(password, unicode):
        raise TypeError("The password must be a unicode object")
    input = u"%s%s" % (sid, password)
    return sha1(input.encode('utf-8')).hexdigest()

class Authenticator:
    def __init__(self):
        self.xmlstream = None

    def connectionMade(self):

    def streamStarted(self, rootElement):
        if rootElement.hasAttribute("version"):
            version = rootElement["version"].split(".")
            try:
                version = (int(version[0]), int(version[1]))
            except (IndexError, ValueError):
                version = (0, 0)
        else:
            version = (0, 0)

        self.xmlstream.version = min(self.xmlstream.version, version)

    def associateWithStream(self, xmlstream):
        self.xmlstream = xmlstream

class ConnectAuthenticator(Authenticator):
    namespace = None

    def __init__(self, otherHost):
        self.otherHost = otherHost

    def connectionMade(self):
        self.xmlstream.namespace = self.namespace
        self.xmlstream.otherEntity = jid.internJID(self.otherHost)
        self.xmlstream.sendHeader()

    def initializeStream(self):

        def remove_first(result):
            self.xmlstream.initializers.pop(0)
            return result

        def do_next(result):
            if result is Reset:
                return None

            try:
                init = self.xmlstream.initializers[0]
            except IndexError:
                self.xmlstream.dispatch(self.xmlstream, STREAM_AUTHD_EVENT)
                return None
            else:
                d = defer.maybeDeferred(init.initialize)
                d.addCallback(remove_first)
                d.addCallback(do_next)
                return d

        d = defer.succeed(None)
        d.addCallback(do_next)
        d.addErrback(self.xmlstream.dispatch, INIT_FAILED_EVENT)

    def streamStarted(self, rootElement):
        Authenticator.streamStarted(self, rootElement)
        self.xmlstream.sid = rootElement.getAttribute("id")
        if rootElement.hasAttribute("from"):
            self.xmlstream.otherEntity = jid.internJID(rootElement["from"])

        if self.xmlstream.version >= (1, 0):
            def onFeatures(element):
                features = {}
                for feature in element.elements():
                    features[(feature.uri, feature.name)] = feature
                self.xmlstream.features = features
                self.initializeStream()
            self.xmlstream.addOnetimeObserver('/features[@xmlns="%s"]' %
                                                  NS_STREAMS,
                                              onFeatures)
        else:
            self.initializeStream()

class ListenAuthenticator(Authenticator):
    namespace = None

    def associateWithStream(self, xmlstream):
        Authenticator.associateWithStream(self, xmlstream)
        self.xmlstream.initiating = False

    def streamStarted(self, rootElement):
        Authenticator.streamStarted(self, rootElement)

        self.xmlstream.namespace = rootElement.defaultUri

        if rootElement.hasAttribute("to"):
            self.xmlstream.thisEntity = jid.internJID(rootElement["to"])

        self.xmlstream.prefixes = {}
        for prefix, uri in rootElement.localPrefixes.iteritems():
            self.xmlstream.prefixes[uri] = prefix

        self.xmlstream.sid = unicode(randbytes.secureRandom(8).encode('hex'))

class FeatureNotAdvertized(Exception):

class BaseFeatureInitiatingInitializer(object):
    implements(ijabber.IInitiatingInitializer)

    feature = None
    required = False

    def __init__(self, xs):
        self.xmlstream = xs

    def initialize(self):
        if self.feature in self.xmlstream.features:
            return self.start()
        elif self.required:
            raise FeatureNotAdvertized
        else:
            return None

    def start(self):

class TLSError(Exception):

class TLSFailed(TLSError):

class TLSRequired(TLSError):

class TLSNotSupported(TLSError):

class TLSInitiatingInitializer(BaseFeatureInitiatingInitializer):
    feature = (NS_XMPP_TLS, 'starttls')
    wanted = True
    _deferred = None

    def onProceed(self, obj):
        self.xmlstream.removeObserver('/failure', self.onFailure)
        ctx = ssl.CertificateOptions()
        self.xmlstream.transport.startTLS(ctx)
        self.xmlstream.reset()
        self.xmlstream.sendHeader()
        self._deferred.callback(Reset)

    def onFailure(self, obj):
        self.xmlstream.removeObserver('/proceed', self.onProceed)
        self._deferred.errback(TLSFailed())

    def start(self):
        if self.wanted:
            if ssl is None:
                if self.required:
                    return defer.fail(TLSNotSupported())
                else:
                    return defer.succeed(None)
            else:
                pass
        elif self.xmlstream.features[self.feature].required:
            return defer.fail(TLSRequired())
        else:
            return defer.succeed(None)

        self._deferred = defer.Deferred()
        self.xmlstream.addOnetimeObserver("/proceed", self.onProceed)
        self.xmlstream.addOnetimeObserver("/failure", self.onFailure)
        self.xmlstream.send(domish.Element((NS_XMPP_TLS, "starttls")))
        return self._deferred

class XmlStream(xmlstream.XmlStream):
    version = (1, 0)
    namespace = 'invalid'
    thisEntity = None
    otherEntity = None
    sid = None
    initiating = True
    _headerSent = False     # True if the stream header has been sent
    def __init__(self, authenticator):
        xmlstream.XmlStream.__init__(self)

        self.prefixes = {NS_STREAMS: 'stream'}
        self.authenticator = authenticator
        self.initializers = []
        self.features = {}
        authenticator.associateWithStream(self)

    def _callLater(self, *args, **kwargs):
        from lib.twisted.internet import reactor
        return reactor.callLater(*args, **kwargs)

    def reset(self):
        self._headerSent = False
        self._initializeStream()

    def onStreamError(self, errelem):
        self.dispatch(failure.Failure(error.exceptionFromStreamError(errelem)),
                      STREAM_ERROR_EVENT)
        self.transport.loseConnection()

    def sendHeader(self):
        localPrefixes = {}
        for uri, prefix in self.prefixes.iteritems():
            if uri != NS_STREAMS:
                localPrefixes[prefix] = uri

        rootElement = domish.Element((NS_STREAMS, 'stream'), self.namespace,
                                     localPrefixes=localPrefixes)

        if self.otherEntity:
            rootElement['to'] = self.otherEntity.userhost()

        if self.thisEntity:
            rootElement['from'] = self.thisEntity.userhost()

        if not self.initiating and self.sid:
            rootElement['id'] = self.sid

        if self.version >= (1, 0):
            rootElement['version'] = "%d.%d" % self.version

        self.send(rootElement.toXml(prefixes=self.prefixes, closeElement=0))
        self._headerSent = True

    def sendFooter(self):
        self.send('</stream:stream>')

    def sendStreamError(self, streamError):
        if not self._headerSent and not self.initiating:
            self.sendHeader()

        if self._headerSent:
            self.send(streamError.getElement())
            self.sendFooter()

        self.transport.loseConnection()

    def send(self, obj):
        if domish.IElement.providedBy(obj):
            obj = obj.toXml(prefixes=self.prefixes,
                            defaultUri=self.namespace,
                            prefixesInScope=self.prefixes.values())

        xmlstream.XmlStream.send(self, obj)

    def connectionMade(self):
        xmlstream.XmlStream.connectionMade(self)
        self.authenticator.connectionMade()

    def onDocumentStart(self, rootElement):
        xmlstream.XmlStream.onDocumentStart(self, rootElement)
        self.addOnetimeObserver("/error[@xmlns='%s']" % NS_STREAMS,
                                self.onStreamError)
        self.authenticator.streamStarted(rootElement)

class XmlStreamFactory(xmlstream.XmlStreamFactory):
    protocol = XmlStream

    def __init__(self, authenticator):
        xmlstream.XmlStreamFactory.__init__(self, authenticator)
        self.authenticator = authenticator

class XmlStreamServerFactory(xmlstream.BootstrapMixin,
                             protocol.ServerFactory):
    protocol = XmlStream

    def __init__(self, authenticatorFactory):
        xmlstream.BootstrapMixin.__init__(self)
        self.authenticatorFactory = authenticatorFactory

    def buildProtocol(self, addr):
        authenticator = self.authenticatorFactory()
        xs = self.protocol(authenticator)
        xs.factory = self
        self.installBootstraps(xs)
        return xs

class TimeoutError(Exception):

def upgradeWithIQResponseTracker(xs):
    def callback(iq):
        if getattr(iq, 'handled', False):
            return

        try:
            d = xs.iqDeferreds[iq["id"]]
        except KeyError:
            pass
        else:
            del xs.iqDeferreds[iq["id"]]
            iq.handled = True
            if iq['type'] == 'error':
                d.errback(error.exceptionFromStanza(iq))
            else:
                d.callback(iq)

    def disconnected(_):
        iqDeferreds = xs.iqDeferreds
        xs.iqDeferreds = {}
        for d in iqDeferreds.itervalues():
            d.errback(ConnectionLost())

    xs.iqDeferreds = {}
    xs.iqDefaultTimeout = getattr(xs, 'iqDefaultTimeout', None)
    xs.addObserver(xmlstream.STREAM_END_EVENT, disconnected)
    xs.addObserver('/iq[@type="result"]', callback)
    xs.addObserver('/iq[@type="error"]', callback)
    directlyProvides(xs, ijabber.IIQResponseTracker)

class IQ(domish.Element):
    timeout = None

    def __init__(self, xmlstream, stanzaType="set"):
        domish.Element.__init__(self, (None, "iq"))
        self.addUniqueId()
        self["type"] = stanzaType
        self._xmlstream = xmlstream

    def send(self, to=None):
        if to is not None:
            self["to"] = to

        if not ijabber.IIQResponseTracker.providedBy(self._xmlstream):
            upgradeWithIQResponseTracker(self._xmlstream)

        d = defer.Deferred()
        self._xmlstream.iqDeferreds[self['id']] = d

        timeout = self.timeout or self._xmlstream.iqDefaultTimeout
        if timeout is not None:
            def onTimeout():
                del self._xmlstream.iqDeferreds[self['id']]
                d.errback(TimeoutError("IQ timed out"))

            call = self._xmlstream._callLater(timeout, onTimeout)

            def cancelTimeout(result):
                if call.active():
                    call.cancel()

                return result

            d.addBoth(cancelTimeout)

        self._xmlstream.send(self)
        return d

def toResponse(stanza, stanzaType=None):
    toAddr = stanza.getAttribute('from')
    fromAddr = stanza.getAttribute('to')
    stanzaID = stanza.getAttribute('id')

    response = domish.Element((None, stanza.name))
    if toAddr:
        response['to'] = toAddr
    if fromAddr:
        response['from'] = fromAddr
    if stanzaID:
        response['id'] = stanzaID
    if stanzaType:
        response['type'] = stanzaType

    return response

class XMPPHandler(object):
    implements(ijabber.IXMPPHandler)

    def __init__(self):
        self.parent = None
        self.xmlstream = None

    def setHandlerParent(self, parent):
        self.parent = parent
        self.parent.addHandler(self)

    def disownHandlerParent(self, parent):
        self.parent.removeHandler(self)
        self.parent = None

    def makeConnection(self, xs):
        self.xmlstream = xs
        self.connectionMade()

    def connectionMade(self):

    def connectionInitialized(self):

    def connectionLost(self, reason):
        self.xmlstream = None

    def send(self, obj):
        self.parent.send(obj)

class XMPPHandlerCollection(object):
    implements(ijabber.IXMPPHandlerCollection)

    def __init__(self):
        self.handlers = []

    def __iter__(self):
        return iter(self.handlers)

    def addHandler(self, handler):
        self.handlers.append(handler)

    def removeHandler(self, handler):
        self.handlers.remove(handler)

class StreamManager(XMPPHandlerCollection):
    logTraffic = False

    def __init__(self, factory):
        XMPPHandlerCollection.__init__(self)
        self.xmlstream = None
        self._packetQueue = []
        self._initialized = False
        factory.addBootstrap(STREAM_CONNECTED_EVENT, self._connected)
        factory.addBootstrap(STREAM_AUTHD_EVENT, self._authd)
        factory.addBootstrap(INIT_FAILED_EVENT, self.initializationFailed)
        factory.addBootstrap(STREAM_END_EVENT, self._disconnected)
        self.factory = factory

    def addHandler(self, handler):
        XMPPHandlerCollection.addHandler(self, handler)
        if self.xmlstream and self._initialized:
            handler.makeConnection(self.xmlstream)
            handler.connectionInitialized()

    def _connected(self, xs):
        def logDataIn(buf):
            log.msg("RECV: %r" % buf)

        def logDataOut(buf):
            log.msg("SEND: %r" % buf)

        if self.logTraffic:
            xs.rawDataInFn = logDataIn
            xs.rawDataOutFn = logDataOut

        self.xmlstream = xs

        for e in self:
            e.makeConnection(xs)


    def _authd(self, xs):
        for p in self._packetQueue:
            xs.send(p)
        self._packetQueue = []
        self._initialized = True
        for e in self:
            e.connectionInitialized()

    def initializationFailed(self, reason):

    def _disconnected(self, _):
        self.xmlstream = None
        self._initialized = False
        for e in self:
            e.connectionLost(None)

    def send(self, obj):
        if self._initialized:
            self.xmlstream.send(obj)
        else:
            self._packetQueue.append(obj)

__all__ = ['Authenticator', 'BaseFeatureInitiatingInitializer',
           'ConnectAuthenticator', 'ConnectionLost', 'FeatureNotAdvertized',
           'INIT_FAILED_EVENT', 'IQ', 'ListenAuthenticator', 'NS_STREAMS',
           'NS_XMPP_TLS', 'Reset', 'STREAM_AUTHD_EVENT',
           'STREAM_CONNECTED_EVENT', 'STREAM_END_EVENT', 'STREAM_ERROR_EVENT',
           'STREAM_START_EVENT', 'StreamManager', 'TLSError', 'TLSFailed',
           'TLSInitiatingInitializer', 'TLSNotSupported', 'TLSRequired',
           'TimeoutError', 'XMPPHandler', 'XMPPHandlerCollection', 'XmlStream',
           'XmlStreamFactory', 'XmlStreamServerFactory', 'hashPassword',
           'toResponse', 'upgradeWithIQResponseTracker']
