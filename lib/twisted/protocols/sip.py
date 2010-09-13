# -*- test-case-name: lib.twisted.test.test_sip -*-

# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import socket, time, sys, random, warnings
from lib.zope.interface import implements, Interface
from lib.twisted.python import log, util
from lib.twisted.python.deprecate import deprecated
from lib.twisted.python.versions import Version
from lib.twisted.python.hashlib import md5
from lib.twisted.internet import protocol, defer, reactor
from twisted import cred
import lib.twisted.cred.error
from lib.twisted.cred.credentials import UsernameHashedPassword, UsernamePassword
from lib.twisted.protocols import basic
PORT = 5060
shortHeaders = {"call-id": "i",
                "contact": "m",
                "content-encoding": "e",
                "content-length": "l",
                "content-type": "c",
                "from": "f",
                "subject": "s",
                "to": "t",
                "via": "v",
                }
longHeaders = {}
for k, v in shortHeaders.items():
    longHeaders[v] = k
del k, v
statusCodes = {
    100: "Trying",
    180: "Ringing",
    181: "Call Is Being Forwarded",
    182: "Queued",
    183: "Session Progress",
    200: "OK",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Moved Temporarily",
    303: "See Other",
    305: "Use Proxy",
    380: "Alternative Service",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict", # Not in RFC3261
    410: "Gone",
    411: "Length Required", # Not in RFC3261
    413: "Request Entity Too Large",
    414: "Request-URI Too Large",
    415: "Unsupported Media Type",
    416: "Unsupported URI Scheme",
    420: "Bad Extension",
    421: "Extension Required",
    423: "Interval Too Brief",
    480: "Temporarily Unavailable",
    481: "Call/Transaction Does Not Exist",
    482: "Loop Detected",
    483: "Too Many Hops",
    484: "Address Incomplete",
    485: "Ambiguous",
    486: "Busy Here",
    487: "Request Terminated",
    488: "Not Acceptable Here",
    491: "Request Pending",
    493: "Undecipherable",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway", # no donut
    503: "Service Unavailable",
    504: "Server Time-out",
    505: "SIP Version not supported",
    513: "Message Too Large",
    600: "Busy Everywhere",
    603: "Decline",
    604: "Does not exist anywhere",
    606: "Not Acceptable",
}
specialCases = {
    'cseq': 'CSeq',
    'call-id': 'Call-ID',
    'www-authenticate': 'WWW-Authenticate',
}
def dashCapitalize(s):
    return '-'.join([ x.capitalize() for x in s.split('-')])

def unq(s):
    if s[0] == s[-1] == '"':
        return s[1:-1]
    return s

def DigestCalcHA1(
    pszAlg,
    pszUserName,
    pszRealm,
    pszPassword,
    pszNonce,
    pszCNonce,
):
    m = md5()
    m.update(pszUserName)
    m.update(":")
    m.update(pszRealm)
    m.update(":")
    m.update(pszPassword)
    HA1 = m.digest()
    if pszAlg == "md5-sess":
        m = md5()
        m.update(HA1)
        m.update(":")
        m.update(pszNonce)
        m.update(":")
        m.update(pszCNonce)
        HA1 = m.digest()
    return HA1.encode('hex')

DigestCalcHA1 = deprecated(Version("Twisted", 9, 0, 0))(DigestCalcHA1)

def DigestCalcResponse(
    HA1,
    pszNonce,
    pszNonceCount,
    pszCNonce,
    pszQop,
    pszMethod,
    pszDigestUri,
    pszHEntity,
):
    m = md5()
    m.update(pszMethod)
    m.update(":")
    m.update(pszDigestUri)
    if pszQop == "auth-int":
        m.update(":")
        m.update(pszHEntity)
    HA2 = m.digest().encode('hex')

    m = md5()
    m.update(HA1)
    m.update(":")
    m.update(pszNonce)
    m.update(":")
    if pszNonceCount and pszCNonce: # pszQop:
        m.update(pszNonceCount)
        m.update(":")
        m.update(pszCNonce)
        m.update(":")
        m.update(pszQop)
        m.update(":")
    m.update(HA2)
    hash = m.digest().encode('hex')
    return hash

DigestCalcResponse = deprecated(Version("Twisted", 9, 0, 0))(DigestCalcResponse)
_absent = object()

class Via(object):
    def __init__(self, host, port=PORT, transport="UDP", ttl=None,
                 hidden=False, received=None, rport=_absent, branch=None,
                 maddr=None, **kw):
        self.transport = transport
        self.host = host
        self.port = port
        self.ttl = ttl
        self.hidden = hidden
        self.received = received
        if rport is True:
            warnings.warn(
                "rport=True is deprecated since Twisted 9.0.",
                DeprecationWarning,
                stacklevel=2)
            self.rportValue = None
            self.rportRequested = True
        elif rport is None:
            self.rportValue = None
            self.rportRequested = True
        elif rport is _absent:
            self.rportValue = None
            self.rportRequested = False
        else:
            self.rportValue = rport
            self.rportRequested = False
        self.branch = branch
        self.maddr = maddr
        self.otherParams = kw

    def _getrport(self):
        if self.rportRequested == True:
            return True
        elif self.rportValue is not None:
            return self.rportValue
        else:
            return None

    def _setrport(self, newRPort):
        self.rportValue = newRPort
        self.rportRequested = False

    rport = property(_getrport, _setrport)

    def toString(self):
        s = "SIP/2.0/%s %s:%s" % (self.transport, self.host, self.port)
        if self.hidden:
            s += ";hidden"
        for n in "ttl", "branch", "maddr", "received":
            value = getattr(self, n)
            if value is not None:
                s += ";%s=%s" % (n, value)
        if self.rportRequested:
            s += ";rport"
        elif self.rportValue is not None:
            s += ";rport=%s" % (self.rport,)

        etc = self.otherParams.items()
        etc.sort()
        for k, v in etc:
            if v is None:
                s += ";" + k
            else:
                s += ";%s=%s" % (k, v)
        return s

def parseViaHeader(value):
    parts = value.split(";")
    sent, params = parts[0], parts[1:]
    protocolinfo, by = sent.split(" ", 1)
    by = by.strip()
    result = {}
    pname, pversion, transport = protocolinfo.split("/")
    if pname != "SIP" or pversion != "2.0":
        raise ValueError, "wrong protocol or version: %r" % value
    result["transport"] = transport
    if ":" in by:
        host, port = by.split(":")
        result["port"] = int(port)
        result["host"] = host
    else:
        result["host"] = by
    for p in params:
        p = p.strip().split(" ", 1)
        if len(p) == 1:
            p, comment = p[0], ""
        else:
            p, comment = p
        if p == "hidden":
            result["hidden"] = True
            continue
        parts = p.split("=", 1)
        if len(parts) == 1:
            name, value = parts[0], None
        else:
            name, value = parts
            if name in ("rport", "ttl"):
                value = int(value)
        result[name] = value
    return Via(**result)

class URL:
    def __init__(self, host, username=None, password=None, port=None,
                 transport=None, usertype=None, method=None,
                 ttl=None, maddr=None, tag=None, other=None, headers=None):
        self.username = username
        self.host = host
        self.password = password
        self.port = port
        self.transport = transport
        self.usertype = usertype
        self.method = method
        self.tag = tag
        self.ttl = ttl
        self.maddr = maddr
        if other == None:
            self.other = []
        else:
            self.other = other
        if headers == None:
            self.headers = {}
        else:
            self.headers = headers

    def toString(self):
        l = []; w = l.append
        w("sip:")
        if self.username != None:
            w(self.username)
            if self.password != None:
                w(":%s" % self.password)
            w("@")
        w(self.host)
        if self.port != None:
            w(":%d" % self.port)
        if self.usertype != None:
            w(";user=%s" % self.usertype)
        for n in ("transport", "ttl", "maddr", "method", "tag"):
            v = getattr(self, n)
            if v != None:
                w(";%s=%s" % (n, v))
        for v in self.other:
            w(";%s" % v)
        if self.headers:
            w("?")
            w("&".join([("%s=%s" % (specialCases.get(h) or dashCapitalize(h), v)) for (h, v) in self.headers.items()]))
        return "".join(l)

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return '<URL %s:%s@%s:%r/%s>' % (self.username, self.password, self.host, self.port, self.transport)

def parseURL(url, host=None, port=None):
    d = {}
    if not url.startswith("sip:"):
        raise ValueError("unsupported scheme: " + url[:4])
    parts = url[4:].split(";")
    userdomain, params = parts[0], parts[1:]
    udparts = userdomain.split("@", 1)
    if len(udparts) == 2:
        userpass, hostport = udparts
        upparts = userpass.split(":", 1)
        if len(upparts) == 1:
            d["username"] = upparts[0]
        else:
            d["username"] = upparts[0]
            d["password"] = upparts[1]
    else:
        hostport = udparts[0]
    hpparts = hostport.split(":", 1)
    if len(hpparts) == 1:
        d["host"] = hpparts[0]
    else:
        d["host"] = hpparts[0]
        d["port"] = int(hpparts[1])
    if host != None:
        d["host"] = host
    if port != None:
        d["port"] = port
    for p in params:
        if p == params[-1] and "?" in p:
            d["headers"] = h = {}
            p, headers = p.split("?", 1)
            for header in headers.split("&"):
                k, v = header.split("=")
                h[k] = v
        nv = p.split("=", 1)
        if len(nv) == 1:
            d.setdefault("other", []).append(p)
            continue
        name, value = nv
        if name == "user":
            d["usertype"] = value
        elif name in ("transport", "ttl", "maddr", "method", "tag"):
            if name == "ttl":
                value = int(value)
            d[name] = value
        else:
            d.setdefault("other", []).append(p)
    return URL(**d)

def cleanRequestURL(url):
    url.transport = None
    url.maddr = None
    url.ttl = None
    url.headers = {}

def parseAddress(address, host=None, port=None, clean=0):
    address = address.strip()
    if address.startswith("sip:"):
        return "", parseURL(address, host=host, port=port), {}
    params = {}
    name, url = address.split("<", 1)
    name = name.strip()
    if name.startswith('"'):
        name = name[1:]
    if name.endswith('"'):
        name = name[:-1]
    url, paramstring = url.split(">", 1)
    url = parseURL(url, host=host, port=port)
    paramstring = paramstring.strip()
    if paramstring:
        for l in paramstring.split(";"):
            if not l:
                continue
            k, v = l.split("=")
            params[k] = v
    if clean:
        url.ttl = None
        url.headers = {}
        url.transport = None
        url.maddr = None
    return name, url, params

class SIPError(Exception):
    def __init__(self, code, phrase=None):
        if phrase is None:
            phrase = statusCodes[code]
        Exception.__init__(self, "SIP error (%d): %s" % (code, phrase))
        self.code = code
        self.phrase = phrase

class RegistrationError(SIPError):

class Message:
    length = None

    def __init__(self):
        self.headers = util.OrderedDict() # map name to list of values
        self.body = ""
        self.finished = 0

    def addHeader(self, name, value):
        name = name.lower()
        name = longHeaders.get(name, name)
        if name == "content-length":
            self.length = int(value)
        self.headers.setdefault(name,[]).append(value)

    def bodyDataReceived(self, data):
        self.body += data

    def creationFinished(self):
        if (self.length != None) and (self.length != len(self.body)):
            raise ValueError, "wrong body length"
        self.finished = 1

    def toString(self):
        s = "%s\r\n" % self._getHeaderLine()
        for n, vs in self.headers.items():
            for v in vs:
                s += "%s: %s\r\n" % (specialCases.get(n) or dashCapitalize(n), v)
        s += "\r\n"
        s += self.body
        return s

    def _getHeaderLine(self):
        raise NotImplementedError

class Request(Message):
    def __init__(self, method, uri, version="SIP/2.0"):
        Message.__init__(self)
        self.method = method
        if isinstance(uri, URL):
            self.uri = uri
        else:
            self.uri = parseURL(uri)
            cleanRequestURL(self.uri)

    def __repr__(self):
        return "<SIP Request %d:%s %s>" % (id(self), self.method, self.uri.toString())

    def _getHeaderLine(self):
        return "%s %s SIP/2.0" % (self.method, self.uri.toString())

class Response(Message):
    def __init__(self, code, phrase=None, version="SIP/2.0"):
        Message.__init__(self)
        self.code = code
        if phrase == None:
            phrase = statusCodes[code]
        self.phrase = phrase

    def __repr__(self):
        return "<SIP Response %d:%s>" % (id(self), self.code)

    def _getHeaderLine(self):
        return "SIP/2.0 %s %s" % (self.code, self.phrase)

class MessagesParser(basic.LineReceiver):
    version = "SIP/2.0"
    acceptResponses = 1
    acceptRequests = 1
    state = "firstline" # or "headers", "body" or "invalid"
    debug = 0

    def __init__(self, messageReceivedCallback):
        self.messageReceived = messageReceivedCallback
        self.reset()

    def reset(self, remainingData=""):
        self.state = "firstline"
        self.length = None # body length
        self.bodyReceived = 0 # how much of the body we received
        self.message = None
        self.setLineMode(remainingData)

    def invalidMessage(self):
        self.state = "invalid"
        self.setRawMode()

    def dataDone(self):
        self.clearLineBuffer()
        if self.state == "firstline":
            return
        if self.state != "body":
            self.reset()
            return
        if self.length == None:
            self.messageDone()
        elif self.length < self.bodyReceived:
            self.reset()
        else:
            raise RuntimeError, "this should never happen"

    def dataReceived(self, data):
        try:
            basic.LineReceiver.dataReceived(self, data)
        except:
            log.err()
            self.invalidMessage()

    def handleFirstLine(self, line):
        raise NotImplementedError

    def lineLengthExceeded(self, line):
        self.invalidMessage()

    def lineReceived(self, line):
        if self.state == "firstline":
            while line.startswith("\n") or line.startswith("\r"):
                line = line[1:]
            if not line:
                return
            try:
                a, b, c = line.split(" ", 2)
            except ValueError:
                self.invalidMessage()
                return
            if a == "SIP/2.0" and self.acceptResponses:
                try:
                    code = int(b)
                except ValueError:
                    self.invalidMessage()
                    return
                self.message = Response(code, c)
            elif c == "SIP/2.0" and self.acceptRequests:
                self.message = Request(a, b)
            else:
                self.invalidMessage()
                return
            self.state = "headers"
            return
        else:
            assert self.state == "headers"
        if line:
            try:
                name, value = line.split(":", 1)
            except ValueError:
                self.invalidMessage()
                return
            self.message.addHeader(name, value.lstrip())
            if name.lower() == "content-length":
                try:
                    self.length = int(value.lstrip())
                except ValueError:
                    self.invalidMessage()
                    return
        else:
            self.state = "body"
            if self.length == 0:
                self.messageDone()
                return
            self.setRawMode()

    def messageDone(self, remainingData=""):
        assert self.state == "body"
        self.message.creationFinished()
        self.messageReceived(self.message)
        self.reset(remainingData)

    def rawDataReceived(self, data):
        assert self.state in ("body", "invalid")
        if self.state == "invalid":
            return
        if self.length == None:
            self.message.bodyDataReceived(data)
        else:
            dataLen = len(data)
            expectedLen = self.length - self.bodyReceived
            if dataLen > expectedLen:
                self.message.bodyDataReceived(data[:expectedLen])
                self.messageDone(data[expectedLen:])
                return
            else:
                self.bodyReceived += dataLen
                self.message.bodyDataReceived(data)
                if self.bodyReceived == self.length:
                    self.messageDone()

class Base(protocol.DatagramProtocol):
    PORT = PORT
    debug = False

    def __init__(self):
        self.messages = []
        self.parser = MessagesParser(self.addMessage)

    def addMessage(self, msg):
        self.messages.append(msg)

    def datagramReceived(self, data, addr):
        self.parser.dataReceived(data)
        self.parser.dataDone()
        for m in self.messages:
            self._fixupNAT(m, addr)
            if self.debug:
                log.msg("Received %r from %r" % (m.toString(), addr))
            if isinstance(m, Request):
                self.handle_request(m, addr)
            else:
                self.handle_response(m, addr)
        self.messages[:] = []

    def _fixupNAT(self, message, (srcHost, srcPort)):
        senderVia = parseViaHeader(message.headers["via"][0])
        if senderVia.host != srcHost:
            senderVia.received = srcHost
            if senderVia.port != srcPort:
                senderVia.rport = srcPort
            message.headers["via"][0] = senderVia.toString()
        elif senderVia.rport == True:
            senderVia.received = srcHost
            senderVia.rport = srcPort
            message.headers["via"][0] = senderVia.toString()

    def deliverResponse(self, responseMessage):
        destVia = parseViaHeader(responseMessage.headers["via"][0])
        host = destVia.received or destVia.host
        port = destVia.rport or destVia.port or self.PORT
        destAddr = URL(host=host, port=port)
        self.sendMessage(destAddr, responseMessage)

    def responseFromRequest(self, code, request):
        response = Response(code)
        for name in ("via", "to", "from", "call-id", "cseq"):
            response.headers[name] = request.headers.get(name, [])[:]

        return response

    def sendMessage(self, destURL, message):
        if destURL.transport not in ("udp", None):
            raise RuntimeError, "only UDP currently supported"
        if self.debug:
            log.msg("Sending %r to %r" % (message.toString(), destURL))
        self.transport.write(message.toString(), (destURL.host, destURL.port or self.PORT))

    def handle_request(self, message, addr):
        raise NotImplementedError

    def handle_response(self, message, addr):
        raise NotImplementedError

class IContact(Interface):

class Registration:
    def __init__(self, secondsToExpiry, contactURL):
        self.secondsToExpiry = secondsToExpiry
        self.contactURL = contactURL

class IRegistry(Interface):
    def registerAddress(domainURL, logicalURL, physicalURL):

    def unregisterAddress(domainURL, logicalURL, physicalURL):

    def getRegistrationInfo(logicalURL):

class ILocator(Interface):
    def getAddress(logicalURL):

class Proxy(Base):
    PORT = PORT
    locator = None # object implementing ILocator

    def __init__(self, host=None, port=PORT):
        self.host = host or socket.getfqdn()
        self.port = port
        Base.__init__(self)

    def getVia(self):
        return Via(host=self.host, port=self.port)

    def handle_request(self, message, addr):
        f = getattr(self, "handle_%s_request" % message.method, None)
        if f is None:
            f = self.handle_request_default
        try:
            d = f(message, addr)
        except SIPError, e:
            self.deliverResponse(self.responseFromRequest(e.code, message))
        except:
            log.err()
            self.deliverResponse(self.responseFromRequest(500, message))
        else:
            if d is not None:
                d.addErrback(lambda e:
                    self.deliverResponse(self.responseFromRequest(e.code, message))
                )

    def handle_request_default(self, message, (srcHost, srcPort)):
        def _mungContactHeader(uri, message):
            message.headers['contact'][0] = uri.toString()
            return self.sendMessage(uri, message)

        viaHeader = self.getVia()
        if viaHeader.toString() in message.headers["via"]:
            log.msg("Dropping looped message.")
            return

        message.headers["via"].insert(0, viaHeader.toString())
        name, uri, tags = parseAddress(message.headers["to"][0], clean=1)
        d = self.locator.getAddress(uri)
        d.addCallback(self.sendMessage, message)
        d.addErrback(self._cantForwardRequest, message)

    def _cantForwardRequest(self, error, message):
        error.trap(LookupError)
        del message.headers["via"][0] # this'll be us
        self.deliverResponse(self.responseFromRequest(404, message))

    def deliverResponse(self, responseMessage):
        destVia = parseViaHeader(responseMessage.headers["via"][0])
        host = destVia.received or destVia.host
        port = destVia.rport or destVia.port or self.PORT
        destAddr = URL(host=host, port=port)
        self.sendMessage(destAddr, responseMessage)

    def responseFromRequest(self, code, request):
        response = Response(code)
        for name in ("via", "to", "from", "call-id", "cseq"):
            response.headers[name] = request.headers.get(name, [])[:]
        return response

    def handle_response(self, message, addr):
        v = parseViaHeader(message.headers["via"][0])
        if (v.host, v.port) != (self.host, self.port):
            log.msg("Dropping incorrectly addressed message")
            return
        del message.headers["via"][0]
        if not message.headers["via"]:
            self.gotResponse(message, addr)
            return
        self.deliverResponse(message)

    def gotResponse(self, message, addr):
        pass

class IAuthorizer(Interface):
    def getChallenge(peer):

    def decode(response):

class BasicAuthorizer:
    implements(IAuthorizer)

    def __init__(self):
        warnings.warn(
            "lib.twisted.protocols.sip.BasicAuthorizer was deprecated "
            "in Twisted 9.0.0",
            category=DeprecationWarning,
            stacklevel=2)

    def getChallenge(self, peer):
        return None

    def decode(self, response):
        for i in range(3):
            try:
                creds = (response + ('=' * i)).decode('base64')
            except:
                pass
            else:
                break
        else:
            raise SIPError(400)
        p = creds.split(':', 1)
        if len(p) == 2:
            return UsernamePassword(*p)
        raise SIPError(400)

class DigestedCredentials(UsernameHashedPassword):
    def __init__(self, username, fields, challenges):
        warnings.warn(
            "lib.twisted.protocols.sip.DigestedCredentials was deprecated "
            "in Twisted 9.0.0",
            category=DeprecationWarning,
            stacklevel=2)
        self.username = username
        self.fields = fields
        self.challenges = challenges

    def checkPassword(self, password):
        method = 'REGISTER'
        response = self.fields.get('response')
        uri = self.fields.get('uri')
        nonce = self.fields.get('nonce')
        cnonce = self.fields.get('cnonce')
        nc = self.fields.get('nc')
        algo = self.fields.get('algorithm', 'MD5')
        qop = self.fields.get('qop-options', 'auth')
        opaque = self.fields.get('opaque')
        if opaque not in self.challenges:
            return False
        del self.challenges[opaque]
        user, domain = self.username.split('@', 1)
        if uri is None:
            uri = 'sip:' + domain
        expected = DigestCalcResponse(
            DigestCalcHA1(algo, user, domain, password, nonce, cnonce),
            nonce, nc, cnonce, qop, method, uri, None,
        )
        return expected == response

class DigestAuthorizer:
    CHALLENGE_LIFETIME = 15
    implements(IAuthorizer)

    def __init__(self):
        warnings.warn(
            "lib.twisted.protocols.sip.DigestAuthorizer was deprecated "
            "in Twisted 9.0.0",
            category=DeprecationWarning,
            stacklevel=2)

        self.outstanding = {}

    def generateNonce(self):
        c = tuple([random.randrange(sys.maxint) for _ in range(3)])
        c = '%d%d%d' % c
        return c

    def generateOpaque(self):
        return str(random.randrange(sys.maxint))

    def getChallenge(self, peer):
        c = self.generateNonce()
        o = self.generateOpaque()
        self.outstanding[o] = c
        return ','.join((
            'nonce="%s"' % c,
            'opaque="%s"' % o,
            'qop-options="auth"',
            'algorithm="MD5"',
        ))

    def decode(self, response):
        response = ' '.join(response.splitlines())
        parts = response.split(',')
        auth = dict([(k.strip(), unq(v.strip())) for (k, v) in [p.split('=', 1) for p in parts]])
        try:
            username = auth['username']
        except KeyError:
            raise SIPError(401)
        try:
            return DigestedCredentials(username, auth, self.outstanding)
        except:
            raise SIPError(400)

class RegisterProxy(Proxy):
    portal = None
    registry = None # should implement IRegistry
    authorizers = {}

    def __init__(self, *args, **kw):
        Proxy.__init__(self, *args, **kw)
        self.liveChallenges = {}
        if "digest" not in self.authorizers:
            self.authorizers["digest"] = DigestAuthorizer()

    def handle_ACK_request(self, message, (host, port)):
        pass

    def handle_REGISTER_request(self, message, (host, port)):
        if self.portal is None:
            self.register(message, host, port)
        else:
            if not message.headers.has_key("authorization"):
                return self.unauthorized(message, host, port)
            else:
                return self.login(message, host, port)

    def unauthorized(self, message, host, port):
        m = self.responseFromRequest(401, message)
        for (scheme, auth) in self.authorizers.iteritems():
            chal = auth.getChallenge((host, port))
            if chal is None:
                value = '%s realm="%s"' % (scheme.title(), self.host)
            else:
                value = '%s %s,realm="%s"' % (scheme.title(), chal, self.host)
            m.headers.setdefault('www-authenticate', []).append(value)
        self.deliverResponse(m)

    def login(self, message, host, port):
        parts = message.headers['authorization'][0].split(None, 1)
        a = self.authorizers.get(parts[0].lower())
        if a:
            try:
                c = a.decode(parts[1])
            except SIPError:
                raise
            except:
                log.err()
                self.deliverResponse(self.responseFromRequest(500, message))
            else:
                c.username += '@' + self.host
                self.portal.login(c, None, IContact
                    ).addCallback(self._cbLogin, message, host, port
                    ).addErrback(self._ebLogin, message, host, port
                    ).addErrback(log.err
                    )
        else:
            self.deliverResponse(self.responseFromRequest(501, message))

    def _cbLogin(self, (i, a, l), message, host, port):
        self.register(message, host, port)

    def _ebLogin(self, failure, message, host, port):
        failure.trap(cred.error.UnauthorizedLogin)
        self.unauthorized(message, host, port)

    def register(self, message, host, port):
        """Allow all users to register"""
        name, toURL, params = parseAddress(message.headers["to"][0], clean=1)
        contact = None
        if message.headers.has_key("contact"):
            contact = message.headers["contact"][0]

        if message.headers.get("expires", [None])[0] == "0":
            self.unregister(message, toURL, contact)
        else:
            if contact is not None:
                name, contactURL, params = parseAddress(contact, host=host, port=port)
                d = self.registry.registerAddress(message.uri, toURL, contactURL)
            else:
                d = self.registry.getRegistrationInfo(toURL)
            d.addCallbacks(self._cbRegister, self._ebRegister,
                callbackArgs=(message,),
                errbackArgs=(message,)
            )

    def _cbRegister(self, registration, message):
        response = self.responseFromRequest(200, message)
        if registration.contactURL != None:
            response.addHeader("contact", registration.contactURL.toString())
            response.addHeader("expires", "%d" % registration.secondsToExpiry)
        response.addHeader("content-length", "0")
        self.deliverResponse(response)

    def _ebRegister(self, error, message):
        error.trap(RegistrationError, LookupError)

    def unregister(self, message, toURL, contact):
        try:
            expires = int(message.headers["expires"][0])
        except ValueError:
            self.deliverResponse(self.responseFromRequest(400, message))
        else:
            if expires == 0:
                if contact == "*":
                    contactURL = "*"
                else:
                    name, contactURL, params = parseAddress(contact)
                d = self.registry.unregisterAddress(message.uri, toURL, contactURL)
                d.addCallback(self._cbUnregister, message
                    ).addErrback(self._ebUnregister, message
                    )

    def _cbUnregister(self, registration, message):
        msg = self.responseFromRequest(200, message)
        msg.headers.setdefault('contact', []).append(registration.contactURL.toString())
        msg.addHeader("expires", "0")
        self.deliverResponse(msg)

    def _ebUnregister(self, registration, message):
        pass

class InMemoryRegistry:
    implements(IRegistry, ILocator)

    def __init__(self, domain):
        self.domain = domain # the domain we handle registration for
        self.users = {} # map username to (IDelayedCall for expiry, address URI)

    def getAddress(self, userURI):
        if userURI.host != self.domain:
            return defer.fail(LookupError("unknown domain"))
        if self.users.has_key(userURI.username):
            dc, url = self.users[userURI.username]
            return defer.succeed(url)
        else:
            return defer.fail(LookupError("no such user"))

    def getRegistrationInfo(self, userURI):
        if userURI.host != self.domain:
            return defer.fail(LookupError("unknown domain"))
        if self.users.has_key(userURI.username):
            dc, url = self.users[userURI.username]
            return defer.succeed(Registration(int(dc.getTime() - time.time()), url))
        else:
            return defer.fail(LookupError("no such user"))

    def _expireRegistration(self, username):
        try:
            dc, url = self.users[username]
        except KeyError:
            return defer.fail(LookupError("no such user"))
        else:
            dc.cancel()
            del self.users[username]
        return defer.succeed(Registration(0, url))

    def registerAddress(self, domainURL, logicalURL, physicalURL):
        if domainURL.host != self.domain:
            log.msg("Registration for domain we don't handle.")
            return defer.fail(RegistrationError(404))
        if logicalURL.host != self.domain:
            log.msg("Registration for domain we don't handle.")
            return defer.fail(RegistrationError(404))
        if self.users.has_key(logicalURL.username):
            dc, old = self.users[logicalURL.username]
            dc.reset(3600)
        else:
            dc = reactor.callLater(3600, self._expireRegistration, logicalURL.username)
        log.msg("Registered %s at %s" % (logicalURL.toString(), physicalURL.toString()))
        self.users[logicalURL.username] = (dc, physicalURL)
        return defer.succeed(Registration(int(dc.getTime() - time.time()), physicalURL))

    def unregisterAddress(self, domainURL, logicalURL, physicalURL):
        return self._expireRegistration(logicalURL.username)
