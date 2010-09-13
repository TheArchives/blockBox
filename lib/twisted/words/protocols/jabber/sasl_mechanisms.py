# -*- test-case-name: lib.twisted.words.test.test_jabbersaslmechanisms -*-
#
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import binascii, random, time, os
from lib.zope.interface import Interface, Attribute, implements
from lib.twisted.python.hashlib import md5

class ISASLMechanism(Interface):
    name = Attribute("""Common name for the SASL Mechanism.""")
    def getInitialResponse():

    def getResponse(challenge):

class Anonymous(object):
    implements(ISASLMechanism)
    name = 'ANONYMOUS'

    def getInitialResponse(self):
        return None

class Plain(object):
    implements(ISASLMechanism)
    name = 'PLAIN'

    def __init__(self, authzid, authcid, password):
        self.authzid = authzid or ''
        self.authcid = authcid or ''
        self.password = password or ''

    def getInitialResponse(self):
        return "%s\x00%s\x00%s" % (self.authzid.encode('utf-8'),
                                   self.authcid.encode('utf-8'),
                                   self.password.encode('utf-8'))

class DigestMD5(object):
    implements(ISASLMechanism)
    name = 'DIGEST-MD5'

    def __init__(self, serv_type, host, serv_name, username, password):
        self.username = username
        self.password = password
        self.defaultRealm = host
        self.digest_uri = '%s/%s' % (serv_type, host)
        if serv_name is not None:
            self.digest_uri += '/%s' % serv_name

    def getInitialResponse(self):
        return None

    def getResponse(self, challenge):
        directives = self._parse(challenge)
        if 'rspauth' in directives:
            return ''
        try:
            realm = directives['realm']
        except KeyError:
            realm = self.defaultRealm

        return self._gen_response(directives['charset'],
                                  realm,
                                  directives['nonce'])

    def _parse(self, challenge):
        s = challenge
        paramDict = {}
        cur = 0
        remainingParams = True
        while remainingParams:
            middle = s.index("=", cur)
            name = s[cur:middle].lstrip()
            middle += 1
            if s[middle] == '"':
                middle += 1
                end = s.index('"', middle)
                value = s[middle:end]
                cur = s.find(',', end) + 1
                if cur == 0:
                    remainingParams = False
            else:
                end = s.find(',', middle)
                if end == -1:
                    value = s[middle:].rstrip()
                    remainingParams = False
                else:
                    value = s[middle:end].rstrip()
                cur = end + 1
            paramDict[name] = value

        for param in ('qop', 'cipher'):
            if param in paramDict:
                paramDict[param] = paramDict[param].split(',')

        return paramDict

    def _unparse(self, directives):
        directive_list = []
        for name, value in directives.iteritems():
            if name in ('username', 'realm', 'cnonce',
                        'nonce', 'digest-uri', 'authzid', 'cipher'):
                directive = '%s="%s"' % (name, value)
            else:
                directive = '%s=%s' % (name, value)

            directive_list.append(directive)

        return ','.join(directive_list)

    def _gen_response(self, charset, realm, nonce):

        def H(s):
            return md5(s).digest()

        def HEX(n):
            return binascii.b2a_hex(n)

        def KD(k, s):
            return H('%s:%s' % (k, s))
        try:
            username = self.username.encode(charset)
            password = self.password.encode(charset)
        except UnicodeError:
            raise

        nc = '%08x' % 1 # TODO: support subsequent auth.
        cnonce = self._gen_nonce()
        qop = 'auth'

        a1 = "%s:%s:%s" % (H("%s:%s:%s" % (username, realm, password)),
                           nonce,
                           cnonce)
        a2 = "AUTHENTICATE:%s" % self.digest_uri

        response = HEX( KD ( HEX(H(a1)),
                             "%s:%s:%s:%s:%s" % (nonce, nc,
                                                 cnonce, "auth", HEX(H(a2)))))

        directives = {'username': username,
                      'realm' : realm,
                      'nonce' : nonce,
                      'cnonce' : cnonce,
                      'nc' : nc,
                      'qop' : qop,
                      'digest-uri': self.digest_uri,
                      'response': response,
                      'charset': charset}

        return self._unparse(directives)

    def _gen_nonce(self):
        return md5("%s:%s:%s" % (str(random.random()) , str(time.gmtime()),str(os.getpid()))).hexdigest()
