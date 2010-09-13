# -*- test-case-name: lib.twisted.words.test.test_jabbererror -*-
#
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import copy
from lib.twisted.words.xish import domish
NS_XML = "http://www.w3.org/XML/1998/namespace"
NS_XMPP_STREAMS = "urn:ietf:params:xml:ns:xmpp-streams"
NS_XMPP_STANZAS = "urn:ietf:params:xml:ns:xmpp-stanzas"
STANZA_CONDITIONS = {
    'bad-request':              {'code': '400', 'type': 'modify'},
    'conflict':                 {'code': '409', 'type': 'cancel'},
    'feature-not-implemented':  {'code': '501', 'type': 'cancel'},
    'forbidden':                {'code': '403', 'type': 'auth'},
    'gone':                     {'code': '302', 'type': 'modify'},
    'internal-server-error':    {'code': '500', 'type': 'wait'},
    'item-not-found':           {'code': '404', 'type': 'cancel'},
    'jid-malformed':            {'code': '400', 'type': 'modify'},
    'not-acceptable':           {'code': '406', 'type': 'modify'},
    'not-allowed':              {'code': '405', 'type': 'cancel'},
    'not-authorized':           {'code': '401', 'type': 'auth'},
    'payment-required':         {'code': '402', 'type': 'auth'},
    'recipient-unavailable':    {'code': '404', 'type': 'wait'},
    'redirect':                 {'code': '302', 'type': 'modify'},
    'registration-required':    {'code': '407', 'type': 'auth'},
    'remote-server-not-found':  {'code': '404', 'type': 'cancel'},
    'remote-server-timeout':    {'code': '504', 'type': 'wait'},
    'resource-constraint':      {'code': '500', 'type': 'wait'},
    'service-unavailable':      {'code': '503', 'type': 'cancel'},
    'subscription-required':    {'code': '407', 'type': 'auth'},
    'undefined-condition':      {'code': '500', 'type': None},
    'unexpected-request':       {'code': '400', 'type': 'wait'},
}
CODES_TO_CONDITIONS = {
    '302': ('gone', 'modify'),
    '400': ('bad-request', 'modify'),
    '401': ('not-authorized', 'auth'),
    '402': ('payment-required', 'auth'),
    '403': ('forbidden', 'auth'),
    '404': ('item-not-found', 'cancel'),
    '405': ('not-allowed', 'cancel'),
    '406': ('not-acceptable', 'modify'),
    '407': ('registration-required', 'auth'),
    '408': ('remote-server-timeout', 'wait'),
    '409': ('conflict', 'cancel'),
    '500': ('internal-server-error', 'wait'),
    '501': ('feature-not-implemented', 'cancel'),
    '502': ('service-unavailable', 'wait'),
    '503': ('service-unavailable', 'cancel'),
    '504': ('remote-server-timeout', 'wait'),
    '510': ('service-unavailable', 'cancel'),
}
class BaseError(Exception):
    namespace = None
    def __init__(self, condition, text=None, textLang=None, appCondition=None):
        Exception.__init__(self)
        self.condition = condition
        self.text = text
        self.textLang = textLang
        self.appCondition = appCondition

    def __str__(self):
        message = "%s with condition %r" % (self.__class__.__name__,
                                            self.condition)

        if self.text:
            message += ': ' + self.text

        return message

    def getElement(self):
        error = domish.Element((None, 'error'))
        error.addElement((self.namespace, self.condition))
        if self.text:
            text = error.addElement((self.namespace, 'text'),
                                    content=self.text)
            if self.textLang:
                text[(NS_XML, 'lang')] = self.textLang
        if self.appCondition:
            error.addChild(self.appCondition)
        return error

class StreamError(BaseError):
    namespace = NS_XMPP_STREAMS
    def getElement(self):
        from lib.twisted.words.protocols.jabber.xmlstream import NS_STREAMS
        error = BaseError.getElement(self)
        error.uri = NS_STREAMS
        return error

class StanzaError(BaseError):
    namespace = NS_XMPP_STANZAS

    def __init__(self, condition, type=None, text=None, textLang=None,
                       appCondition=None):
        BaseError.__init__(self, condition, text, textLang, appCondition)

        if type is None:
            try:
                type = STANZA_CONDITIONS[condition]['type']
            except KeyError:
                pass
        self.type = type

        try:
            self.code = STANZA_CONDITIONS[condition]['code']
        except KeyError:
            self.code = None

        self.children = []
        self.iq = None

    def getElement(self):
        error = BaseError.getElement(self)
        error['type'] = self.type
        if self.code:
            error['code'] = self.code
        return error

    def toResponse(self, stanza):
        from lib.twisted.words.protocols.jabber.xmlstream import toResponse
        response = toResponse(stanza, stanzaType='error')
        response.children = copy.copy(stanza.children)
        response.addChild(self.getElement())
        return response

def _getText(element):
    for child in element.children:
        if isinstance(child, basestring):
            return unicode(child)

    return None

def _parseError(error, errorNamespace):
    condition = None
    text = None
    textLang = None
    appCondition = None

    for element in error.elements():
        if element.uri == errorNamespace:
            if element.name == 'text':
                text = _getText(element)
                textLang = element.getAttribute((NS_XML, 'lang'))
            else:
                condition = element.name
        else:
            appCondition = element

    return {
        'condition': condition,
        'text': text,
        'textLang': textLang,
        'appCondition': appCondition,
    }

def exceptionFromStreamError(element):
    error = _parseError(element, NS_XMPP_STREAMS)

    exception = StreamError(error['condition'],
                            error['text'],
                            error['textLang'],
                            error['appCondition'])

    return exception

def exceptionFromStanza(stanza):
    children = []
    condition = text = textLang = appCondition = type = code = None

    for element in stanza.elements():
        if element.name == 'error' and element.uri == stanza.uri:
            code = element.getAttribute('code')
            type = element.getAttribute('type')
            error = _parseError(element, NS_XMPP_STANZAS)
            condition = error['condition']
            text = error['text']
            textLang = error['textLang']
            appCondition = error['appCondition']

            if not condition and code:
               condition, type = CODES_TO_CONDITIONS[code]
               text = _getText(stanza.error)
        else:
            children.append(element)

    if condition is None:
        return StanzaError(None)

    exception = StanzaError(condition, type, text, textLang, appCondition)
    exception.children = children
    exception.stanza = stanza
    return exception
