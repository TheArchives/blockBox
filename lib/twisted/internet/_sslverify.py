# -*- test-case-name: twisted.test.test_sslverify -*-
# Copyright (c) 2005 Divmod, Inc.
# Copyright (c) 2008 Twisted Matrix Laboratories.
# See LICENSE for details.
# Copyright (c) 2005-2008 Twisted Matrix Laboratories.

import itertools
from OpenSSL import SSL, crypto
from twisted.python import reflect, util
from twisted.python.hashlib import md5
from twisted.internet.defer import Deferred
from twisted.internet.error import VerifyError, CertificateError

# Private - shared between all OpenSSLCertificateOptions, counts up to provide
# a unique session id for each context
_sessionCounter = itertools.count().next

_x509names = {
    'CN': 'commonName',
    'commonName': 'commonName',
    'O': 'organizationName',
    'organizationName': 'organizationName',
    'OU': 'organizationalUnitName',
    'organizationalUnitName': 'organizationalUnitName',
    'L': 'localityName',
    'localityName': 'localityName',
    'ST': 'stateOrProvinceName',
    'stateOrProvinceName': 'stateOrProvinceName',
    'C': 'countryName',
    'countryName': 'countryName',
    'emailAddress': 'emailAddress'}

class DistinguishedName(dict):
    __slots__ = ()

    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def _copyFrom(self, x509name):
        d = {}
        for name in _x509names:
            value = getattr(x509name, name, None)
            if value is not None:
                setattr(self, name, value)

    def _copyInto(self, x509name):
        for k, v in self.iteritems():
            setattr(x509name, k, v)

    def __repr__(self):
        return '<DN %s>' % (dict.__repr__(self)[1:-1])

    def __getattr__(self, attr):
        try:
            return self[_x509names[attr]]
        except KeyError:
            raise AttributeError(attr)

    def __setattr__(self, attr, value):
        assert type(attr) is str
        if not attr in _x509names:
            raise AttributeError("%s is not a valid OpenSSL X509 name field" % (attr,))
        realAttr = _x509names[attr]
        value = value.encode('ascii')
        assert type(value) is str
        self[realAttr] = value

    def inspect(self):
        l = []
        lablen = 0
        def uniqueValues(mapping):
            return dict.fromkeys(mapping.itervalues()).keys()
        for k in uniqueValues(_x509names):
            label = util.nameToLabel(k)
            lablen = max(len(label), lablen)
            v = getattr(self, k, None)
            if v is not None:
                l.append((label, v))
        lablen += 2
        for n, (label, attr) in enumerate(l):
            l[n] = (label.rjust(lablen)+': '+ attr)
        return '\n'.join(l)

DN = DistinguishedName

class CertBase:
    def __init__(self, original):
        self.original = original

    def _copyName(self, suffix):
        dn = DistinguishedName()
        dn._copyFrom(getattr(self.original, 'get_'+suffix)())
        return dn

    def getSubject(self):
        return self._copyName('subject')

def _handleattrhelper(Class, transport, methodName):
    method = getattr(transport.getHandle(),
                     "get_%s_certificate" % (methodName,), None)
    if method is None:
        raise CertificateError(
            "non-TLS transport %r did not have %s certificate" % (transport, methodName))
    cert = method()
    if cert is None:
        raise CertificateError(
            "TLS transport %r did not have %s certificate" % (transport, methodName))
    return Class(cert)

class Certificate(CertBase):
    def __repr__(self):
        return '<%s Subject=%s Issuer=%s>' % (self.__class__.__name__,
                                              self.getSubject().commonName,
                                              self.getIssuer().commonName)

    def __eq__(self, other):
        if isinstance(other, Certificate):
            return self.dump() == other.dump()
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def load(Class, requestData, format=crypto.FILETYPE_ASN1, args=()):
        return Class(crypto.load_certificate(format, requestData), *args)
    load = classmethod(load)
    _load = load

    def dumpPEM(self):
        return self.dump(crypto.FILETYPE_PEM)

    def loadPEM(Class, data):
        return Class.load(data, crypto.FILETYPE_PEM)
    loadPEM = classmethod(loadPEM)

    def peerFromTransport(Class, transport):
        return _handleattrhelper(Class, transport, 'peer')
    peerFromTransport = classmethod(peerFromTransport)

    def hostFromTransport(Class, transport):
        return _handleattrhelper(Class, transport, 'host')
    hostFromTransport = classmethod(hostFromTransport)

    def getPublicKey(self):
        return PublicKey(self.original.get_pubkey())

    def dump(self, format=crypto.FILETYPE_ASN1):
        return crypto.dump_certificate(format, self.original)

    def serialNumber(self):
        return self.original.get_serial_number()

    def digest(self, method='md5'):
        return self.original.digest(method)

    def _inspect(self):
        return '\n'.join(['Certificate For Subject:',
                          self.getSubject().inspect(),
                          '\nIssuer:',
                          self.getIssuer().inspect(),
                          '\nSerial Number: %d' % self.serialNumber(),
                          'Digest: %s' % self.digest()])

    def inspect(self):
        return '\n'.join((self._inspect(), self.getPublicKey().inspect()))

    def getIssuer(self):
        return self._copyName('issuer')

    def options(self, *authorities):
        raise NotImplementedError('Possible, but doubtful we need this yet')

class CertificateRequest(CertBase):
    def load(Class, requestData, requestFormat=crypto.FILETYPE_ASN1):
        req = crypto.load_certificate_request(requestFormat, requestData)
        dn = DistinguishedName()
        dn._copyFrom(req.get_subject())
        if not req.verify(req.get_pubkey()):
            raise VerifyError("Can't verify that request for %r is self-signed." % (dn,))
        return Class(req)
    load = classmethod(load)

    def dump(self, format=crypto.FILETYPE_ASN1):
        return crypto.dump_certificate_request(format, self.original)

class PrivateCertificate(Certificate):
    def __repr__(self):
        return Certificate.__repr__(self) + ' with ' + repr(self.privateKey)

    def _setPrivateKey(self, privateKey):
        if not privateKey.matches(self.getPublicKey()):
            raise VerifyError(
                "Certificate public and private keys do not match.")
        self.privateKey = privateKey
        return self

    def newCertificate(self, newCertData, format=crypto.FILETYPE_ASN1):
        return self.load(newCertData, self.privateKey, format)

    def load(Class, data, privateKey, format=crypto.FILETYPE_ASN1):
        return Class._load(data, format)._setPrivateKey(privateKey)
    load = classmethod(load)

    def inspect(self):
        return '\n'.join([Certificate._inspect(self),
                          self.privateKey.inspect()])

    def dumpPEM(self):
        return self.dump(crypto.FILETYPE_PEM) + self.privateKey.dump(crypto.FILETYPE_PEM)

    def loadPEM(Class, data):
        return Class.load(data, KeyPair.load(data, crypto.FILETYPE_PEM),
                          crypto.FILETYPE_PEM)
    loadPEM = classmethod(loadPEM)

    def fromCertificateAndKeyPair(Class, certificateInstance, privateKey):
        privcert = Class(certificateInstance.original)
        return privcert._setPrivateKey(privateKey)
    fromCertificateAndKeyPair = classmethod(fromCertificateAndKeyPair)

    def options(self, *authorities):
        options = dict(privateKey=self.privateKey.original,
                       certificate=self.original)
        if authorities:
            options.update(dict(verify=True,
                                requireCertificate=True,
                                caCerts=[auth.original for auth in authorities]))
        return OpenSSLCertificateOptions(**options)

    def certificateRequest(self, format=crypto.FILETYPE_ASN1,
                           digestAlgorithm='md5'):
        return self.privateKey.certificateRequest(
            self.getSubject(),
            format,
            digestAlgorithm)

    def signCertificateRequest(self,
                               requestData,
                               verifyDNCallback,
                               serialNumber,
                               requestFormat=crypto.FILETYPE_ASN1,
                               certificateFormat=crypto.FILETYPE_ASN1):
        issuer = self.getSubject()
        return self.privateKey.signCertificateRequest(
            issuer,
            requestData,
            verifyDNCallback,
            serialNumber,
            requestFormat,
            certificateFormat)

    def signRequestObject(self, certificateRequest, serialNumber,
                          secondsToExpiry=60 * 60 * 24 * 365, # One year
                          digestAlgorithm='md5'):
        return self.privateKey.signRequestObject(self.getSubject(),
                                                 certificateRequest,
                                                 serialNumber,
                                                 secondsToExpiry,
                                                 digestAlgorithm)

class PublicKey:
    def __init__(self, osslpkey):
        self.original = osslpkey
        req1 = crypto.X509Req()
        req1.set_pubkey(osslpkey)
        self._emptyReq = crypto.dump_certificate_request(crypto.FILETYPE_ASN1, req1)

    def matches(self, otherKey):
        return self._emptyReq == otherKey._emptyReq

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.keyHash())

    def keyHash(self):
        return md5(self._emptyReq).hexdigest()

    def inspect(self):
        return 'Public Key with Hash: %s' % (self.keyHash(),)

class KeyPair(PublicKey):
    def load(Class, data, format=crypto.FILETYPE_ASN1):
        return Class(crypto.load_privatekey(format, data))
    load = classmethod(load)

    def dump(self, format=crypto.FILETYPE_ASN1):
        return crypto.dump_privatekey(format, self.original)

    def __getstate__(self):
        return self.dump()

    def __setstate__(self, state):
        self.__init__(crypto.load_privatekey(crypto.FILETYPE_ASN1, state))

    def inspect(self):
        t = self.original.type()
        if t == crypto.TYPE_RSA:
            ts = 'RSA'
        elif t == crypto.TYPE_DSA:
            ts = 'DSA'
        else:
            ts = '(Unknown Type!)'
        L = (self.original.bits(), ts, self.keyHash())
        return '%s-bit %s Key Pair with Hash: %s' % L

    def generate(Class, kind=crypto.TYPE_RSA, size=1024):
        pkey = crypto.PKey()
        pkey.generate_key(kind, size)
        return Class(pkey)

    def newCertificate(self, newCertData, format=crypto.FILETYPE_ASN1):
        return PrivateCertificate.load(newCertData, self, format)
    generate = classmethod(generate)

    def requestObject(self, distinguishedName, digestAlgorithm='md5'):
        req = crypto.X509Req()
        req.set_pubkey(self.original)
        distinguishedName._copyInto(req.get_subject())
        req.sign(self.original, digestAlgorithm)
        return CertificateRequest(req)

    def certificateRequest(self, distinguishedName,
                           format=crypto.FILETYPE_ASN1,
                           digestAlgorithm='md5'):
        return self.requestObject(distinguishedName, digestAlgorithm).dump(format)

    def signCertificateRequest(self,
                               issuerDistinguishedName,
                               requestData,
                               verifyDNCallback,
                               serialNumber,
                               requestFormat=crypto.FILETYPE_ASN1,
                               certificateFormat=crypto.FILETYPE_ASN1,
                               secondsToExpiry=60 * 60 * 24 * 365, # One year
                               digestAlgorithm='md5'):
        hlreq = CertificateRequest.load(requestData, requestFormat)

        dn = hlreq.getSubject()
        vval = verifyDNCallback(dn)

        def verified(value):
            if not value:
                raise VerifyError("DN callback %r rejected request DN %r" % (verifyDNCallback, dn))
            return self.signRequestObject(issuerDistinguishedName, hlreq,
                                          serialNumber, secondsToExpiry, digestAlgorithm).dump(certificateFormat)

        if isinstance(vval, Deferred):
            return vval.addCallback(verified)
        else:
            return verified(vval)

    def signRequestObject(self,
                          issuerDistinguishedName,
                          requestObject,
                          serialNumber,
                          secondsToExpiry=60 * 60 * 24 * 365, # One year
                          digestAlgorithm='md5'):
        req = requestObject.original
        dn = requestObject.getSubject()
        cert = crypto.X509()
        issuerDistinguishedName._copyInto(cert.get_issuer())
        cert.set_subject(req.get_subject())
        cert.set_pubkey(req.get_pubkey())
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(secondsToExpiry)
        cert.set_serial_number(serialNumber)
        cert.sign(self.original, digestAlgorithm)
        return Certificate(cert)

    def selfSignedCert(self, serialNumber, **kw):
        dn = DN(**kw)
        return PrivateCertificate.fromCertificateAndKeyPair(
            self.signRequestObject(dn, self.requestObject(dn), serialNumber),
            self)

class OpenSSLCertificateOptions(object):

    _context = None
    _OP_ALL = getattr(SSL, 'OP_ALL', 0x0000FFFF)
    _OP_NO_TICKET = 0x00004000
    method = SSL.TLSv1_METHOD

    def __init__(self,
                 privateKey=None,
                 certificate=None,
                 method=None,
                 verify=False,
                 caCerts=None,
                 verifyDepth=9,
                 requireCertificate=True,
                 verifyOnce=True,
                 enableSingleUseKeys=True,
                 enableSessions=True,
                 fixBrokenPeers=False,
                 enableSessionTickets=False):
        assert (privateKey is None) == (certificate is None), "Specify neither or both of privateKey and certificate"
        self.privateKey = privateKey
        self.certificate = certificate
        if method is not None:
            self.method = method

        self.verify = verify
        assert ((verify and caCerts) or
                (not verify)), "Specify client CA certificate information if and only if enabling certificate verification"
        self.caCerts = caCerts
        self.verifyDepth = verifyDepth
        self.requireCertificate = requireCertificate
        self.verifyOnce = verifyOnce
        self.enableSingleUseKeys = enableSingleUseKeys
        self.enableSessions = enableSessions
        self.fixBrokenPeers = fixBrokenPeers
        self.enableSessionTickets = enableSessionTickets

    def __getstate__(self):
        d = self.__dict__.copy()
        try:
            del d['_context']
        except KeyError:
            pass
        return d

    def __setstate__(self, state):
        self.__dict__ = state

    def getContext(self):
        """Return a SSL.Context object.
        """
        if self._context is None:
            self._context = self._makeContext()
        return self._context

    def _makeContext(self):
        ctx = SSL.Context(self.method)

        if self.certificate is not None and self.privateKey is not None:
            ctx.use_certificate(self.certificate)
            ctx.use_privatekey(self.privateKey)
            ctx.check_privatekey()

        verifyFlags = SSL.VERIFY_NONE
        if self.verify:
            verifyFlags = SSL.VERIFY_PEER
            if self.requireCertificate:
                verifyFlags |= SSL.VERIFY_FAIL_IF_NO_PEER_CERT
            if self.verifyOnce:
                verifyFlags |= SSL.VERIFY_CLIENT_ONCE
            if self.caCerts:
                store = ctx.get_cert_store()
                for cert in self.caCerts:
                    store.add_cert(cert)

        def _verifyCallback(conn, cert, errno, depth, preverify_ok):
            return preverify_ok
        ctx.set_verify(verifyFlags, _verifyCallback)

        if self.verifyDepth is not None:
            ctx.set_verify_depth(self.verifyDepth)

        if self.enableSingleUseKeys:
            ctx.set_options(SSL.OP_SINGLE_DH_USE)

        if self.fixBrokenPeers:
            ctx.set_options(self._OP_ALL)

        if self.enableSessions:
            sessionName = md5("%s-%d" % (reflect.qual(self.__class__), _sessionCounter())).hexdigest()
            ctx.set_session_id(sessionName)

        if not self.enableSessionTickets:
            ctx.set_options(self._OP_NO_TICKET)

        return ctx
