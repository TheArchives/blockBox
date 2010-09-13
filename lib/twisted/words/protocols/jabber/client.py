# -*- test-case-name: lib.twisted.words.test.test_jabberclient -*-
#
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.twisted.internet import defer
from lib.twisted.words.xish import domish, xpath, utility
from lib.twisted.words.protocols.jabber import xmlstream, sasl, error
from lib.twisted.words.protocols.jabber.jid import JID
NS_XMPP_STREAMS = 'urn:ietf:params:xml:ns:xmpp-streams'
NS_XMPP_BIND = 'urn:ietf:params:xml:ns:xmpp-bind'
NS_XMPP_SESSION = 'urn:ietf:params:xml:ns:xmpp-session'
NS_IQ_AUTH_FEATURE = 'http://jabber.org/features/iq-auth'
DigestAuthQry = xpath.internQuery("/iq/query/digest")
PlaintextAuthQry = xpath.internQuery("/iq/query/password")

def basicClientFactory(jid, secret):
    a = BasicAuthenticator(jid, secret)
    return xmlstream.XmlStreamFactory(a)

class IQ(domish.Element):
    def __init__(self, xmlstream, type = "set"):
        """
        @type xmlstream: L{xmlstream.XmlStream}
        @param xmlstream: XmlStream to use for transmission of this IQ

        @type type: L{str}
        @param type: IQ type identifier ('get' or 'set')
        """

        domish.Element.__init__(self, ("jabber:client", "iq"))
        self.addUniqueId()
        self["type"] = type
        self._xmlstream = xmlstream
        self.callbacks = utility.CallbackList()

    def addCallback(self, fn, *args, **kwargs):
        self.callbacks.addCallback(True, fn, *args, **kwargs)

    def send(self, to = None):
        if to != None:
            self["to"] = to
        self._xmlstream.addOnetimeObserver("/iq[@id='%s']" % self["id"], \
                                                             self._resultEvent)
        self._xmlstream.send(self)

    def _resultEvent(self, iq):
        self.callbacks.callback(iq)
        self.callbacks = None

class IQAuthInitializer(object):
    INVALID_USER_EVENT    = "//event/client/basicauth/invaliduser"
    AUTH_FAILED_EVENT     = "//event/client/basicauth/authfailed"

    def __init__(self, xs):
        self.xmlstream = xs


    def initialize(self):
        # Send request for auth fields
        iq = xmlstream.IQ(self.xmlstream, "get")
        iq.addElement(("jabber:iq:auth", "query"))
        jid = self.xmlstream.authenticator.jid
        iq.query.addElement("username", content = jid.user)

        d = iq.send()
        d.addCallbacks(self._cbAuthQuery, self._ebAuthQuery)
        return d

    def _cbAuthQuery(self, iq):
        jid = self.xmlstream.authenticator.jid
        password = self.xmlstream.authenticator.password

        # Construct auth request
        reply = xmlstream.IQ(self.xmlstream, "set")
        reply.addElement(("jabber:iq:auth", "query"))
        reply.query.addElement("username", content = jid.user)
        reply.query.addElement("resource", content = jid.resource)

        # Prefer digest over plaintext
        if DigestAuthQry.matches(iq):
            digest = xmlstream.hashPassword(self.xmlstream.sid, unicode(password))
            reply.query.addElement("digest", content = digest)
        else:
            reply.query.addElement("password", content = password)

        d = reply.send()
        d.addCallbacks(self._cbAuth, self._ebAuth)
        return d

    def _ebAuthQuery(self, failure):
        failure.trap(error.StanzaError)
        e = failure.value
        if e.condition == 'not-authorized':
            self.xmlstream.dispatch(e.stanza, self.INVALID_USER_EVENT)
        else:
            self.xmlstream.dispatch(e.stanza, self.AUTH_FAILED_EVENT)

        return failure

    def _cbAuth(self, iq):
        pass

    def _ebAuth(self, failure):
        failure.trap(error.StanzaError)
        self.xmlstream.dispatch(failure.value.stanza, self.AUTH_FAILED_EVENT)
        return failure

class BasicAuthenticator(xmlstream.ConnectAuthenticator):
    namespace = "jabber:client"

    INVALID_USER_EVENT    = IQAuthInitializer.INVALID_USER_EVENT
    AUTH_FAILED_EVENT     = IQAuthInitializer.AUTH_FAILED_EVENT
    REGISTER_FAILED_EVENT = "//event/client/basicauth/registerfailed"

    def __init__(self, jid, password):
        xmlstream.ConnectAuthenticator.__init__(self, jid.host)
        self.jid = jid
        self.password = password

    def associateWithStream(self, xs):
        xs.version = (0, 0)
        xmlstream.ConnectAuthenticator.associateWithStream(self, xs)

        inits = [ (xmlstream.TLSInitiatingInitializer, False),
                  (IQAuthInitializer, True),
                ]

        for initClass, required in inits:
            init = initClass(xs)
            init.required = required
            xs.initializers.append(init)

    def registerAccount(self, username = None, password = None):
        if username:
            self.jid.user = username
        if password:
            self.password = password

        iq = IQ(self.xmlstream, "set")
        iq.addElement(("jabber:iq:register", "query"))
        iq.query.addElement("username", content = self.jid.user)
        iq.query.addElement("password", content = self.password)

        iq.addCallback(self._registerResultEvent)

        iq.send()

    def _registerResultEvent(self, iq):
        if iq["type"] == "result":
            # Registration succeeded -- go ahead and auth
            self.streamStarted()
        else:
            # Registration failed
            self.xmlstream.dispatch(iq, self.REGISTER_FAILED_EVENT)

class CheckVersionInitializer(object):
    def __init__(self, xs):
        self.xmlstream = xs

    def initialize(self):
        if self.xmlstream.version < (1, 0):
            raise error.StreamError('unsupported-version')

class BindInitializer(xmlstream.BaseFeatureInitiatingInitializer):
    feature = (NS_XMPP_BIND, 'bind')

    def start(self):
        iq = xmlstream.IQ(self.xmlstream, 'set')
        bind = iq.addElement((NS_XMPP_BIND, 'bind'))
        resource = self.xmlstream.authenticator.jid.resource
        if resource:
            bind.addElement('resource', content=resource)
        d = iq.send()
        d.addCallback(self.onBind)
        return d

    def onBind(self, iq):
        if iq.bind:
            self.xmlstream.authenticator.jid = JID(unicode(iq.bind.jid))

class SessionInitializer(xmlstream.BaseFeatureInitiatingInitializer):
    feature = (NS_XMPP_SESSION, 'session')

    def start(self):
        iq = xmlstream.IQ(self.xmlstream, 'set')
        session = iq.addElement((NS_XMPP_SESSION, 'session'))
        return iq.send()

def XMPPClientFactory(jid, password):
    a = XMPPAuthenticator(jid, password)
    return xmlstream.XmlStreamFactory(a)

class XMPPAuthenticator(xmlstream.ConnectAuthenticator):
    namespace = 'jabber:client'

    def __init__(self, jid, password):
        xmlstream.ConnectAuthenticator.__init__(self, jid.host)
        self.jid = jid
        self.password = password

    def associateWithStream(self, xs):
        xmlstream.ConnectAuthenticator.associateWithStream(self, xs)

        xs.initializers = [CheckVersionInitializer(xs)]
        inits = [ (xmlstream.TLSInitiatingInitializer, False),
                  (sasl.SASLInitiatingInitializer, True),
                  (BindInitializer, False),
                  (SessionInitializer, False),
                ]

        for initClass, required in inits:
            init = initClass(xs)
            init.required = required
            xs.initializers.append(init)
