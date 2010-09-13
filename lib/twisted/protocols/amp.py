# -*- test-case-name: lib.twisted.test.test_amp -*-
# Copyright (c) 2005 Divmod, Inc.
# Copyright (c) 2007-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
__metaclass__ = type
import types, warnings
from cStringIO import StringIO
from struct import pack
import decimal, datetime
from lib.zope.interface import Interface, implements
from lib.twisted.python.compat import set
from lib.twisted.python.util import unsignedID
from lib.twisted.python.reflect import accumulateClassDict
from lib.twisted.python.failure import Failure
from lib.twisted.python import log, filepath
from lib.twisted.internet.main import CONNECTION_LOST
from lib.twisted.internet.error import PeerVerifyError, ConnectionLost
from lib.twisted.internet.error import ConnectionClosed
from lib.twisted.internet.defer import Deferred, maybeDeferred, fail
from lib.twisted.protocols.basic import Int16StringReceiver, StatefulStringProtocol
try:
    from lib.twisted.internet import ssl
except ImportError:
    ssl = None

if ssl and not ssl.supported:
    ssl = None

if ssl is not None:
    from lib.twisted.internet.ssl import CertificateOptions, Certificate, DN, KeyPair
ASK = '_ask'
ANSWER = '_answer'
COMMAND = '_command'
ERROR = '_error'
ERROR_CODE = '_error_code'
ERROR_DESCRIPTION = '_error_description'
UNKNOWN_ERROR_CODE = 'UNKNOWN'
UNHANDLED_ERROR_CODE = 'UNHANDLED'
MAX_KEY_LENGTH = 0xff
MAX_VALUE_LENGTH = 0xffff

class IArgumentType(Interface):
    def fromBox(name, strings, objects, proto):

    def toBox(name, strings, objects, proto):

class IBoxSender(Interface):
    def sendBox(box):

    def unhandledError(failure):

class IBoxReceiver(Interface):
    def startReceivingBoxes(boxSender):

    def ampBoxReceived(box):

    def stopReceivingBoxes(reason):

class IResponderLocator(Interface):

    def locateResponder(self, name):

class AmpError(Exception):

class ProtocolSwitched(Exception):

class OnlyOneTLS(AmpError):

class NoEmptyBoxes(AmpError):

class InvalidSignature(AmpError):

class TooLong(AmpError):
    def __init__(self, isKey, isLocal, value, keyName=None):
        AmpError.__init__(self)
        self.isKey = isKey
        self.isLocal = isLocal
        self.value = value
        self.keyName = keyName

    def __repr__(self):
        hdr = self.isKey and "key" or "value"
        if not self.isKey:
            hdr += ' ' + repr(self.keyName)
        lcl = self.isLocal and "local" or "remote"
        return "%s %s too long: %d" % (lcl, hdr, len(self.value))

class BadLocalReturn(AmpError):
    def __init__(self, message, enclosed):
        AmpError.__init__(self)
        self.message = message
        self.enclosed = enclosed

    def __repr__(self):
        return self.message + " " + self.enclosed.getBriefTraceback()

    __str__ = __repr__

class RemoteAmpError(AmpError):
    def __init__(self, errorCode, description, fatal=False, local=None):
        if local:
            localwhat = ' (local)'
            othertb = local.getBriefTraceback()
        else:
            localwhat = ''
            othertb = ''
        Exception.__init__(self, "Code<%s>%s: %s%s" % (
                errorCode, localwhat,
                description, othertb))
        self.local = local
        self.errorCode = errorCode
        self.description = description
        self.fatal = fatal

class UnknownRemoteError(RemoteAmpError):
    def __init__(self, description):
        errorCode = UNKNOWN_ERROR_CODE
        RemoteAmpError.__init__(self, errorCode, description)

class MalformedAmpBox(AmpError):

class UnhandledCommand(AmpError):

class IncompatibleVersions(AmpError):

PROTOCOL_ERRORS = {UNHANDLED_ERROR_CODE: UnhandledCommand}

class AmpBox(dict):
    __slots__ = []              # be like a regular dictionary, don't magically
                                # acquire a __dict__...

    def copy(self):
        newBox = self.__class__()
        newBox.update(self)
        return newBox

    def serialize(self):
        i = self.items()
        i.sort()
        L = []
        w = L.append
        for k, v in i:
            if len(k) > MAX_KEY_LENGTH:
                raise TooLong(True, True, k, None)
            if len(v) > MAX_VALUE_LENGTH:
                raise TooLong(False, True, v, k)
            for kv in k, v:
                w(pack("!H", len(kv)))
                w(kv)
        w(pack("!H", 0))
        return ''.join(L)

    def _sendTo(self, proto):
        proto.sendBox(self)

    def __repr__(self):
        return 'AmpBox(%s)' % (dict.__repr__(self),)

Box = AmpBox

class QuitBox(AmpBox):
    __slots__ = []

    def __repr__(self):
        return 'QuitBox(**%s)' % (super(QuitBox, self).__repr__(),)

    def _sendTo(self, proto):
        super(QuitBox, self)._sendTo(proto)
        proto.transport.loseConnection()

class _SwitchBox(AmpBox):
    def __init__(self, innerProto, **kw):
        super(_SwitchBox, self).__init__(**kw)
        self.innerProto = innerProto

    def __repr__(self):
        return '_SwitchBox(%r, **%s)' % (self.innerProto,
                                         dict.__repr__(self),)

    def _sendTo(self, proto):
        super(_SwitchBox, self)._sendTo(proto)
        proto._lockForSwitch()
        proto._switchTo(self.innerProto)

class BoxDispatcher:
    implements(IBoxReceiver)
    _failAllReason = None
    _outstandingRequests = None
    _counter = 0L
    boxSender = None

    def __init__(self, locator):
        self._outstandingRequests = {}
        self.locator = locator

    def startReceivingBoxes(self, boxSender):
        self.boxSender = boxSender

    def stopReceivingBoxes(self, reason):
        self.failAllOutgoing(reason)

    def failAllOutgoing(self, reason):
        self._failAllReason = reason
        OR = self._outstandingRequests.items()
        self._outstandingRequests = None # we can never send another request
        for key, value in OR:
            value.errback(reason)

    def _nextTag(self):
        self._counter += 1
        return '%x' % (self._counter,)

    def _sendBoxCommand(self, command, box, requiresAnswer=True):
        if self._failAllReason is not None:
            return fail(self._failAllReason)
        box[COMMAND] = command
        tag = self._nextTag()
        if requiresAnswer:
            box[ASK] = tag
        box._sendTo(self.boxSender)
        if requiresAnswer:
            result = self._outstandingRequests[tag] = Deferred()
        else:
            result = None
        return result

    def callRemoteString(self, command, requiresAnswer=True, **kw):
        box = Box(kw)
        return self._sendBoxCommand(command, box, requiresAnswer)

    def callRemote(self, commandType, *a, **kw):
        try:
            co = commandType(*a, **kw)
        except:
            return fail()
        return co._doCommand(self)

    def unhandledError(self, failure):
        return self.boxSender.unhandledError(failure)

    def _answerReceived(self, box):
        question = self._outstandingRequests.pop(box[ANSWER])
        question.addErrback(self.unhandledError)
        question.callback(box)

    def _errorReceived(self, box):
        question = self._outstandingRequests.pop(box[ERROR])
        question.addErrback(self.unhandledError)
        errorCode = box[ERROR_CODE]
        description = box[ERROR_DESCRIPTION]
        if errorCode in PROTOCOL_ERRORS:
            exc = PROTOCOL_ERRORS[errorCode](errorCode, description)
        else:
            exc = RemoteAmpError(errorCode, description)
        question.errback(Failure(exc))

    def _commandReceived(self, box):

        def formatAnswer(answerBox):
            answerBox[ANSWER] = box[ASK]
            return answerBox
        def formatError(error):
            if error.check(RemoteAmpError):
                code = error.value.errorCode
                desc = error.value.description
                if error.value.fatal:
                    errorBox = QuitBox()
                else:
                    errorBox = AmpBox()
            else:
                errorBox = QuitBox()
                log.err(error) # here is where server-side logging happens
                               # if the error isn't handled
                code = UNKNOWN_ERROR_CODE
                desc = "Unknown Error"
            errorBox[ERROR] = box[ASK]
            errorBox[ERROR_DESCRIPTION] = desc
            errorBox[ERROR_CODE] = code
            return errorBox
        deferred = self.dispatchCommand(box)
        if ASK in box:
            deferred.addCallbacks(formatAnswer, formatError)
            deferred.addCallback(self._safeEmit)
        deferred.addErrback(self.unhandledError)

    def ampBoxReceived(self, box):
        if ANSWER in box:
            self._answerReceived(box)
        elif ERROR in box:
            self._errorReceived(box)
        elif COMMAND in box:
            self._commandReceived(box)
        else:
            raise NoEmptyBoxes(box)

    def _safeEmit(self, aBox):
        try:
            aBox._sendTo(self.boxSender)
        except (ProtocolSwitched, ConnectionLost):
            pass

    def dispatchCommand(self, box):
        cmd = box[COMMAND]
        responder = self.locator.locateResponder(cmd)
        if responder is None:
            return fail(RemoteAmpError(
                    UNHANDLED_ERROR_CODE,
                    "Unhandled Command: %r" % (cmd,),
                    False,
                    local=Failure(UnhandledCommand())))
        return maybeDeferred(responder, box)

class CommandLocator:

    class __metaclass__(type):
        _currentClassCommands = []
        def __new__(cls, name, bases, attrs):
            commands = cls._currentClassCommands[:]
            cls._currentClassCommands[:] = []
            cd = attrs['_commandDispatch'] = {}
            subcls = type.__new__(cls, name, bases, attrs)
            ancestors = list(subcls.__mro__[1:])
            ancestors.reverse()
            for ancestor in ancestors:
                cd.update(getattr(ancestor, '_commandDispatch', {}))
            for commandClass, responderFunc in commands:
                cd[commandClass.commandName] = (commandClass, responderFunc)
            if (bases and (
                    subcls.lookupFunction != CommandLocator.lookupFunction)):
                def locateResponder(self, name):
                    warnings.warn(
                        "Override locateResponder, not lookupFunction.",
                        category=PendingDeprecationWarning,
                        stacklevel=2)
                    return self.lookupFunction(name)
                subcls.locateResponder = locateResponder
            return subcls

    implements(IResponderLocator)

    def _wrapWithSerialization(self, aCallable, command):
        def doit(box):
            kw = command.parseArguments(box, self)
            def checkKnownErrors(error):
                key = error.trap(*command.allErrors)
                code = command.allErrors[key]
                desc = str(error.value)
                return Failure(RemoteAmpError(
                        code, desc, key in command.fatalErrors, local=error))
            def makeResponseFor(objects):
                try:
                    return command.makeResponse(objects, self)
                except:
                    originalFailure = Failure()
                    raise BadLocalReturn(
                        "%r returned %r and %r could not serialize it" % (
                            aCallable,
                            objects,
                            command),
                        originalFailure)
            return maybeDeferred(aCallable, **kw).addCallback(
                makeResponseFor).addErrback(
                checkKnownErrors)
        return doit

    def lookupFunction(self, name):
        if self.__class__.lookupFunction != CommandLocator.lookupFunction:
            return CommandLocator.locateResponder(self, name)
        else:
            warnings.warn("Call locateResponder, not lookupFunction.",
                          category=PendingDeprecationWarning,
                          stacklevel=2)
        return self.locateResponder(name)

    def locateResponder(self, name):
        cd = self._commandDispatch
        if name in cd:
            commandClass, responderFunc = cd[name]
            responderMethod = types.MethodType(
                responderFunc, self, self.__class__)
            return self._wrapWithSerialization(responderMethod, commandClass)

class SimpleStringLocator(object):
    implements(IResponderLocator)
    baseDispatchPrefix = 'amp_'

    def locateResponder(self, name):
        fName = self.baseDispatchPrefix + (name.upper())
        return getattr(self, fName, None)

PYTHON_KEYWORDS = [
    'and', 'del', 'for', 'is', 'raise', 'assert', 'elif', 'from', 'lambda',
    'return', 'break', 'else', 'global', 'not', 'try', 'class', 'except',
    'if', 'or', 'while', 'continue', 'exec', 'import', 'pass', 'yield',
    'def', 'finally', 'in', 'print']

def _wireNameToPythonIdentifier(key):
    lkey = key.replace("-", "_")
    if lkey in PYTHON_KEYWORDS:
        return lkey.title()
    return lkey

class Argument:
    implements(IArgumentType)
    optional = False

    def __init__(self, optional=False):
        self.optional = optional

    def retrieve(self, d, name, proto):
        if self.optional:
            value = d.get(name)
            if value is not None:
                del d[name]
        else:
            value = d.pop(name)
        return value

    def fromBox(self, name, strings, objects, proto):
        st = self.retrieve(strings, name, proto)
        nk = _wireNameToPythonIdentifier(name)
        if self.optional and st is None:
            objects[nk] = None
        else:
            objects[nk] = self.fromStringProto(st, proto)

    def toBox(self, name, strings, objects, proto):
        obj = self.retrieve(objects, _wireNameToPythonIdentifier(name), proto)
        if self.optional and obj is None:
            pass
        else:
            strings[name] = self.toStringProto(obj, proto)

    def fromStringProto(self, inString, proto):
        return self.fromString(inString)

    def toStringProto(self, inObject, proto):
        return self.toString(inObject)

    def fromString(self, inString):

    def toString(self, inObject):

class Integer(Argument):
    fromString = int
    def toString(self, inObject):
        return str(int(inObject))

class String(Argument):
    def toString(self, inObject):
        return inObject

    def fromString(self, inString):
        return inString

class Float(Argument):
    fromString = float
    toString = repr

class Boolean(Argument):
    def fromString(self, inString):
        if inString == 'True':
            return True
        elif inString == 'False':
            return False
        else:
            raise TypeError("Bad boolean value: %r" % (inString,))

    def toString(self, inObject):
        if inObject:
            return 'True'
        else:
            return 'False'

class Unicode(String):
    def toString(self, inObject):
        return String.toString(self, inObject.encode('utf-8'))

    def fromString(self, inString):
        return String.fromString(self, inString).decode('utf-8')

class Path(Unicode):
    def fromString(self, inString):
        return filepath.FilePath(Unicode.fromString(self, inString))

    def toString(self, inObject):
        return Unicode.toString(self, inObject.path)

class ListOf(Argument):
    def __init__(self, elementType, optional=False):
        self.elementType = elementType
        Argument.__init__(self, optional)

    def fromString(self, inString):
        strings = []
        parser = Int16StringReceiver()
        parser.stringReceived = strings.append
        parser.dataReceived(inString)
        return map(self.elementType.fromString, strings)

    def toString(self, inObject):
        strings = []
        for obj in inObject:
            serialized = self.elementType.toString(obj)
            strings.append(pack('!H', len(serialized)))
            strings.append(serialized)
        return ''.join(strings)

class AmpList(Argument):
    def __init__(self, subargs, optional=False):
        self.subargs = subargs
        Argument.__init__(self, optional)

    def fromStringProto(self, inString, proto):
        boxes = parseString(inString)
        values = [_stringsToObjects(box, self.subargs, proto)
                  for box in boxes]
        return values

    def toStringProto(self, inObject, proto):
        return ''.join([_objectsToStrings(
                    objects, self.subargs, Box(), proto
                    ).serialize() for objects in inObject])

class Command:
    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            reverseErrors = attrs['reverseErrors'] = {}
            er = attrs['allErrors'] = {}
            if 'commandName' not in attrs:
                attrs['commandName'] = name
            newtype = type.__new__(cls, name, bases, attrs)
            errors = {}
            fatalErrors = {}
            accumulateClassDict(newtype, 'errors', errors)
            accumulateClassDict(newtype, 'fatalErrors', fatalErrors)
            for v, k in errors.iteritems():
                reverseErrors[k] = v
                er[v] = k
            for v, k in fatalErrors.iteritems():
                reverseErrors[k] = v
                er[v] = k
            return newtype
    arguments = []
    response = []
    extra = []
    errors = {}
    fatalErrors = {}
    commandType = Box
    responseType = Box
    requiresAnswer = True

    def __init__(self, **kw):
        self.structured = kw
        givenArgs = kw.keys()
        forgotten = []
        for name, arg in self.arguments:
            pythonName = _wireNameToPythonIdentifier(name)
            if pythonName not in givenArgs and not arg.optional:
                forgotten.append(pythonName)
        if forgotten:
            raise InvalidSignature("forgot %s for %s" % (
                    ', '.join(forgotten), self.commandName))
        forgotten = []

    def makeResponse(cls, objects, proto):
        try:
            responseType = cls.responseType()
        except:
            return fail()
        return _objectsToStrings(objects, cls.response, responseType, proto)
    makeResponse = classmethod(makeResponse)

    def makeArguments(cls, objects, proto):
        allowedNames = set()
        for (argName, ignored) in cls.arguments:
            allowedNames.add(_wireNameToPythonIdentifier(argName))

        for intendedArg in objects:
            if intendedArg not in allowedNames:
                raise InvalidSignature(
                    "%s is not a valid argument" % (intendedArg,))
        return _objectsToStrings(objects, cls.arguments, cls.commandType(),
                                 proto)
    makeArguments = classmethod(makeArguments)

    def parseResponse(cls, box, protocol):
        return _stringsToObjects(box, cls.response, protocol)
    parseResponse = classmethod(parseResponse)

    def parseArguments(cls, box, protocol):
        return _stringsToObjects(box, cls.arguments, protocol)
    parseArguments = classmethod(parseArguments)

    def responder(cls, methodfunc):
        CommandLocator._currentClassCommands.append((cls, methodfunc))
        return methodfunc
    responder = classmethod(responder)

    def _doCommand(self, proto):

        def _massageError(error):
            error.trap(RemoteAmpError)
            rje = error.value
            errorType = self.reverseErrors.get(rje.errorCode,
                                               UnknownRemoteError)
            return Failure(errorType(rje.description))

        d = proto._sendBoxCommand(self.commandName,
                                  self.makeArguments(self.structured, proto),
                                  self.requiresAnswer)

        if self.requiresAnswer:
            d.addCallback(self.parseResponse, proto)
            d.addErrback(_massageError)

        return d

class _NoCertificate:
    def __init__(self, client):
        self.client = client

    def options(self, *authorities):
        if not self.client:
            sharedDN = DN(CN='TEMPORARY CERTIFICATE')
            key = KeyPair.generate()
            cr = key.certificateRequest(sharedDN)
            sscrd = key.signCertificateRequest(sharedDN, cr, lambda dn: True, 1)
            cert = key.newCertificate(sscrd)
            return cert.options(*authorities)
        options = dict()
        if authorities:
            options.update(dict(verify=True,
                                requireCertificate=True,
                                caCerts=[auth.original for auth in authorities]))
        occo = CertificateOptions(**options)
        return occo

class _TLSBox(AmpBox):
    __slots__ = []

    def __init__(self):
        if ssl is None:
            raise RemoteAmpError("TLS_ERROR", "TLS not available")
        AmpBox.__init__(self)

    def _keyprop(k, default):
        return property(lambda self: self.get(k, default))

    certificate = _keyprop('tls_localCertificate', _NoCertificate(False))
    verify = _keyprop('tls_verifyAuthorities', None)

    def _sendTo(self, proto):
        ab = AmpBox(self)
        for k in ['tls_localCertificate',
                  'tls_verifyAuthorities']:
            ab.pop(k, None)
        ab._sendTo(proto)
        proto._startTLS(self.certificate, self.verify)

class _LocalArgument(String):
    def fromBox(self, name, strings, objects, proto):
        pass

class StartTLS(Command):
    arguments = [("tls_localCertificate", _LocalArgument(optional=True)),
                 ("tls_verifyAuthorities", _LocalArgument(optional=True))]

    response = [("tls_localCertificate", _LocalArgument(optional=True)),
                ("tls_verifyAuthorities", _LocalArgument(optional=True))]

    responseType = _TLSBox

    def __init__(self, **kw):
        if ssl is None:
            raise RuntimeError("TLS not available.")
        self.certificate = kw.pop('tls_localCertificate', _NoCertificate(True))
        self.authorities = kw.pop('tls_verifyAuthorities', None)
        Command.__init__(self, **kw)

    def _doCommand(self, proto):
        d = Command._doCommand(self, proto)
        proto._prepareTLS(self.certificate, self.authorities)
        def actuallystart(response):
            proto._startTLS(self.certificate, self.authorities)
            return response
        d.addCallback(actuallystart)
        return d

class ProtocolSwitchCommand(Command):
    def __init__(self, _protoToSwitchToFactory, **kw):
        self.protoToSwitchToFactory = _protoToSwitchToFactory
        super(ProtocolSwitchCommand, self).__init__(**kw)

    def makeResponse(cls, innerProto, proto):
        return _SwitchBox(innerProto)
    makeResponse = classmethod(makeResponse)

    def _doCommand(self, proto):
        d = super(ProtocolSwitchCommand, self)._doCommand(proto)
        proto._lockForSwitch()
        def switchNow(ign):
            innerProto = self.protoToSwitchToFactory.buildProtocol(
                proto.transport.getPeer())
            proto._switchTo(innerProto, self.protoToSwitchToFactory)
            return ign
        def handle(ign):
            proto._unlockFromSwitch()
            self.protoToSwitchToFactory.clientConnectionFailed(
                None, Failure(CONNECTION_LOST))
            return ign
        return d.addCallbacks(switchNow, handle)

class BinaryBoxProtocol(StatefulStringProtocol, Int16StringReceiver):
    implements(IBoxSender)
    _justStartedTLS = False
    _startingTLSBuffer = None
    _locked = False
    _currentKey = None
    _currentBox = None
    _keyLengthLimitExceeded = False
    hostCertificate = None
    noPeerCertificate = False   # for tests
    innerProtocol = None
    innerProtocolClientFactory = None

    def __init__(self, boxReceiver):
        self.boxReceiver = boxReceiver

    def _switchTo(self, newProto, clientFactory=None):
        newProtoData = self.recvd
        self.recvd = ''
        self.innerProtocol = newProto
        self.innerProtocolClientFactory = clientFactory
        newProto.makeConnection(self.transport)
        if newProtoData:
            newProto.dataReceived(newProtoData)

    def sendBox(self, box):
        if self._locked:
            raise ProtocolSwitched(
                "This connection has switched: no AMP traffic allowed.")
        if self.transport is None:
            raise ConnectionLost()
        if self._startingTLSBuffer is not None:
            self._startingTLSBuffer.append(box)
        else:
            self.transport.write(box.serialize())

    def makeConnection(self, transport):
        self.transport = transport
        self.boxReceiver.startReceivingBoxes(self)
        self.connectionMade()

    def dataReceived(self, data):
        if self._justStartedTLS:
            self._justStartedTLS = False
        if self.innerProtocol is not None:
            self.innerProtocol.dataReceived(data)
            return
        return Int16StringReceiver.dataReceived(self, data)

    def connectionLost(self, reason):
        if self.innerProtocol is not None:
            self.innerProtocol.connectionLost(reason)
            if self.innerProtocolClientFactory is not None:
                self.innerProtocolClientFactory.clientConnectionLost(None, reason)
        if self._keyLengthLimitExceeded:
            failReason = Failure(TooLong(True, False, None, None))
        elif reason.check(ConnectionClosed) and self._justStartedTLS:
            failReason = PeerVerifyError(
                "Peer rejected our certificate for an unknown reason.")
        else:
            failReason = reason
        self.boxReceiver.stopReceivingBoxes(failReason)
    _MAX_KEY_LENGTH = 255
    _MAX_VALUE_LENGTH = 65535
    MAX_LENGTH = _MAX_KEY_LENGTH

    def proto_init(self, string):
        self._currentBox = AmpBox()
        return self.proto_key(string)

    def proto_key(self, string):
        if string:
            self._currentKey = string
            self.MAX_LENGTH = self._MAX_VALUE_LENGTH
            return 'value'
        else:
            self.boxReceiver.ampBoxReceived(self._currentBox)
            self._currentBox = None
            return 'init'

    def proto_value(self, string):
        self._currentBox[self._currentKey] = string
        self._currentKey = None
        self.MAX_LENGTH = self._MAX_KEY_LENGTH
        return 'key'

    def lengthLimitExceeded(self, length):
        self._keyLengthLimitExceeded = True
        self.transport.loseConnection()

    def _lockForSwitch(self):
        self._locked = True

    def _unlockFromSwitch(self):
        if self.innerProtocol is not None:
            raise ProtocolSwitched("Protocol already switched.  Cannot unlock.")
        self._locked = False

    def _prepareTLS(self, certificate, verifyAuthorities):
        self._startingTLSBuffer = []
        if self.hostCertificate is not None:
            raise OnlyOneTLS(
                "Previously authenticated connection between %s and %s "
                "is trying to re-establish as %s" % (
                    self.hostCertificate,
                    self.peerCertificate,
                    (certificate, verifyAuthorities)))

    def _startTLS(self, certificate, verifyAuthorities):
        self.hostCertificate = certificate
        self._justStartedTLS = True
        if verifyAuthorities is None:
            verifyAuthorities = ()
        self.transport.startTLS(certificate.options(*verifyAuthorities))
        stlsb = self._startingTLSBuffer
        if stlsb is not None:
            self._startingTLSBuffer = None
            for box in stlsb:
                self.sendBox(box)

    def _getPeerCertificate(self):
        if self.noPeerCertificate:
            return None
        return Certificate.peerFromTransport(self.transport)
    peerCertificate = property(_getPeerCertificate)

    def unhandledError(self, failure):
        log.msg("Amp server or network failure "
                "unhandled by client application:")
        log.err(failure)
        log.msg(
            "Dropping connection!  "
            "To avoid, add errbacks to ALL remote commands!")
        if self.transport is not None:
            self.transport.loseConnection()

    def _defaultStartTLSResponder(self):
        return {}
    StartTLS.responder(_defaultStartTLSResponder)

class AMP(BinaryBoxProtocol, BoxDispatcher,
          CommandLocator, SimpleStringLocator):
    _ampInitialized = False

    def __init__(self, boxReceiver=None, locator=None):
        self._ampInitialized = True
        if boxReceiver is None:
            boxReceiver = self
        if locator is None:
            locator = self
        BoxDispatcher.__init__(self, locator)
        BinaryBoxProtocol.__init__(self, boxReceiver)

    def locateResponder(self, name):
        firstResponder = CommandLocator.locateResponder(self, name)
        if firstResponder is not None:
            return firstResponder
        secondResponder = SimpleStringLocator.locateResponder(self, name)
        return secondResponder

    def __repr__(self):
        if self.innerProtocol is not None:
            innerRepr = ' inner %r' % (self.innerProtocol,)
        else:
            innerRepr = ''
        return '<%s%s at 0x%x>' % (
            self.__class__.__name__, innerRepr, unsignedID(self))

    def makeConnection(self, transport):
        if not self._ampInitialized:
            AMP.__init__(self)
        self._transportPeer = transport.getPeer()
        self._transportHost = transport.getHost()
        log.msg("%s connection established (HOST:%s PEER:%s)" % (
                self.__class__.__name__,
                self._transportHost,
                self._transportPeer))
        BinaryBoxProtocol.makeConnection(self, transport)

    def connectionLost(self, reason):
        log.msg("%s connection lost (HOST:%s PEER:%s)" %
                (self.__class__.__name__,
                 self._transportHost,
                 self._transportPeer))
        BinaryBoxProtocol.connectionLost(self, reason)
        self.transport = None

class _ParserHelper:
    def __init__(self):
        self.boxes = []

    def getPeer(self):
        return 'string'

    def getHost(self):
        return 'string'

    disconnecting = False

    def startReceivingBoxes(self, sender):

    def ampBoxReceived(self, box):
        self.boxes.append(box)

    def parse(cls, fileObj):
        parserHelper = cls()
        bbp = BinaryBoxProtocol(boxReceiver=parserHelper)
        bbp.makeConnection(parserHelper)
        bbp.dataReceived(fileObj.read())
        return parserHelper.boxes
    parse = classmethod(parse)

    def parseString(cls, data):
        return cls.parse(StringIO(data))
    parseString = classmethod(parseString)

parse = _ParserHelper.parse
parseString = _ParserHelper.parseString

def _stringsToObjects(strings, arglist, proto):
    objects = {}
    myStrings = strings.copy()
    for argname, argparser in arglist:
        argparser.fromBox(argname, myStrings, objects, proto)
    return objects

def _objectsToStrings(objects, arglist, strings, proto):
    myObjects = {}
    for (k, v) in objects.items():
        myObjects[k] = v

    for argname, argparser in arglist:
        argparser.toBox(argname, strings, myObjects, proto)
    return strings

class _FixedOffsetTZInfo(datetime.tzinfo):
    def __init__(self, sign, hours, minutes):
        self.name = '%s%02i:%02i' % (sign, hours, minutes)
        if sign == '-':
            hours = -hours
            minutes = -minutes
        elif sign != '+':
            raise ValueError('invalid sign for timezone %r' % (sign,))
        self.offset = datetime.timedelta(hours=hours, minutes=minutes)

    def utcoffset(self, dt):
        return self.offset

    def dst(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return self.name

utc = _FixedOffsetTZInfo('+', 0, 0)

class Decimal(Argument):
    fromString = decimal.Decimal

    def toString(self, inObject):
        if isinstance(inObject, decimal.Decimal):
            return str(inObject)
        raise ValueError(
            "amp.Decimal can only encode instances of decimal.Decimal")

class DateTime(Argument):
    _positions = [
        slice(0, 4), slice(5, 7), slice(8, 10), # year, month, day
        slice(11, 13), slice(14, 16), slice(17, 19), # hour, minute, second
        slice(20, 26), # microsecond
        # intentionally skip timezone direction, as it is not an integer
        slice(27, 29), slice(30, 32) # timezone hour, timezone minute
        ]

    def fromString(self, s):
        if len(s) != 32:
            raise ValueError('invalid date format %r' % (s,))

        values = [int(s[p]) for p in self._positions]
        sign = s[26]
        timezone = _FixedOffsetTZInfo(sign, *values[7:])
        values[7:] = [timezone]
        return datetime.datetime(*values)

    def toString(self, i):
        offset = i.utcoffset()
        if offset is None:
            raise ValueError(
                'amp.DateTime cannot serialize naive datetime instances.  '
                'You may find amp.utc useful.')

        minutesOffset = (offset.days * 86400 + offset.seconds) // 60
        if minutesOffset > 0:
            sign = '+'
        else:
            sign = '-'

        return '%04i-%02i-%02iT%02i:%02i:%02i.%06i%s%02i:%02i' % (
            i.year,
            i.month,
            i.day,
            i.hour,
            i.minute,
            i.second,
            i.microsecond,
            sign,
            abs(minutesOffset) // 60,
            abs(minutesOffset) % 60)