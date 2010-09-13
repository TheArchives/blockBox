# -*- test-case-name: lib.twisted.words.test -*-
# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.
import types, operator, os
from random import randint
from urllib import quote, unquote
from lib.twisted.python import failure, log
from lib.twisted.python.hashlib import md5
from lib.twisted.internet import reactor
from lib.twisted.internet.defer import Deferred
from lib.twisted.internet.protocol import ClientFactory
try:
    from lib.twisted.internet.ssl import ClientContextFactory
except ImportError:
    ClientContextFactory = None
from lib.twisted.protocols.basic import LineReceiver
from lib.twisted.web.http import HTTPClient
MSN_PROTOCOL_VERSION = "MSNP8 CVR0"       # protocol version
MSN_PORT             = 1863               # default dispatch server port
MSN_MAX_MESSAGE      = 1664               # max message length
MSN_CHALLENGE_STR    = "Q1P7W2E4J9R8U3S5" # used for server challenges
MSN_CVR_STR          = "0x0409 win 4.10 i386 MSNMSGR 5.0.0544 MSMSGS" # :(
LOGIN_SUCCESS  = 1
LOGIN_FAILURE  = 2
LOGIN_REDIRECT = 3
FORWARD_LIST = 1
ALLOW_LIST   = 2
BLOCK_LIST   = 4
REVERSE_LIST = 8
HOME_PHONE   = "PHH"
WORK_PHONE   = "PHW"
MOBILE_PHONE = "PHM"
HAS_PAGER    = "MOB"
STATUS_ONLINE  = 'NLN'
STATUS_OFFLINE = 'FLN'
STATUS_HIDDEN  = 'HDN'
STATUS_IDLE    = 'IDL'
STATUS_AWAY    = 'AWY'
STATUS_BUSY    = 'BSY'
STATUS_BRB     = 'BRB'
STATUS_PHONE   = 'PHN'
STATUS_LUNCH   = 'LUN'
CR = "\r"
LF = "\n"

def checkParamLen(num, expected, cmd, error=None):
    if error == None:
        error = "Invalid Number of Parameters for %s" % cmd
    if num != expected:
        raise MSNProtocolError, error

def _parseHeader(h, v):

    if h in ('passporturls','authentication-info','www-authenticate'):
        v = v.replace('Passport1.4','').lstrip()
        fields = {}
        for fieldPair in v.split(','):
            try:
                field,value = fieldPair.split('=',1)
                fields[field.lower()] = value
            except ValueError:
                fields[field.lower()] = ''
        return fields
    else:
        return v

def _parsePrimitiveHost(host):
    h,p = host.replace('https://','').split('/',1)
    p = '/' + p
    return h,p

def _login(userHandle, passwd, nexusServer, cached=0, authData=''):
    """
    This function is used internally and should not ever be called
    directly.
    """
    cb = Deferred()
    def _cb(server, auth):
        loginFac = ClientFactory()
        loginFac.protocol = lambda : PassportLogin(cb, userHandle, passwd, server, auth)
        reactor.connectSSL(_parsePrimitiveHost(server)[0], 443, loginFac, ClientContextFactory())

    if cached:
        _cb(nexusServer, authData)
    else:
        fac = ClientFactory()
        d = Deferred()
        d.addCallbacks(_cb, callbackArgs=(authData,))
        d.addErrback(lambda f: cb.errback(f))
        fac.protocol = lambda : PassportNexus(d, nexusServer)
        reactor.connectSSL(_parsePrimitiveHost(nexusServer)[0], 443, fac, ClientContextFactory())
    return cb

class PassportNexus(HTTPClient):
    def __init__(self, deferred, host):
        self.deferred = deferred
        self.host, self.path = _parsePrimitiveHost(host)

    def connectionMade(self):
        HTTPClient.connectionMade(self)
        self.sendCommand('GET', self.path)
        self.sendHeader('Host', self.host)
        self.endHeaders()
        self.headers = {}

    def handleHeader(self, header, value):
        h = header.lower()
        self.headers[h] = _parseHeader(h, value)

    def handleEndHeaders(self):
        if self.connected:
            self.transport.loseConnection()
        if not self.headers.has_key('passporturls') or not self.headers['passporturls'].has_key('dalogin'):
            self.deferred.errback(failure.Failure(failure.DefaultException("Invalid Nexus Reply")))
        self.deferred.callback('https://' + self.headers['passporturls']['dalogin'])

    def handleResponse(self, r):
        pass

class PassportLogin(HTTPClient):
    _finished = 0

    def __init__(self, deferred, userHandle, passwd, host, authData):
        self.deferred = deferred
        self.userHandle = userHandle
        self.passwd = passwd
        self.authData = authData
        self.host, self.path = _parsePrimitiveHost(host)

    def connectionMade(self):
        self.sendCommand('GET', self.path)
        self.sendHeader('Authorization', 'Passport1.4 OrgVerb=GET,OrgURL=http://messenger.msn.com,' +
                                         'sign-in=%s,pwd=%s,%s' % (quote(self.userHandle), self.passwd,self.authData))
        self.sendHeader('Host', self.host)
        self.endHeaders()
        self.headers = {}

    def handleHeader(self, header, value):
        h = header.lower()
        self.headers[h] = _parseHeader(h, value)

    def handleEndHeaders(self):
        if self._finished:
            return
        self._finished = 1 # I think we need this because of HTTPClient
        if self.connected:
            self.transport.loseConnection()
        authHeader = 'authentication-info'
        _interHeader = 'www-authenticate'
        if self.headers.has_key(_interHeader):
            authHeader = _interHeader
        try:
            info = self.headers[authHeader]
            status = info['da-status']
            handler = getattr(self, 'login_%s' % (status,), None)
            if handler:
                handler(info)
            else:
                raise Exception()
        except Exception, e:
            self.deferred.errback(failure.Failure(e))

    def handleResponse(self, r):
        pass

    def login_success(self, info):
        ticket = info['from-pp']
        ticket = ticket[1:len(ticket)-1]
        self.deferred.callback((LOGIN_SUCCESS, ticket))

    def login_failed(self, info):
        self.deferred.callback((LOGIN_FAILURE, unquote(info['cbtxt'])))

    def login_redir(self, info):
        self.deferred.callback((LOGIN_REDIRECT, self.headers['location'], self.authData))


class MSNProtocolError(Exception):
    pass

class MSNCommandFailed(Exception):
    def __init__(self, errorCode):
        self.errorCode = errorCode

    def __str__(self):
        return ("Command failed: %s (error code %d)"
                % (errorCodes[self.errorCode], self.errorCode))

class MSNMessage:
    MESSAGE_ACK      = 'A'
    MESSAGE_NACK     = 'N'
    MESSAGE_ACK_NONE = 'U'

    ack = MESSAGE_ACK

    def __init__(self, length=0, userHandle="", screenName="", message=""):
        self.userHandle = userHandle
        self.screenName = screenName
        self.message = message
        self.headers = {'MIME-Version' : '1.0', 'Content-Type' : 'text/plain'}
        self.length = length
        self.readPos = 0

    def _calcMessageLen(self):
        return reduce(operator.add, [len(x[0]) + len(x[1]) + 4  for x in self.headers.items()]) + len(self.message) + 2

    def setHeader(self, header, value):
        self.headers[header] = value

    def getHeader(self, header):
        return self.headers[header]

    def hasHeader(self, header):
        return self.headers.has_key(header)

    def getMessage(self):
        return self.message

    def setMessage(self, message):
        self.message = message

class MSNContact:
    def __init__(self, userHandle="", screenName="", lists=0, groups=[], status=None):
        self.userHandle = userHandle
        self.screenName = screenName
        self.lists = lists
        self.groups = [] # if applicable
        self.status = status # current status
        self.homePhone   = None
        self.workPhone   = None
        self.mobilePhone = None
        self.hasPager    = None

    def setPhone(self, phoneType, value):
        t = phoneType.upper()
        if t == HOME_PHONE:
            self.homePhone = value
        elif t == WORK_PHONE:
            self.workPhone = value
        elif t == MOBILE_PHONE:
            self.mobilePhone = value
        elif t == HAS_PAGER:
            self.hasPager = value
        else:
            raise ValueError, "Invalid Phone Type"

    def addToList(self, listType):
        self.lists |= listType

    def removeFromList(self, listType):
        self.lists ^= listType

class MSNContactList:
    def __init__(self):
        self.contacts = {}
        self.version = 0
        self.groups = {}
        self.autoAdd = 0
        self.privacy = 0

    def _getContactsFromList(self, listType):
        return dict([(uH,obj) for uH,obj in self.contacts.items() if obj.lists & listType])

    def addContact(self, contact):
        self.contacts[contact.userHandle] = contact

    def remContact(self, userHandle):
        try:
            del self.contacts[userHandle]
        except KeyError:
            pass

    def getContact(self, userHandle):
        try:
            return self.contacts[userHandle]
        except KeyError:
            return None

    def getBlockedContacts(self):
        return self._getContactsFromList(BLOCK_LIST)

    def getAuthorizedContacts(self):
        return self._getContactsFromList(ALLOW_LIST)

    def getReverseContacts(self):
        return self._getContactsFromList(REVERSE_LIST)

    def getContacts(self):
        return self._getContactsFromList(FORWARD_LIST)

    def setGroup(self, id, name):
        self.groups[id] = name

    def remGroup(self, id):
        try:
            del self.groups[id]
        except KeyError:
            pass
        for c in self.contacts:
            if id in c.groups:
                c.groups.remove(id)


class MSNEventBase(LineReceiver):
    def __init__(self):
        self.ids = {} # mapping of ids to Deferreds
        self.currentID = 0
        self.connected = 0
        self.setLineMode()
        self.currentMessage = None

    def connectionLost(self, reason):
        self.ids = {}
        self.connected = 0

    def connectionMade(self):
        self.connected = 1

    def _fireCallback(self, id, *args):
        if self.ids.has_key(id):
            self.ids[id][0].callback(args)
            del self.ids[id]
            return 1
        return 0

    def _nextTransactionID(self):
        self.currentID += 1
        if self.currentID > 1000:
            self.currentID = 1
        return self.currentID

    def _createIDMapping(self, data=None):
        id = self._nextTransactionID()
        d = Deferred()
        self.ids[id] = (d, data)
        return (id, d)

    def checkMessage(self, message):
        raise NotImplementedError

    def lineReceived(self, line):
        if self.currentMessage:
            self.currentMessage.readPos += len(line+CR+LF)
            if line == "":
                self.setRawMode()
                if self.currentMessage.readPos == self.currentMessage.length:
                    self.rawDataReceived("") # :(
                return
            try:
                header, value = line.split(':')
            except ValueError:
                raise MSNProtocolError, "Invalid Message Header"
            self.currentMessage.setHeader(header, unquote(value).lstrip())
            return
        try:
            cmd, params = line.split(' ', 1)
        except ValueError:
            raise MSNProtocolError, "Invalid Message, %s" % repr(line)

        if len(cmd) != 3:
            raise MSNProtocolError, "Invalid Command, %s" % repr(cmd)
        if cmd.isdigit():
            errorCode = int(cmd)
            id = int(params.split()[0])
            if id in self.ids:
                self.ids[id][0].errback(MSNCommandFailed(errorCode))
                del self.ids[id]
                return
            else:       # we received an error which doesn't map to a sent command
                self.gotError(errorCode)
                return

        handler = getattr(self, "handle_%s" % cmd.upper(), None)
        if handler:
            try:
                handler(params.split())
            except MSNProtocolError, why:
                self.gotBadLine(line, why)
        else:
            self.handle_UNKNOWN(cmd, params.split())

    def rawDataReceived(self, data):
        extra = ""
        self.currentMessage.readPos += len(data)
        diff = self.currentMessage.readPos - self.currentMessage.length
        if diff > 0:
            self.currentMessage.message += data[:-diff]
            extra = data[-diff:]
        elif diff == 0:
            self.currentMessage.message += data
        else:
            self.currentMessage += data
            return
        del self.currentMessage.readPos
        m = self.currentMessage
        self.currentMessage = None
        self.setLineMode(extra)
        if not self.checkMessage(m):
            return
        self.gotMessage(m)

    def handle_MSG(self, params):
        checkParamLen(len(params), 3, 'MSG')
        try:
            messageLen = int(params[2])
        except ValueError:
            raise MSNProtocolError, "Invalid Parameter for MSG length argument"
        self.currentMessage = MSNMessage(length=messageLen, userHandle=params[0], screenName=unquote(params[1]))

    def handle_UNKNOWN(self, cmd, params):
        log.msg("Received unknown command (%s), params: %s" % (cmd, params))

    def gotMessage(self, message):
        raise NotImplementedError

    def gotBadLine(self, line, why):
        log.msg('Error in line: %s (%s)' % (line, why))

    def gotError(self, errorCode):
        log.msg('Error %s' % (errorCodes[errorCode]))

class DispatchClient(MSNEventBase):
    userHandle = ""

    def connectionMade(self):
        MSNEventBase.connectionMade(self)
        self.sendLine('VER %s %s' % (self._nextTransactionID(), MSN_PROTOCOL_VERSION))

    def handle_VER(self, params):
        id = self._nextTransactionID()
        self.sendLine("CVR %s %s %s" % (id, MSN_CVR_STR, self.userHandle))

    def handle_CVR(self, params):
        self.sendLine("USR %s TWN I %s" % (self._nextTransactionID(), self.userHandle))

    def handle_XFR(self, params):
        if len(params) < 4:
            raise MSNProtocolError, "Invalid number of parameters for XFR"
        id, refType, addr = params[:3]
        try:
            host, port = addr.split(':')
        except ValueError:
            host = addr
            port = MSN_PORT
        if refType == "NS":
            self.gotNotificationReferral(host, int(port))

    def gotNotificationReferral(self, host, port):
        pass

class NotificationClient(MSNEventBase):

    factory = None

    def __init__(self, currentID=0):
        MSNEventBase.__init__(self)
        self.currentID = currentID
        self._state = ['DISCONNECTED', {}]

    def _setState(self, state):
        self._state[0] = state

    def _getState(self):
        return self._state[0]

    def _getStateData(self, key):
        return self._state[1][key]

    def _setStateData(self, key, value):
        self._state[1][key] = value

    def _remStateData(self, *args):
        for key in args:
            del self._state[1][key]

    def connectionMade(self):
        MSNEventBase.connectionMade(self)
        self._setState('CONNECTED')
        self.sendLine("VER %s %s" % (self._nextTransactionID(), MSN_PROTOCOL_VERSION))

    def connectionLost(self, reason):
        self._setState('DISCONNECTED')
        self._state[1] = {}
        MSNEventBase.connectionLost(self, reason)

    def checkMessage(self, message):
        cTypes = [s.lstrip() for s in message.getHeader('Content-Type').split(';')]
        if 'text/x-msmsgsprofile' in cTypes:
            self.gotProfile(message)
            return 0
        return 1

    def handle_VER(self, params):
        id = self._nextTransactionID()
        self.sendLine("CVR %s %s %s" % (id, MSN_CVR_STR, self.factory.userHandle))

    def handle_CVR(self, params):
        self.sendLine("USR %s TWN I %s" % (self._nextTransactionID(), self.factory.userHandle))

    def handle_USR(self, params):
        if len(params) != 4 and len(params) != 6:
            raise MSNProtocolError, "Invalid Number of Parameters for USR"

        mechanism = params[1]
        if mechanism == "OK":
            self.loggedIn(params[2], unquote(params[3]), int(params[4]))
        elif params[2].upper() == "S":
            f = self.factory
            d = _login(f.userHandle, f.password, f.passportServer, authData=params[3])
            d.addCallback(self._passportLogin)
            d.addErrback(self._passportError)

    def _passportLogin(self, result):
        if result[0] == LOGIN_REDIRECT:
            d = _login(self.factory.userHandle, self.factory.password,
                       result[1], cached=1, authData=result[2])
            d.addCallback(self._passportLogin)
            d.addErrback(self._passportError)
        elif result[0] == LOGIN_SUCCESS:
            self.sendLine("USR %s TWN S %s" % (self._nextTransactionID(), result[1]))
        elif result[0] == LOGIN_FAILURE:
            self.loginFailure(result[1])

    def _passportError(self, failure):
        self.loginFailure("Exception while authenticating: %s" % failure)

    def handle_CHG(self, params):
        checkParamLen(len(params), 3, 'CHG')
        id = int(params[0])
        if not self._fireCallback(id, params[1]):
            self.statusChanged(params[1])

    def handle_ILN(self, params):
        checkParamLen(len(params), 5, 'ILN')
        self.gotContactStatus(params[1], params[2], unquote(params[3]))

    def handle_CHL(self, params):
        checkParamLen(len(params), 2, 'CHL')
        self.sendLine("QRY %s msmsgs@msnmsgr.com 32" % self._nextTransactionID())
        self.transport.write(md5(params[1] + MSN_CHALLENGE_STR).hexdigest())

    def handle_QRY(self, params):
        pass

    def handle_NLN(self, params):
        checkParamLen(len(params), 4, 'NLN')
        self.contactStatusChanged(params[0], params[1], unquote(params[2]))

    def handle_FLN(self, params):
        checkParamLen(len(params), 1, 'FLN')
        self.contactOffline(params[0])

    def handle_LST(self, params):
        if self._getState() != 'SYNC':
            return
        contact = MSNContact(userHandle=params[0], screenName=unquote(params[1]),
                             lists=int(params[2]))
        if contact.lists & FORWARD_LIST:
            contact.groups.extend(map(int, params[3].split(',')))
        self._getStateData('list').addContact(contact)
        self._setStateData('last_contact', contact)
        sofar = self._getStateData('lst_sofar') + 1
        if sofar == self._getStateData('lst_reply'):
            self._setState('SESSION')
            contacts = self._getStateData('list')
            phone = self._getStateData('phone')
            id = self._getStateData('synid')
            self._remStateData('lst_reply', 'lsg_reply', 'lst_sofar', 'phone', 'synid', 'list')
            self._fireCallback(id, contacts, phone)
        else:
            self._setStateData('lst_sofar',sofar)

    def handle_BLP(self, params):
        if self._getState() == 'SYNC':
            self._getStateData('list').privacy = listCodeToID[params[0].lower()]
        else:
            id = int(params[0])
            self._fireCallback(id, int(params[1]), listCodeToID[params[2].lower()])

    def handle_GTC(self, params):
        if self._getState() == 'SYNC':
            if params[0].lower() == "a":
                self._getStateData('list').autoAdd = 0
            elif params[0].lower() == "n":
                self._getStateData('list').autoAdd = 1
            else:
                raise MSNProtocolError, "Invalid Paramater for GTC" # debug
        else:
            id = int(params[0])
            if params[1].lower() == "a":
                self._fireCallback(id, 0)
            elif params[1].lower() == "n":
                self._fireCallback(id, 1)
            else:
                raise MSNProtocolError, "Invalid Paramater for GTC" # debug

    def handle_SYN(self, params):
        id = int(params[0])
        if len(params) == 2:
            self._setState('SESSION')
            self._fireCallback(id, None, None)
        else:
            contacts = MSNContactList()
            contacts.version = int(params[1])
            self._setStateData('list', contacts)
            self._setStateData('lst_reply', int(params[2]))
            self._setStateData('lsg_reply', int(params[3]))
            self._setStateData('lst_sofar', 0)
            self._setStateData('phone', [])

    def handle_LSG(self, params):
        if self._getState() == 'SYNC':
            self._getStateData('list').groups[int(params[0])] = unquote(params[1])

    def handle_PRP(self, params):
        if self._getState() == 'SYNC':
            self._getStateData('phone').append((params[0], unquote(params[1])))
        else:
            self._fireCallback(int(params[0]), int(params[1]), unquote(params[3]))

    def handle_BPR(self, params):
        numParams = len(params)
        if numParams == 2: # part of a syn
            self._getStateData('last_contact').setPhone(params[0], unquote(params[1]))
        elif numParams == 4:
            self.gotPhoneNumber(int(params[0]), params[1], params[2], unquote(params[3]))

    def handle_ADG(self, params):
        checkParamLen(len(params), 5, 'ADG')
        id = int(params[0])
        if not self._fireCallback(id, int(params[1]), unquote(params[2]), int(params[3])):
            raise MSNProtocolError, "ADG response does not match up to a request" # debug

    def handle_RMG(self, params):
        checkParamLen(len(params), 3, 'RMG')
        id = int(params[0])
        if not self._fireCallback(id, int(params[1]), int(params[2])):
            raise MSNProtocolError, "RMG response does not match up to a request" # debug

    def handle_REG(self, params):
        checkParamLen(len(params), 5, 'REG')
        id = int(params[0])
        if not self._fireCallback(id, int(params[1]), int(params[2]), unquote(params[3])):
            raise MSNProtocolError, "REG response does not match up to a request" # debug

    def handle_ADD(self, params):
        numParams = len(params)
        if numParams < 5 or params[1].upper() not in ('AL','BL','RL','FL'):
            raise MSNProtocolError, "Invalid Paramaters for ADD" # debug
        id = int(params[0])
        listType = params[1].lower()
        listVer = int(params[2])
        userHandle = params[3]
        groupID = None
        if numParams == 6: # they sent a group id
            if params[1].upper() != "FL":
                raise MSNProtocolError, "Only forward list can contain groups" # debug
            groupID = int(params[5])
        if not self._fireCallback(id, listCodeToID[listType], userHandle, listVer, groupID):
            self.userAddedMe(userHandle, unquote(params[4]), listVer)

    def handle_REM(self, params):
        numParams = len(params)
        if numParams < 4 or params[1].upper() not in ('AL','BL','FL','RL'):
            raise MSNProtocolError, "Invalid Paramaters for REM" # debug
        id = int(params[0])
        listType = params[1].lower()
        listVer = int(params[2])
        userHandle = params[3]
        groupID = None
        if numParams == 5:
            if params[1] != "FL":
                raise MSNProtocolError, "Only forward list can contain groups" # debug
            groupID = int(params[4])
        if not self._fireCallback(id, listCodeToID[listType], userHandle, listVer, groupID):
            if listType.upper() == "RL":
                self.userRemovedMe(userHandle, listVer)

    def handle_REA(self, params):
        checkParamLen(len(params), 4, 'REA')
        id = int(params[0])
        self._fireCallback(id, int(params[1]), unquote(params[3]))

    def handle_XFR(self, params):
        checkParamLen(len(params), 5, 'XFR')
        id = int(params[0])
        # check to see if they sent a host/port pair
        try:
            host, port = params[2].split(':')
        except ValueError:
            host = params[2]
            port = MSN_PORT

        if not self._fireCallback(id, host, int(port), params[4]):
            raise MSNProtocolError, "Got XFR (referral) that I didn't ask for .. should this happen?" # debug

    def handle_RNG(self, params):
        checkParamLen(len(params), 6, 'RNG')
        # check for host:port pair
        try:
            host, port = params[1].split(":")
            port = int(port)
        except ValueError:
            host = params[1]
            port = MSN_PORT
        self.gotSwitchboardInvitation(int(params[0]), host, port, params[3], params[4],
                                      unquote(params[5]))

    def handle_OUT(self, params):
        checkParamLen(len(params), 1, 'OUT')
        if params[0] == "OTH":
            self.multipleLogin()
        elif params[0] == "SSD":
            self.serverGoingDown()
        else:
            raise MSNProtocolError, "Invalid Parameters received for OUT" # debug

    def loggedIn(self, userHandle, screenName, verified):
        self.factory.screenName = screenName
        if not self.factory.contacts:
            listVersion = 0
        else:
            listVersion = self.factory.contacts.version
        self.syncList(listVersion).addCallback(self.listSynchronized)

    def loginFailure(self, message):
        pass

    def gotProfile(self, message):
        pass

    def listSynchronized(self, *args):
        pass

    def statusChanged(self, statusCode):
        self.factory.status = statusCode

    def gotContactStatus(self, statusCode, userHandle, screenName):
        self.factory.contacts.getContact(userHandle).status = statusCode

    def contactStatusChanged(self, statusCode, userHandle, screenName):
        self.factory.contacts.getContact(userHandle).status = statusCode

    def contactOffline(self, userHandle):
        self.factory.contacts.getContact(userHandle).status = STATUS_OFFLINE

    def gotPhoneNumber(self, listVersion, userHandle, phoneType, number):
        self.factory.contacts.version = listVersion
        self.factory.contacts.getContact(userHandle).setPhone(phoneType, number)

    def userAddedMe(self, userHandle, screenName, listVersion):
        self.factory.contacts.version = listVersion
        c = self.factory.contacts.getContact(userHandle)
        if not c:
            c = MSNContact(userHandle=userHandle, screenName=screenName)
            self.factory.contacts.addContact(c)
        c.addToList(REVERSE_LIST)

    def userRemovedMe(self, userHandle, listVersion):
        self.factory.contacts.version = listVersion
        c = self.factory.contacts.getContact(userHandle)
        c.removeFromList(REVERSE_LIST)
        if c.lists == 0:
            self.factory.contacts.remContact(c.userHandle)

    def gotSwitchboardInvitation(self, sessionID, host, port,
                                 key, userHandle, screenName):
        pass

    def multipleLogin(self):
        pass

    def serverGoingDown(self):
        pass

    def changeStatus(self, status):
        id, d = self._createIDMapping()
        self.sendLine("CHG %s %s" % (id, status))
        def _cb(r):
            self.factory.status = r[0]
            return r
        return d.addCallback(_cb)

    def setPrivacyMode(self, privLevel):
        id, d = self._createIDMapping()
        if privLevel:
            self.sendLine("BLP %s AL" % id)
        else:
            self.sendLine("BLP %s BL" % id)
        return d

    def syncList(self, version):
        self._setState('SYNC')
        id, d = self._createIDMapping(data=str(version))
        self._setStateData('synid',id)
        self.sendLine("SYN %s %s" % (id, version))
        def _cb(r):
            self.changeStatus(STATUS_ONLINE)
            if r[0] is not None:
                self.factory.contacts = r[0]
            return r
        return d.addCallback(_cb)

    def setPhoneDetails(self, phoneType, value):
        id, d = self._createIDMapping()
        self.sendLine("PRP %s %s %s" % (id, phoneType, quote(value)))
        return d

    def addListGroup(self, name):
        id, d = self._createIDMapping()
        self.sendLine("ADG %s %s 0" % (id, quote(name)))
        def _cb(r):
            self.factory.contacts.version = r[0]
            self.factory.contacts.setGroup(r[1], r[2])
            return r
        return d.addCallback(_cb)

    def remListGroup(self, groupID):
        id, d = self._createIDMapping()
        self.sendLine("RMG %s %s" % (id, groupID))
        def _cb(r):
            self.factory.contacts.version = r[0]
            self.factory.contacts.remGroup(r[1])
            return r
        return d.addCallback(_cb)

    def renameListGroup(self, groupID, newName):
        id, d = self._createIDMapping()
        self.sendLine("REG %s %s %s 0" % (id, groupID, quote(newName)))
        def _cb(r):
            self.factory.contacts.version = r[0]
            self.factory.contacts.setGroup(r[1], r[2])
            return r
        return d.addCallback(_cb)

    def addContact(self, listType, userHandle, groupID=0):
        id, d = self._createIDMapping()
        listType = listIDToCode[listType].upper()
        if listType == "FL":
            self.sendLine("ADD %s FL %s %s %s" % (id, userHandle, userHandle, groupID))
        else:
            self.sendLine("ADD %s %s %s %s" % (id, listType, userHandle, userHandle))

        def _cb(r):
            self.factory.contacts.version = r[2]
            c = self.factory.contacts.getContact(r[1])
            if not c:
                c = MSNContact(userHandle=r[1])
            if r[3]:
                c.groups.append(r[3])
            c.addToList(r[0])
            return r
        return d.addCallback(_cb)

    def remContact(self, listType, userHandle, groupID=0):
        id, d = self._createIDMapping()
        listType = listIDToCode[listType].upper()
        if listType == "FL":
            self.sendLine("REM %s FL %s %s" % (id, userHandle, groupID))
        else:
            self.sendLine("REM %s %s %s" % (id, listType, userHandle))

        def _cb(r):
            l = self.factory.contacts
            l.version = r[2]
            c = l.getContact(r[1])
            group = r[3]
            shouldRemove = 1
            if group: # they may not have been removed from the list
                c.groups.remove(group)
                if c.groups:
                    shouldRemove = 0
            if shouldRemove:
                c.removeFromList(r[0])
                if c.lists == 0:
                    l.remContact(c.userHandle)
            return r
        return d.addCallback(_cb)

    def changeScreenName(self, newName):
        id, d = self._createIDMapping()
        self.sendLine("REA %s %s %s" % (id, self.factory.userHandle, quote(newName)))
        def _cb(r):
            self.factory.contacts.version = r[0]
            self.factory.screenName = r[1]
            return r
        return d.addCallback(_cb)

    def requestSwitchboardServer(self):
        id, d = self._createIDMapping()
        self.sendLine("XFR %s SB" % id)
        return d

    def logOut(self):
        self.sendLine("OUT")

class NotificationFactory(ClientFactory):
    contacts = None
    userHandle = ''
    screenName = ''
    password = ''
    passportServer = 'https://nexus.passport.com/rdr/pprdr.asp'
    status = 'FLN'
    protocol = NotificationClient

class SwitchboardClient(MSNEventBase):
    key = 0
    userHandle = ""
    sessionID = ""
    reply = 0
    _iCookie = 0

    def __init__(self):
        MSNEventBase.__init__(self)
        self.pendingUsers = {}
        self.cookies = {'iCookies' : {}, 'external' : {}} # will maybe be moved to a factory in the future

    def connectionMade(self):
        MSNEventBase.connectionMade(self)
        print 'sending initial stuff'
        self._sendInit()

    def connectionLost(self, reason):
        self.cookies['iCookies'] = {}
        self.cookies['external'] = {}
        MSNEventBase.connectionLost(self, reason)

    def _sendInit(self):
        id = self._nextTransactionID()
        if not self.reply:
            self.sendLine("USR %s %s %s" % (id, self.userHandle, self.key))
        else:
            self.sendLine("ANS %s %s %s %s" % (id, self.userHandle, self.key, self.sessionID))

    def _newInvitationCookie(self):
        self._iCookie += 1
        if self._iCookie > 1000:
            self._iCookie = 1
        return self._iCookie

    def _checkTyping(self, message, cTypes):
        if 'text/x-msmsgscontrol' in cTypes and message.hasHeader('TypingUser'):
            self.userTyping(message)
            return 1

    def _checkFileInvitation(self, message, info):
        """ helper method for checkMessage """
        guid = info.get('Application-GUID', '').lower()
        name = info.get('Application-Name', '').lower()

        if name != "file transfer" and guid != classNameToGUID["file transfer"]:
            return 0
        try:
            cookie = int(info['Invitation-Cookie'])
            fileName = info['Application-File']
            fileSize = int(info['Application-FileSize'])
        except KeyError:
            log.msg('Received munged file transfer request ... ignoring.')
            return 0
        self.gotSendRequest(fileName, fileSize, cookie, message)
        return 1

    def _checkFileResponse(self, message, info):
        try:
            cmd = info['Invitation-Command'].upper()
            cookie = int(info['Invitation-Cookie'])
        except KeyError:
            return 0
        accept = (cmd == 'ACCEPT') and 1 or 0
        requested = self.cookies['iCookies'].get(cookie)
        if not requested:
            return 1
        requested[0].callback((accept, cookie, info))
        del self.cookies['iCookies'][cookie]
        return 1

    def _checkFileInfo(self, message, info):
        try:
            ip = info['IP-Address']
            iCookie = int(info['Invitation-Cookie'])
            aCookie = int(info['AuthCookie'])
            cmd = info['Invitation-Command'].upper()
            port = int(info['Port'])
        except KeyError:
            return 0
        accept = (cmd == 'ACCEPT') and 1 or 0
        requested = self.cookies['external'].get(iCookie)
        if not requested:
            return 1 # we didn't ask for this
        requested[0].callback((accept, ip, port, aCookie, info))
        del self.cookies['external'][iCookie]
        return 1

    def checkMessage(self, message):
        cTypes = [s.lstrip() for s in message.getHeader('Content-Type').split(';')]
        if self._checkTyping(message, cTypes):
            return 0
        if 'text/x-msmsgsinvite' in cTypes:
            info = {}
            for line in message.message.split('\r\n'):
                try:
                    key, val = line.split(':')
                    info[key] = val.lstrip()
                except ValueError:
                    continue
            if self._checkFileInvitation(message, info) or self._checkFileInfo(message, info) or self._checkFileResponse(message, info):
                return 0
        elif 'text/x-clientcaps' in cTypes:
            return 0
        return 1

    def handle_USR(self, params):
        checkParamLen(len(params), 4, 'USR')
        if params[1] == "OK":
            self.loggedIn()

    def handle_CAL(self, params):
        checkParamLen(len(params), 3, 'CAL')
        id = int(params[0])
        if params[1].upper() == "RINGING":
            self._fireCallback(id, int(params[2])) # session ID as parameter

    def handle_JOI(self, params):
        checkParamLen(len(params), 2, 'JOI')
        self.userJoined(params[0], unquote(params[1]))

    def handle_IRO(self, params):
        checkParamLen(len(params), 5, 'IRO')
        self.pendingUsers[params[3]] = unquote(params[4])
        if params[1] == params[2]:
            self.gotChattingUsers(self.pendingUsers)
            self.pendingUsers = {}

    def handle_ANS(self, params):
        checkParamLen(len(params), 2, 'ANS')
        if params[1] == "OK":
            self.loggedIn()

    def handle_ACK(self, params):
        checkParamLen(len(params), 1, 'ACK')
        self._fireCallback(int(params[0]), None)

    def handle_NAK(self, params):
        checkParamLen(len(params), 1, 'NAK')
        self._fireCallback(int(params[0]), None)

    def handle_BYE(self, params):
        #checkParamLen(len(params), 1, 'BYE') # i've seen more than 1 param passed to this
        self.userLeft(params[0])

    def loggedIn(self):
        pass

    def gotChattingUsers(self, users):
        pass

    def userJoined(self, userHandle, screenName):
        pass

    def userLeft(self, userHandle):
        pass

    def gotMessage(self, message):
        pass

    def userTyping(self, message):
        pass

    def gotSendRequest(self, fileName, fileSize, iCookie, message):
        pass

    def inviteUser(self, userHandle):
        id, d = self._createIDMapping()
        self.sendLine("CAL %s %s" % (id, userHandle))
        return d

    def sendMessage(self, message):
        if message.ack not in ('A','N'):
            id, d = self._nextTransactionID(), None
        else:
            id, d = self._createIDMapping()
        if message.length == 0:
            message.length = message._calcMessageLen()
        self.sendLine("MSG %s %s %s" % (id, message.ack, message.length))
        self.sendLine('MIME-Version: %s' % message.getHeader('MIME-Version'))
        self.sendLine('Content-Type: %s' % message.getHeader('Content-Type'))
        for header in [h for h in message.headers.items() if h[0].lower() not in ('mime-version','content-type')]:
            self.sendLine("%s: %s" % (header[0], header[1]))
        self.transport.write(CR+LF)
        self.transport.write(message.message)
        return d

    def sendTypingNotification(self):
        m = MSNMessage()
        m.ack = m.MESSAGE_ACK_NONE
        m.setHeader('Content-Type', 'text/x-msmsgscontrol')
        m.setHeader('TypingUser', self.userHandle)
        m.message = "\r\n"
        self.sendMessage(m)

    def sendFileInvitation(self, fileName, fileSize):
        cookie = self._newInvitationCookie()
        d = Deferred()
        m = MSNMessage()
        m.setHeader('Content-Type', 'text/x-msmsgsinvite; charset=UTF-8')
        m.message += 'Application-Name: File Transfer\r\n'
        m.message += 'Application-GUID: %s\r\n' % (classNameToGUID["file transfer"],)
        m.message += 'Invitation-Command: INVITE\r\n'
        m.message += 'Invitation-Cookie: %s\r\n' % str(cookie)
        m.message += 'Application-File: %s\r\n' % fileName
        m.message += 'Application-FileSize: %s\r\n\r\n' % str(fileSize)
        m.ack = m.MESSAGE_ACK_NONE
        self.sendMessage(m)
        self.cookies['iCookies'][cookie] = (d, m)
        return d

    def fileInvitationReply(self, iCookie, accept=1):
        d = Deferred()
        m = MSNMessage()
        m.setHeader('Content-Type', 'text/x-msmsgsinvite; charset=UTF-8')
        m.message += 'Invitation-Command: %s\r\n' % (accept and 'ACCEPT' or 'CANCEL')
        m.message += 'Invitation-Cookie: %s\r\n' % str(iCookie)
        if not accept:
            m.message += 'Cancel-Code: REJECT\r\n'
        m.message += 'Launch-Application: FALSE\r\n'
        m.message += 'Request-Data: IP-Address:\r\n'
        m.message += '\r\n'
        m.ack = m.MESSAGE_ACK_NONE
        self.sendMessage(m)
        self.cookies['external'][iCookie] = (d, m)
        return d

    def sendTransferInfo(self, accept, iCookie, authCookie, ip, port):
        m = MSNMessage()
        m.setHeader('Content-Type', 'text/x-msmsgsinvite; charset=UTF-8')
        m.message += 'Invitation-Command: %s\r\n' % (accept and 'ACCEPT' or 'CANCEL')
        m.message += 'Invitation-Cookie: %s\r\n' % iCookie
        m.message += 'IP-Address: %s\r\n' % ip
        m.message += 'Port: %s\r\n' % port
        m.message += 'AuthCookie: %s\r\n' % authCookie
        m.message += '\r\n'
        m.ack = m.MESSAGE_NACK
        self.sendMessage(m)

class FileReceive(LineReceiver):
    def __init__(self, auth, myUserHandle, file, directory="", overwrite=0):
        self.auth = auth
        self.myUserHandle = myUserHandle
        self.fileSize = 0
        self.connected = 0
        self.completed = 0
        self.directory = directory
        self.bytesReceived = 0
        self.overwrite = overwrite
        self.state = 'CONNECTING'
        self.segmentLength = 0
        self.buffer = ''

        if isinstance(file, types.StringType):
            path = os.path.join(directory, file)
            if os.path.exists(path) and not self.overwrite:
                log.msg('File already exists...')
                raise IOError, "File Exists" # is this all we should do here?
            self.file = open(os.path.join(directory, file), 'wb')
        else:
            self.file = file

    def connectionMade(self):
        self.connected = 1
        self.state = 'INHEADER'
        self.sendLine('VER MSNFTP')

    def connectionLost(self, reason):
        self.connected = 0
        self.file.close()

    def parseHeader(self, header):
        if ord(header[0]) != 0: # they requested that we close the connection
            self.transport.loseConnection()
            return
        try:
            extra, factor = header[1:]
        except ValueError:
            # munged header, ending transfer
            self.transport.loseConnection()
            raise
        extra  = ord(extra)
        factor = ord(factor)
        return factor * 256 + extra

    def lineReceived(self, line):
        temp = line.split()
        if len(temp) == 1:
            params = []
        else:
            params = temp[1:]
        cmd = temp[0]
        handler = getattr(self, "handle_%s" % cmd.upper(), None)
        if handler:
            handler(params) # try/except
        else:
            self.handle_UNKNOWN(cmd, params)

    def rawDataReceived(self, data):
        bufferLen = len(self.buffer)
        if self.state == 'INHEADER':
            delim = 3-bufferLen
            self.buffer += data[:delim]
            if len(self.buffer) == 3:
                self.segmentLength = self.parseHeader(self.buffer)
                if not self.segmentLength:
                    return # hrm
                self.buffer = ""
                self.state = 'INSEGMENT'
            extra = data[delim:]
            if len(extra) > 0:
                self.rawDataReceived(extra)
            return

        elif self.state == 'INSEGMENT':
            dataSeg = data[:(self.segmentLength-bufferLen)]
            self.buffer += dataSeg
            self.bytesReceived += len(dataSeg)
            if len(self.buffer) == self.segmentLength:
                self.gotSegment(self.buffer)
                self.buffer = ""
                if self.bytesReceived == self.fileSize:
                    self.completed = 1
                    self.buffer = ""
                    self.file.close()
                    self.sendLine("BYE 16777989")
                    return
                self.state = 'INHEADER'
                extra = data[(self.segmentLength-bufferLen):]
                if len(extra) > 0:
                    self.rawDataReceived(extra)
                return

    def handle_VER(self, params):
        checkParamLen(len(params), 1, 'VER')
        if params[0].upper() == "MSNFTP":
            self.sendLine("USR %s %s" % (self.myUserHandle, self.auth))
        else:
            log.msg('they sent the wrong version, time to quit this transfer')
            self.transport.loseConnection()

    def handle_FIL(self, params):
        checkParamLen(len(params), 1, 'FIL')
        try:
            self.fileSize = int(params[0])
        except ValueError: # they sent the wrong file size - probably want to log this
            self.transport.loseConnection()
            return
        self.setRawMode()
        self.sendLine("TFR")

    def handle_UNKNOWN(self, cmd, params):
        log.msg('received unknown command (%s), params: %s' % (cmd, params))

    def gotSegment(self, data):
        self.file.write(data)

class FileSend(LineReceiver):
    def __init__(self, file):
        if isinstance(file, types.StringType):
            self.file = open(file, 'rb')
        else:
            self.file = file

        self.fileSize = 0
        self.bytesSent = 0
        self.completed = 0
        self.connected = 0
        self.targetUser = None
        self.segmentSize = 2045
        self.auth = randint(0, 2**30)
        self._pendingSend = None # :(

    def connectionMade(self):
        self.connected = 1

    def connectionLost(self, reason):
        if self._pendingSend.active():
            self._pendingSend.cancel()
            self._pendingSend = None
        if self.bytesSent == self.fileSize:
            self.completed = 1
        self.connected = 0
        self.file.close()

    def lineReceived(self, line):
        temp = line.split()
        if len(temp) == 1:
            params = []
        else:
            params = temp[1:]
        cmd = temp[0]
        handler = getattr(self, "handle_%s" % cmd.upper(), None)
        if handler:
            handler(params)
        else:
            self.handle_UNKNOWN(cmd, params)

    def handle_VER(self, params):
        checkParamLen(len(params), 1, 'VER')
        if params[0].upper() == "MSNFTP":
            self.sendLine("VER MSNFTP")
        else: # they sent some weird version during negotiation, i'm quitting.
            self.transport.loseConnection()

    def handle_USR(self, params):
        checkParamLen(len(params), 2, 'USR')
        self.targetUser = params[0]
        if self.auth == int(params[1]):
            self.sendLine("FIL %s" % (self.fileSize))
        else: # they failed the auth test, disconnecting.
            self.transport.loseConnection()

    def handle_TFR(self, params):
        checkParamLen(len(params), 0, 'TFR')
        # they are ready for me to start sending
        self.sendPart()

    def handle_BYE(self, params):
        self.completed = (self.bytesSent == self.fileSize)
        self.transport.loseConnection()

    def handle_CCL(self, params):
        self.completed = (self.bytesSent == self.fileSize)
        self.transport.loseConnection()

    def handle_UNKNOWN(self, cmd, params):
        log.msg('received unknown command (%s), params: %s' % (cmd, params))

    def makeHeader(self, size):
        quotient, remainder = divmod(size, 256)
        return chr(0) + chr(remainder) + chr(quotient)

    def sendPart(self):
        if not self.connected:
            self._pendingSend = None
            return # may be buggy (if handle_CCL/BYE is called but self.connected is still 1)
        data = self.file.read(self.segmentSize)
        if data:
            dataSize = len(data)
            header = self.makeHeader(dataSize)
            self.bytesSent += dataSize
            self.transport.write(header + data)
            self._pendingSend = reactor.callLater(0, self.sendPart)
        else:
            self._pendingSend = None
            self.completed = 1
errorCodes = {

    200 : "Syntax error",
    201 : "Invalid parameter",
    205 : "Invalid user",
    206 : "Domain name missing",
    207 : "Already logged in",
    208 : "Invalid username",
    209 : "Invalid screen name",
    210 : "User list full",
    215 : "User already there",
    216 : "User already on list",
    217 : "User not online",
    218 : "Already in mode",
    219 : "User is in the opposite list",
    223 : "Too many groups",
    224 : "Invalid group",
    225 : "User not in group",
    229 : "Group name too long",
    230 : "Cannot remove group 0",
    231 : "Invalid group",
    280 : "Switchboard failed",
    281 : "Transfer to switchboard failed",
    300 : "Required field missing",
    301 : "Too many FND responses",
    302 : "Not logged in",
    500 : "Internal server error",
    501 : "Database server error",
    502 : "Command disabled",
    510 : "File operation failed",
    520 : "Memory allocation failed",
    540 : "Wrong CHL value sent to server",
    600 : "Server is busy",
    601 : "Server is unavaliable",
    602 : "Peer nameserver is down",
    603 : "Database connection failed",
    604 : "Server is going down",
    605 : "Server unavailable",
    707 : "Could not create connection",
    710 : "Invalid CVR parameters",
    711 : "Write is blocking",
    712 : "Session is overloaded",
    713 : "Too many active users",
    714 : "Too many sessions",
    715 : "Not expected",
    717 : "Bad friend file",
    731 : "Not expected",
    800 : "Requests too rapid",
    910 : "Server too busy",
    911 : "Authentication failed",
    912 : "Server too busy",
    913 : "Not allowed when offline",
    914 : "Server too busy",
    915 : "Server too busy",
    916 : "Server too busy",
    917 : "Server too busy",
    918 : "Server too busy",
    919 : "Server too busy",
    920 : "Not accepting new users",
    921 : "Server too busy",
    922 : "Server too busy",
    923 : "No parent consent",
    924 : "Passport account not yet verified"
}
statusCodes = {
    STATUS_ONLINE  : "Online",
    STATUS_OFFLINE : "Offline",
    STATUS_HIDDEN  : "Appear Offline",
    STATUS_IDLE    : "Idle",
    STATUS_AWAY    : "Away",
    STATUS_BUSY    : "Busy",
    STATUS_BRB     : "Be Right Back",
    STATUS_PHONE   : "On the Phone",
    STATUS_LUNCH   : "Out to Lunch"
}
listIDToCode = {
    FORWARD_LIST : 'fl',
    BLOCK_LIST   : 'bl',
    ALLOW_LIST   : 'al',
    REVERSE_LIST : 'rl'
}
listCodeToID = {}
for id,code in listIDToCode.items():
    listCodeToID[code] = id
del id, code
guidToClassName = {
    "{5D3E02AB-6190-11d3-BBBB-00C04F795683}": "file transfer",
    }
classNameToGUID = {}
for guid, name in guidToClassName.iteritems():
    classNameToGUID[name] = guid