# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import re
from lib.twisted.internet import defer
from lib.twisted.words.protocols.jabber import sasl_mechanisms, xmlstream
from lib.twisted.words.xish import domish
try:
    from base64 import b64decode, b64encode
except ImportError:
    import base64

    def b64encode(s):
        return "".join(base64.encodestring(s).split("\n"))

    b64decode = base64.decodestring
NS_XMPP_SASL = 'urn:ietf:params:xml:ns:xmpp-sasl'

def get_mechanisms(xs):
    mechanisms = []
    for element in xs.features[(NS_XMPP_SASL, 'mechanisms')].elements():
        if element.name == 'mechanism':
            mechanisms.append(str(element))

    return mechanisms

class SASLError(Exception):

class SASLNoAcceptableMechanism(SASLError):

class SASLAuthError(SASLError):
    def __init__(self, condition=None):
        self.condition = condition

    def __str__(self):
        return "SASLAuthError with condition %r" % self.condition


class SASLIncorrectEncodingError(SASLError):

base64Pattern = re.compile("^[0-9A-Za-z+/]*[0-9A-Za-z+/=]{,2}$")

def fromBase64(s):
    if base64Pattern.match(s) is None:
        raise SASLIncorrectEncodingError()
    try:
        return b64decode(s)
    except Exception, e:
        raise SASLIncorrectEncodingError(str(e))

class SASLInitiatingInitializer(xmlstream.BaseFeatureInitiatingInitializer):
    feature = (NS_XMPP_SASL, 'mechanisms')
    _deferred = None

    def setMechanism(self):
        jid = self.xmlstream.authenticator.jid
        password = self.xmlstream.authenticator.password

        mechanisms = get_mechanisms(self.xmlstream)
        if jid.user is not None:
            if 'DIGEST-MD5' in mechanisms:
                self.mechanism = sasl_mechanisms.DigestMD5('xmpp', jid.host, None,
                                                           jid.user, password)
            elif 'PLAIN' in mechanisms:
                self.mechanism = sasl_mechanisms.Plain(None, jid.user, password)
            else:
                raise SASLNoAcceptableMechanism()
        else:
            if 'ANONYMOUS' in mechanisms:
                self.mechanism = sasl_mechanisms.Anonymous()
            else:
                raise SASLNoAcceptableMechanism()

    def start(self):
        self.setMechanism()
        self._deferred = defer.Deferred()
        self.xmlstream.addObserver('/challenge', self.onChallenge)
        self.xmlstream.addOnetimeObserver('/success', self.onSuccess)
        self.xmlstream.addOnetimeObserver('/failure', self.onFailure)
        self.sendAuth(self.mechanism.getInitialResponse())
        return self._deferred

    def sendAuth(self, data=None):
        auth = domish.Element((NS_XMPP_SASL, 'auth'))
        auth['mechanism'] = self.mechanism.name
        if data is not None:
            auth.addContent(b64encode(data) or '=')
        self.xmlstream.send(auth)

    def sendResponse(self, data=''):
        response = domish.Element((NS_XMPP_SASL, 'response'))
        if data:
            response.addContent(b64encode(data))
        self.xmlstream.send(response)

    def onChallenge(self, element):
        try:
            challenge = fromBase64(str(element))
        except SASLIncorrectEncodingError:
            self._deferred.errback()
        else:
            self.sendResponse(self.mechanism.getResponse(challenge))

    def onSuccess(self, success):
        self.xmlstream.removeObserver('/challenge', self.onChallenge)
        self.xmlstream.removeObserver('/failure', self.onFailure)
        self.xmlstream.reset()
        self.xmlstream.sendHeader()
        self._deferred.callback(xmlstream.Reset)

    def onFailure(self, failure):
        self.xmlstream.removeObserver('/challenge', self.onChallenge)
        self.xmlstream.removeObserver('/success', self.onSuccess)
        try:
            condition = failure.firstChildElement().name
        except AttributeError:
            condition = None
        self._deferred.errback(SASLAuthError(condition))
