# -*- test-case-name: lib.twisted.test.test_ftp -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import os
import time
import re
import operator
import stat
import errno
import fnmatch
import warnings
try:
    import pwd, grp
except ImportError:
    pwd = grp = None
from lib.zope.interface import Interface, implements
from twisted import copyright
from lib.twisted.internet import reactor, interfaces, protocol, error, defer
from lib.twisted.protocols import basic, policies
from lib.twisted.python import log, failure, filepath
from lib.twisted.python.compat import reduce
from lib.twisted.cred import error as cred_error, portal, credentials, checkers
RESTART_MARKER_REPLY                    = "100"
SERVICE_READY_IN_N_MINUTES              = "120"
DATA_CNX_ALREADY_OPEN_START_XFR         = "125"
FILE_STATUS_OK_OPEN_DATA_CNX            = "150"
CMD_OK                                  = "200.1"
TYPE_SET_OK                             = "200.2"
ENTERING_PORT_MODE                      = "200.3"
CMD_NOT_IMPLMNTD_SUPERFLUOUS            = "202"
SYS_STATUS_OR_HELP_REPLY                = "211"
DIR_STATUS                              = "212"
FILE_STATUS                             = "213"
HELP_MSG                                = "214"
NAME_SYS_TYPE                           = "215"
SVC_READY_FOR_NEW_USER                  = "220.1"
WELCOME_MSG                             = "220.2"
SVC_CLOSING_CTRL_CNX                    = "221"
GOODBYE_MSG                             = "221"
DATA_CNX_OPEN_NO_XFR_IN_PROGRESS        = "225"
CLOSING_DATA_CNX                        = "226"
TXFR_COMPLETE_OK                        = "226"
ENTERING_PASV_MODE                      = "227"
ENTERING_EPSV_MODE                      = "229"
USR_LOGGED_IN_PROCEED                   = "230.1"     # v1 of code 230
GUEST_LOGGED_IN_PROCEED                 = "230.2"     # v2 of code 230
REQ_FILE_ACTN_COMPLETED_OK              = "250"
PWD_REPLY                               = "257.1"
MKD_REPLY                               = "257.2"
USR_NAME_OK_NEED_PASS                   = "331.1"     # v1 of Code 331
GUEST_NAME_OK_NEED_EMAIL                = "331.2"     # v2 of code 331
NEED_ACCT_FOR_LOGIN                     = "332"
REQ_FILE_ACTN_PENDING_FURTHER_INFO      = "350"
SVC_NOT_AVAIL_CLOSING_CTRL_CNX          = "421.1"
TOO_MANY_CONNECTIONS                    = "421.2"
CANT_OPEN_DATA_CNX                      = "425"
CNX_CLOSED_TXFR_ABORTED                 = "426"
REQ_ACTN_ABRTD_FILE_UNAVAIL             = "450"
REQ_ACTN_ABRTD_LOCAL_ERR                = "451"
REQ_ACTN_ABRTD_INSUFF_STORAGE           = "452"
SYNTAX_ERR                              = "500"
SYNTAX_ERR_IN_ARGS                      = "501"
CMD_NOT_IMPLMNTD                        = "502"
BAD_CMD_SEQ                             = "503"
CMD_NOT_IMPLMNTD_FOR_PARAM              = "504"
NOT_LOGGED_IN                           = "530.1"     # v1 of code 530 - please log in
AUTH_FAILURE                            = "530.2"     # v2 of code 530 - authorization failure
NEED_ACCT_FOR_STOR                      = "532"
FILE_NOT_FOUND                          = "550.1"     # no such file or directory
PERMISSION_DENIED                       = "550.2"     # permission denied
ANON_USER_DENIED                        = "550.3"     # anonymous users can't alter filesystem
IS_NOT_A_DIR                            = "550.4"     # rmd called on a path that is not a directory
REQ_ACTN_NOT_TAKEN                      = "550.5"
FILE_EXISTS                             = "550.6"
IS_A_DIR                                = "550.7"
PAGE_TYPE_UNK                           = "551"
EXCEEDED_STORAGE_ALLOC                  = "552"
FILENAME_NOT_ALLOWED                    = "553"

RESPONSE = {
    RESTART_MARKER_REPLY:               '110 MARK yyyy-mmmm', # TODO: this must be fixed
    SERVICE_READY_IN_N_MINUTES:         '120 service ready in %s minutes',
    DATA_CNX_ALREADY_OPEN_START_XFR:    '125 Data connection already open, starting transfer',
    FILE_STATUS_OK_OPEN_DATA_CNX:       '150 File status okay; about to open data connection.',
    CMD_OK:                             '200 Command OK',
    TYPE_SET_OK:                        '200 Type set to %s.',
    ENTERING_PORT_MODE:                 '200 PORT OK',
    CMD_NOT_IMPLMNTD_SUPERFLUOUS:       '202 Command not implemented, superfluous at this site',
    SYS_STATUS_OR_HELP_REPLY:           '211 System status reply',
    DIR_STATUS:                         '212 %s',
    FILE_STATUS:                        '213 %s',
    HELP_MSG:                           '214 help: %s',
    NAME_SYS_TYPE:                      '215 UNIX Type: L8',
    WELCOME_MSG:                        "220 %s",
    SVC_READY_FOR_NEW_USER:             '220 Service ready',
    GOODBYE_MSG:                        '221 Goodbye.',
    DATA_CNX_OPEN_NO_XFR_IN_PROGRESS:   '225 data connection open, no transfer in progress',
    CLOSING_DATA_CNX:                   '226 Abort successful',
    TXFR_COMPLETE_OK:                   '226 Transfer Complete.',
    ENTERING_PASV_MODE:                 '227 Entering Passive Mode (%s).',
    ENTERING_EPSV_MODE:                 '229 Entering Extended Passive Mode (|||%s|).', # where is epsv defined in the rfc's?
    USR_LOGGED_IN_PROCEED:              '230 User logged in, proceed',
    GUEST_LOGGED_IN_PROCEED:            '230 Anonymous login ok, access restrictions apply.',
    REQ_FILE_ACTN_COMPLETED_OK:         '250 Requested File Action Completed OK', #i.e. CWD completed ok
    PWD_REPLY:                          '257 "%s"',
    MKD_REPLY:                          '257 "%s" created',
    'userotp':                          '331 Response to %s.',  # ???
    USR_NAME_OK_NEED_PASS:              '331 Password required for %s.',
    GUEST_NAME_OK_NEED_EMAIL:           '331 Guest login ok, type your email address as password.',
    REQ_FILE_ACTN_PENDING_FURTHER_INFO: '350 Requested file action pending further information.',
    SVC_NOT_AVAIL_CLOSING_CTRL_CNX:     '421 Service not available, closing control connection.',
    TOO_MANY_CONNECTIONS:               '421 Too many users right now, try again in a few minutes.',
    CANT_OPEN_DATA_CNX:                 "425 Can't open data connection.",
    CNX_CLOSED_TXFR_ABORTED:            '426 Transfer aborted.  Data connection closed.',
    REQ_ACTN_ABRTD_LOCAL_ERR:           '451 Requested action aborted. Local error in processing.',
    SYNTAX_ERR:                         "500 Syntax error: %s",
    SYNTAX_ERR_IN_ARGS:                 '501 syntax error in argument(s) %s.',
    CMD_NOT_IMPLMNTD:                   "502 Command '%s' not implemented",
    BAD_CMD_SEQ:                        '503 Incorrect sequence of commands: %s',
    CMD_NOT_IMPLMNTD_FOR_PARAM:         "504 Not implemented for parameter '%s'.",
    NOT_LOGGED_IN:                      '530 Please login with USER and PASS.',
    AUTH_FAILURE:                       '530 Sorry, Authentication failed.',
    NEED_ACCT_FOR_STOR:                 '532 Need an account for storing files',
    FILE_NOT_FOUND:                     '550 %s: No such file or directory.',
    PERMISSION_DENIED:                  '550 %s: Permission denied.',
    ANON_USER_DENIED:                   '550 Anonymous users are forbidden to change the filesystem',
    IS_NOT_A_DIR:                       '550 Cannot rmd, %s is not a directory',
    FILE_EXISTS:                        '550 %s: File exists',
    IS_A_DIR:                           '550 %s: is a directory',
    REQ_ACTN_NOT_TAKEN:                 '550 Requested action not taken: %s',
    EXCEEDED_STORAGE_ALLOC:             '552 Requested file action aborted, exceeded file storage allocation',
    FILENAME_NOT_ALLOWED:               '553 Requested action not taken, file name not allowed'
}

class InvalidPath(Exception):

def toSegments(cwd, path):
    if path.startswith('/'):
        segs = []
    else:
        segs = cwd[:]

    for s in path.split('/'):
        if s == '.' or s == '':
            continue
        elif s == '..':
            if segs:
                segs.pop()
            else:
                raise InvalidPath(cwd, path)
        elif '\0' in s or '/' in s:
            raise InvalidPath(cwd, path)
        else:
            segs.append(s)
    return segs

def errnoToFailure(e, path):
    if e == errno.ENOENT:
        return defer.fail(FileNotFoundError(path))
    elif e == errno.EACCES or e == errno.EPERM:
        return defer.fail(PermissionDeniedError(path))
    elif e == errno.ENOTDIR:
        return defer.fail(IsNotADirectoryError(path))
    elif e == errno.EEXIST:
        return defer.fail(FileExistsError(path))
    elif e == errno.EISDIR:
        return defer.fail(IsADirectoryError(path))
    else:
        return defer.fail()

class FTPCmdError(Exception):
    def __init__(self, *msg):
        Exception.__init__(self, *msg)
        self.errorMessage = msg

    def response(self):
        """
        Generate a FTP response message for this error.
        """
        return RESPONSE[self.errorCode] % self.errorMessage

class FileNotFoundError(FTPCmdError):
    errorCode = FILE_NOT_FOUND

class AnonUserDeniedError(FTPCmdError):
    def __init__(self):
        # No message
        FTPCmdError.__init__(self, None)

    errorCode = ANON_USER_DENIED

class PermissionDeniedError(FTPCmdError):
    errorCode = PERMISSION_DENIED

class IsNotADirectoryError(FTPCmdError):
    errorCode = IS_NOT_A_DIR

class FileExistsError(FTPCmdError):
    errorCode = FILE_EXISTS

class IsADirectoryError(FTPCmdError):
    errorCode = IS_A_DIR

class CmdSyntaxError(FTPCmdError):
    errorCode = SYNTAX_ERR

class CmdArgSyntaxError(FTPCmdError):
    errorCode = SYNTAX_ERR_IN_ARGS

class CmdNotImplementedError(FTPCmdError):
    errorCode = CMD_NOT_IMPLMNTD

class CmdNotImplementedForArgError(FTPCmdError):
    errorCode = CMD_NOT_IMPLMNTD_FOR_PARAM

class FTPError(Exception):
    pass

class PortConnectionError(Exception):
    pass

class BadCmdSequenceError(FTPCmdError):
    errorCode = BAD_CMD_SEQ

class AuthorizationError(FTPCmdError):
    errorCode = AUTH_FAILURE

def debugDeferred(self, *_):
    log.msg('debugDeferred(): %s' % str(_), debug=True)

_months = [
    None,
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

class DTP(object, protocol.Protocol):
    implements(interfaces.IConsumer)
    isConnected = False
    _cons = None
    _onConnLost = None
    _buffer = None

    def connectionMade(self):
        self.isConnected = True
        self.factory.deferred.callback(None)
        self._buffer = []

    def connectionLost(self, reason):
        self.isConnected = False
        if self._onConnLost is not None:
            self._onConnLost.callback(None)

    def sendLine(self, line):
        self.transport.write(line + '\r\n')

    def _formatOneListResponse(self, name, size, directory, permissions, hardlinks, modified, owner, group):
        def formatMode(mode):
            return ''.join([mode & (256 >> n) and 'rwx'[n % 3] or '-' for n in range(9)])

        def formatDate(mtime):
            now = time.gmtime()
            info = {
                'month': _months[mtime.tm_mon],
                'day': mtime.tm_mday,
                'year': mtime.tm_year,
                'hour': mtime.tm_hour,
                'minute': mtime.tm_min
                }
            if now.tm_year != mtime.tm_year:
                return '%(month)s %(day)02d %(year)5d' % info
            else:
                return '%(month)s %(day)02d %(hour)02d:%(minute)02d' % info

        format = ('%(directory)s%(permissions)s%(hardlinks)4d '
                  '%(owner)-9s %(group)-9s %(size)15d %(date)12s '
                  '%(name)s')

        return format % {
            'directory': directory and 'd' or '-',
            'permissions': formatMode(permissions),
            'hardlinks': hardlinks,
            'owner': owner[:8],
            'group': group[:8],
            'size': size,
            'date': formatDate(time.gmtime(modified)),
            'name': name}

    def sendListResponse(self, name, response):
        self.sendLine(self._formatOneListResponse(name, *response))

    def registerProducer(self, producer, streaming):
        return self.transport.registerProducer(producer, streaming)

    def unregisterProducer(self):
        self.transport.unregisterProducer()
        self.transport.loseConnection()

    def write(self, data):
        if self.isConnected:
            return self.transport.write(data)
        raise Exception("Crap damn crap damn crap damn")

    def _conswrite(self, bytes):
        try:
            self._cons.write(bytes)
        except:
            self._onConnLost.errback()

    def dataReceived(self, bytes):
        if self._cons is not None:
            self._conswrite(bytes)
        else:
            self._buffer.append(bytes)

    def _unregConsumer(self, ignored):
        self._cons.unregisterProducer()
        self._cons = None
        del self._onConnLost
        return ignored

    def registerConsumer(self, cons):
        assert self._cons is None
        self._cons = cons
        self._cons.registerProducer(self, True)
        for chunk in self._buffer:
            self._conswrite(chunk)
        self._buffer = None
        if self.isConnected:
            self._onConnLost = d = defer.Deferred()
            d.addBoth(self._unregConsumer)
            return d
        else:
            self._cons.unregisterProducer()
            self._cons = None
            return defer.succeed(None)

    def resumeProducing(self):
        self.transport.resumeProducing()

    def pauseProducing(self):
        self.transport.pauseProducing()

    def stopProducing(self):
        self.transport.stopProducing()

class DTPFactory(protocol.ClientFactory):
    _IN_PROGRESS = object()
    _FAILED = object()
    _FINISHED = object()
    _state = _IN_PROGRESS
    peerCheck = False

    def __init__(self, pi, peerHost=None, reactor=None):
        self.pi = pi                        # the protocol interpreter that is using this factory
        self.peerHost = peerHost            # the from FTP.transport.peerHost()
        self.deferred = defer.Deferred()    # deferred will fire when instance is connected
        self.delayedCall = None
        if reactor is None:
            from lib.twisted.internet import reactor
        self._reactor = reactor

    def buildProtocol(self, addr):
        log.msg('DTPFactory.buildProtocol', debug=True)
        if self._state is not self._IN_PROGRESS:
            return None
        self._state = self._FINISHED
        self.cancelTimeout()
        p = DTP()
        p.factory = self
        p.pi = self.pi
        self.pi.dtpInstance = p
        return p

    def stopFactory(self):
        log.msg('dtpFactory.stopFactory', debug=True)
        self.cancelTimeout()

    def timeoutFactory(self):
        log.msg('timed out waiting for DTP connection')
        if self._state is not self._IN_PROGRESS:
            return
        self._state = self._FAILED

        d = self.deferred
        self.deferred = None
        d.errback(
            PortConnectionError(defer.TimeoutError("DTPFactory timeout")))

    def cancelTimeout(self):
        if self.delayedCall is not None and self.delayedCall.active():
            log.msg('cancelling DTP timeout', debug=True)
            self.delayedCall.cancel()

    def setTimeout(self, seconds):
        log.msg('DTPFactory.setTimeout set to %s seconds' % seconds)
        self.delayedCall = self._reactor.callLater(seconds, self.timeoutFactory)

    def clientConnectionFailed(self, connector, reason):
        if self._state is not self._IN_PROGRESS:
            return
        self._state = self._FAILED
        d = self.deferred
        self.deferred = None
        d.errback(PortConnectionError(reason))

class ASCIIConsumerWrapper(object):
    def __init__(self, cons):
        self.cons = cons
        self.registerProducer = cons.registerProducer
        self.unregisterProducer = cons.unregisterProducer
        assert os.linesep == "\r\n" or len(os.linesep) == 1, "Unsupported platform (yea right like this even exists)"
        if os.linesep == "\r\n":
            self.write = cons.write

    def write(self, bytes):
        return self.cons.write(bytes.replace(os.linesep, "\r\n"))

class FileConsumer(object):
    implements(interfaces.IConsumer)

    def __init__(self, fObj):
        self.fObj = fObj

    def registerProducer(self, producer, streaming):
        self.producer = producer
        assert streaming

    def unregisterProducer(self):
        self.producer = None
        self.fObj.close()

    def write(self, bytes):
        self.fObj.write(bytes)

class FTPOverflowProtocol(basic.LineReceiver):
    def connectionMade(self):
        self.sendLine(RESPONSE[TOO_MANY_CONNECTIONS])
        self.transport.loseConnection()

class FTP(object, basic.LineReceiver, policies.TimeoutMixin):
    disconnected = False
    UNAUTH, INAUTH, AUTHED, RENAMING = range(4)
    dtpTimeout = 10
    portal = None
    shell = None
    dtpFactory = None
    dtpPort = None
    dtpInstance = None
    binary = True
    passivePortRange = xrange(0, 1)
    listenFactory = reactor.listenTCP

    def reply(self, key, *args):
        msg = RESPONSE[key] % args
        self.sendLine(msg)

    def connectionMade(self):
        self.state = self.UNAUTH
        self.setTimeout(self.timeOut)
        self.reply(WELCOME_MSG, self.factory.welcomeMessage)

    def connectionLost(self, reason):
        if self.dtpFactory:
            self.cleanupDTP()
        self.setTimeout(None)
        if hasattr(self.shell, 'logout') and self.shell.logout is not None:
            self.shell.logout()
        self.shell = None
        self.transport = None

    def timeoutConnection(self):
        self.transport.loseConnection()

    def lineReceived(self, line):
        self.resetTimeout()
        self.pauseProducing()

        def processFailed(err):
            if err.check(FTPCmdError):
                self.sendLine(err.value.response())
            elif (err.check(TypeError) and
                  err.value.args[0].find('takes exactly') != -1):
                self.reply(SYNTAX_ERR, "%s requires an argument." % (cmd,))
            else:
                log.msg("Unexpected FTP error")
                log.err(err)
                self.reply(REQ_ACTN_NOT_TAKEN, "internal server error")

        def processSucceeded(result):
            if isinstance(result, tuple):
                self.reply(*result)
            elif result is not None:
                self.reply(result)

        def allDone(ignored):
            if not self.disconnected:
                self.resumeProducing()

        spaceIndex = line.find(' ')
        if spaceIndex != -1:
            cmd = line[:spaceIndex]
            args = (line[spaceIndex + 1:],)
        else:
            cmd = line
            args = ()
        d = defer.maybeDeferred(self.processCommand, cmd, *args)
        d.addCallbacks(processSucceeded, processFailed)
        d.addErrback(log.err)

        from lib.twisted.internet import reactor
        reactor.callLater(0, d.addBoth, allDone)

    def processCommand(self, cmd, *params):
        cmd = cmd.upper()
        if self.state == self.UNAUTH:
            if cmd == 'USER':
                return self.ftp_USER(*params)
            elif cmd == 'PASS':
                return BAD_CMD_SEQ, "USER required before PASS"
            else:
                return NOT_LOGGED_IN
        elif self.state == self.INAUTH:
            if cmd == 'PASS':
                return self.ftp_PASS(*params)
            else:
                return BAD_CMD_SEQ, "PASS required after USER"
        elif self.state == self.AUTHED:
            method = getattr(self, "ftp_" + cmd, None)
            if method is not None:
                return method(*params)
            return defer.fail(CmdNotImplementedError(cmd))
        elif self.state == self.RENAMING:
            if cmd == 'RNTO':
                return self.ftp_RNTO(*params)
            else:
                return BAD_CMD_SEQ, "RNTO required after RNFR"

    def getDTPPort(self, factory):
        for portn in self.passivePortRange:
            try:
                dtpPort = self.listenFactory(portn, factory)
            except error.CannotListenError:
                continue
            else:
                return dtpPort
        raise error.CannotListenError('', portn,
            "No port available in range %s" %
            (self.passivePortRange,))

    def ftp_USER(self, username):
        if not username:
            return defer.fail(CmdSyntaxError('USER requires an argument'))

        self._user = username
        self.state = self.INAUTH
        if self.factory.allowAnonymous and self._user == self.factory.userAnonymous:
            return GUEST_NAME_OK_NEED_EMAIL
        else:
            return (USR_NAME_OK_NEED_PASS, username)

    def ftp_PASS(self, password):
        if self.factory.allowAnonymous and self._user == self.factory.userAnonymous:
            creds = credentials.Anonymous()
            reply = GUEST_LOGGED_IN_PROCEED
        else:
            creds = credentials.UsernamePassword(self._user, password)
            reply = USR_LOGGED_IN_PROCEED
        del self._user

        def _cbLogin((interface, avatar, logout)):
            assert interface is IFTPShell, "The realm is busted, jerk."
            self.shell = avatar
            self.logout = logout
            self.workingDirectory = []
            self.state = self.AUTHED
            return reply

        def _ebLogin(failure):
            failure.trap(cred_error.UnauthorizedLogin, cred_error.UnhandledCredentials)
            self.state = self.UNAUTH
            raise AuthorizationError

        d = self.portal.login(creds, None, IFTPShell)
        d.addCallbacks(_cbLogin, _ebLogin)
        return d

    def ftp_PASV(self):
        if self.dtpFactory is not None:
            self.cleanupDTP()
        self.dtpFactory = DTPFactory(pi=self)
        self.dtpFactory.setTimeout(self.dtpTimeout)
        self.dtpPort = self.getDTPPort(self.dtpFactory)
        host = self.transport.getHost().host
        port = self.dtpPort.getHost().port
        self.reply(ENTERING_PASV_MODE, encodeHostPort(host, port))
        return self.dtpFactory.deferred.addCallback(lambda ign: None)

    def ftp_PORT(self, address):
        addr = map(int, address.split(','))
        ip = '%d.%d.%d.%d' % tuple(addr[:4])
        port = addr[4] << 8 | addr[5]
        if self.dtpFactory is not None:
            self.cleanupDTP()
        self.dtpFactory = DTPFactory(pi=self, peerHost=self.transport.getPeer().host)
        self.dtpFactory.setTimeout(self.dtpTimeout)
        self.dtpPort = reactor.connectTCP(ip, port, self.dtpFactory)

        def connected(ignored):
            return ENTERING_PORT_MODE
        def connFailed(err):
            err.trap(PortConnectionError)
            return CANT_OPEN_DATA_CNX
        return self.dtpFactory.deferred.addCallbacks(connected, connFailed)

    def ftp_LIST(self, path=''):
        if self.dtpInstance is None or not self.dtpInstance.isConnected:
            return defer.fail(BadCmdSequenceError('must send PORT or PASV before RETR'))
        if path == "-a":
            path = ''
        if path == "-aL":
            path = ''
        if path == "-L":
            path = ''
        if path == "-la":
            path = ''

        def gotListing(results):
            self.reply(DATA_CNX_ALREADY_OPEN_START_XFR)
            for (name, attrs) in results:
                self.dtpInstance.sendListResponse(name, attrs)
            self.dtpInstance.transport.loseConnection()
            return (TXFR_COMPLETE_OK,)

        try:
            segments = toSegments(self.workingDirectory, path)
        except InvalidPath:
            return defer.fail(FileNotFoundError(path))

        d = self.shell.list(
            segments,
            ('size', 'directory', 'permissions', 'hardlinks',
             'modified', 'owner', 'group'))
        d.addCallback(gotListing)
        return d

    def ftp_NLST(self, path):
        if self.dtpInstance is None or not self.dtpInstance.isConnected:
            return defer.fail(
                BadCmdSequenceError('must send PORT or PASV before RETR'))

        try:
            segments = toSegments(self.workingDirectory, path)
        except InvalidPath:
            return defer.fail(FileNotFoundError(path))

        def cbList(results):
            self.reply(DATA_CNX_ALREADY_OPEN_START_XFR)
            for (name, ignored) in results:
                self.dtpInstance.sendLine(name)
            self.dtpInstance.transport.loseConnection()
            return (TXFR_COMPLETE_OK,)

        def cbGlob(results):
            self.reply(DATA_CNX_ALREADY_OPEN_START_XFR)
            for (name, ignored) in results:
                if fnmatch.fnmatch(name, segments[-1]):
                    self.dtpInstance.sendLine(name)
            self.dtpInstance.transport.loseConnection()
            return (TXFR_COMPLETE_OK,)

        def listErr(results):
            self.dtpInstance.transport.loseConnection()
            return (TXFR_COMPLETE_OK,)

        if segments and (
            '*' in segments[-1] or '?' in segments[-1] or
            ('[' in segments[-1] and ']' in segments[-1])):
            d = self.shell.list(segments[:-1])
            d.addCallback(cbGlob)
        else:
            d = self.shell.list(segments)
            d.addCallback(cbList)
            d.addErrback(listErr)
        return d

    def ftp_CWD(self, path):
        try:
            segments = toSegments(self.workingDirectory, path)
        except InvalidPath:
            return defer.fail(FileNotFoundError(path))

        def accessGranted(result):
            self.workingDirectory = segments
            return (REQ_FILE_ACTN_COMPLETED_OK,)

        return self.shell.access(segments).addCallback(accessGranted)

    def ftp_CDUP(self):
        return self.ftp_CWD('..')

    def ftp_PWD(self):
        return (PWD_REPLY, '/' + '/'.join(self.workingDirectory))

    def ftp_RETR(self, path):
        if self.dtpInstance is None:
            raise BadCmdSequenceError('PORT or PASV required before RETR')

        try:
            newsegs = toSegments(self.workingDirectory, path)
        except InvalidPath:
            return defer.fail(FileNotFoundError(path))

        self.setTimeout(None)

        def enableTimeout(result):
            self.setTimeout(self.factory.timeOut)
            return result

        if not self.binary:
            cons = ASCIIConsumerWrapper(self.dtpInstance)
        else:
            cons = self.dtpInstance

        def cbSent(result):
            return (TXFR_COMPLETE_OK,)

        def ebSent(err):
            log.msg("Unexpected error attempting to transmit file to client:")
            log.err(err)
            return (CNX_CLOSED_TXFR_ABORTED,)

        def cbOpened(file):
            if self.dtpInstance.isConnected:
                self.reply(DATA_CNX_ALREADY_OPEN_START_XFR)
            else:
                self.reply(FILE_STATUS_OK_OPEN_DATA_CNX)

            d = file.send(cons)
            d.addCallbacks(cbSent, ebSent)
            return d

        def ebOpened(err):
            if not err.check(PermissionDeniedError, FileNotFoundError, IsNotADirectoryError):
                log.msg("Unexpected error attempting to open file for transmission:")
                log.err(err)
            if err.check(FTPCmdError):
                return (err.value.errorCode, '/'.join(newsegs))
            return (FILE_NOT_FOUND, '/'.join(newsegs))

        d = self.shell.openForReading(newsegs)
        d.addCallbacks(cbOpened, ebOpened)
        d.addBoth(enableTimeout)
        return d

    def ftp_STOR(self, path):
        if self.dtpInstance is None:
            raise BadCmdSequenceError('PORT or PASV required before STOR')

        try:
            newsegs = toSegments(self.workingDirectory, path)
        except InvalidPath:
            return defer.fail(FileNotFoundError(path))

        self.setTimeout(None)

        def enableTimeout(result):
            self.setTimeout(self.factory.timeOut)
            return result

        def cbSent(result):
            return (TXFR_COMPLETE_OK,)

        def ebSent(err):
            log.msg("Unexpected error receiving file from client:")
            log.err(err)
            return (CNX_CLOSED_TXFR_ABORTED,)

        def cbConsumer(cons):
            if not self.binary:
                cons = ASCIIConsumerWrapper(cons)

            d = self.dtpInstance.registerConsumer(cons)

            if self.dtpInstance.isConnected:
                self.reply(DATA_CNX_ALREADY_OPEN_START_XFR)
            else:
                self.reply(FILE_STATUS_OK_OPEN_DATA_CNX)

            return d

        def cbOpened(file):
            d = file.receive()
            d.addCallback(cbConsumer)
            d.addCallback(lambda ignored: file.close())
            d.addCallbacks(cbSent, ebSent)
            return d

        def ebOpened(err):
            if not err.check(PermissionDeniedError, FileNotFoundError, IsNotADirectoryError):
                log.msg("Unexpected error attempting to open file for upload:")
                log.err(err)
            if isinstance(err.value, FTPCmdError):
                return (err.value.errorCode, '/'.join(newsegs))
            return (FILE_NOT_FOUND, '/'.join(newsegs))

        d = self.shell.openForWriting(newsegs)
        d.addCallbacks(cbOpened, ebOpened)
        d.addBoth(enableTimeout)
        return d

    def ftp_SIZE(self, path):
        try:
            newsegs = toSegments(self.workingDirectory, path)
        except InvalidPath:
            return defer.fail(FileNotFoundError(path))

        def cbStat((size,)):
            return (FILE_STATUS, str(size))

        return self.shell.stat(newsegs, ('size',)).addCallback(cbStat)

    def ftp_MDTM(self, path):
        try:
            newsegs = toSegments(self.workingDirectory, path)
        except InvalidPath:
            return defer.fail(FileNotFoundError(path))

        def cbStat((modified,)):
            return (FILE_STATUS, time.strftime('%Y%m%d%H%M%S', time.gmtime(modified)))

        return self.shell.stat(newsegs, ('modified',)).addCallback(cbStat)

    def ftp_TYPE(self, type):
        p = type.upper()
        if p:
            f = getattr(self, 'type_' + p[0], None)
            if f is not None:
                return f(p[1:])
            return self.type_UNKNOWN(p)
        return (SYNTAX_ERR,)

    def type_A(self, code):
        if code == '' or code == 'N':
            self.binary = False
            return (TYPE_SET_OK, 'A' + code)
        else:
            return defer.fail(CmdArgSyntaxError(code))

    def type_I(self, code):
        if code == '':
            self.binary = True
            return (TYPE_SET_OK, 'I')
        else:
            return defer.fail(CmdArgSyntaxError(code))

    def type_UNKNOWN(self, code):
        return defer.fail(CmdNotImplementedForArgError(code))

    def ftp_SYST(self):
        return NAME_SYS_TYPE

    def ftp_STRU(self, structure):
        p = structure.upper()
        if p == 'F':
            return (CMD_OK,)
        return defer.fail(CmdNotImplementedForArgError(structure))

    def ftp_MODE(self, mode):
        p = mode.upper()
        if p == 'S':
            return (CMD_OK,)
        return defer.fail(CmdNotImplementedForArgError(mode))

    def ftp_MKD(self, path):
        try:
            newsegs = toSegments(self.workingDirectory, path)
        except InvalidPath:
            return defer.fail(FileNotFoundError(path))
        return self.shell.makeDirectory(newsegs).addCallback(lambda ign: (MKD_REPLY, path))

    def ftp_RMD(self, path):
        try:
            newsegs = toSegments(self.workingDirectory, path)
        except InvalidPath:
            return defer.fail(FileNotFoundError(path))
        return self.shell.removeDirectory(newsegs).addCallback(lambda ign: (REQ_FILE_ACTN_COMPLETED_OK,))

    def ftp_DELE(self, path):
        try:
            newsegs = toSegments(self.workingDirectory, path)
        except InvalidPath:
            return defer.fail(FileNotFoundError(path))
        return self.shell.removeFile(newsegs).addCallback(lambda ign: (REQ_FILE_ACTN_COMPLETED_OK,))

    def ftp_NOOP(self):
        return (CMD_OK,)

    def ftp_RNFR(self, fromName):
        self._fromName = fromName
        self.state = self.RENAMING
        return (REQ_FILE_ACTN_PENDING_FURTHER_INFO,)

    def ftp_RNTO(self, toName):
        fromName = self._fromName
        del self._fromName
        self.state = self.AUTHED
        try:
            fromsegs = toSegments(self.workingDirectory, fromName)
            tosegs = toSegments(self.workingDirectory, toName)
        except InvalidPath:
            return defer.fail(FileNotFoundError(fromName))
        return self.shell.rename(fromsegs, tosegs).addCallback(lambda ign: (REQ_FILE_ACTN_COMPLETED_OK,))

    def ftp_QUIT(self):
        self.reply(GOODBYE_MSG)
        self.transport.loseConnection()
        self.disconnected = True

    def cleanupDTP(self):
        log.msg('cleanupDTP', debug=True)

        log.msg(self.dtpPort)
        dtpPort, self.dtpPort = self.dtpPort, None
        if interfaces.IListeningPort.providedBy(dtpPort):
            dtpPort.stopListening()
        elif interfaces.IConnector.providedBy(dtpPort):
            dtpPort.disconnect()
        else:
            assert False, "dtpPort should be an IListeningPort or IConnector, instead is %r" % (dtpPort,)

        self.dtpFactory.stopFactory()
        self.dtpFactory = None
        if self.dtpInstance is not None:
            self.dtpInstance = None

class FTPFactory(policies.LimitTotalConnectionsFactory):
    protocol = FTP
    overflowProtocol = FTPOverflowProtocol
    allowAnonymous = True
    userAnonymous = 'anonymous'
    timeOut = 600
    welcomeMessage = "Twisted %s FTP Server" % (copyright.version,)
    passivePortRange = xrange(0, 1)

    def __init__(self, portal=None, userAnonymous='anonymous'):
        self.portal = portal
        self.userAnonymous = userAnonymous
        self.instances = []

    def buildProtocol(self, addr):
        p = policies.LimitTotalConnectionsFactory.buildProtocol(self, addr)
        if p is not None:
            p.wrappedProtocol.portal = self.portal
            p.wrappedProtocol.timeOut = self.timeOut
            p.wrappedProtocol.passivePortRange = self.passivePortRange
        return p

    def stopFactory(self):
        [p.setTimeout(None) for p in self.instances if p.timeOut is not None]
        policies.LimitTotalConnectionsFactory.stopFactory(self)

class IFTPShell(Interface):
    def makeDirectory(path):

    def removeDirectory(path):

    def removeFile(path):

    def rename(fromPath, toPath):

    def access(path):

    def stat(path, keys=()):

    def list(path, keys=()):

    def openForReading(path):

    def openForWriting(path):

class IReadFile(Interface):
    def send(consumer):

class IWriteFile(Interface):
    def receive():

    def close():

def _getgroups(uid):
    result = []
    pwent = pwd.getpwuid(uid)

    result.append(pwent.pw_gid)

    for grent in grp.getgrall():
        if pwent.pw_name in grent.gr_mem:
            result.append(grent.gr_gid)
    return result

def _testPermissions(uid, gid, spath, mode='r'):
    if mode == 'r':
        usr = stat.S_IRUSR
        grp = stat.S_IRGRP
        oth = stat.S_IROTH
        amode = os.R_OK
    elif mode == 'w':
        usr = stat.S_IWUSR
        grp = stat.S_IWGRP
        oth = stat.S_IWOTH
        amode = os.W_OK
    else:
        raise ValueError("Invalid mode %r: must specify 'r' or 'w'" % (mode,))
    access = False
    if os.path.exists(spath):
        if uid == 0:
            access = True
        else:
            s = os.stat(spath)
            if usr & s.st_mode and uid == s.st_uid:
                access = True
            elif grp & s.st_mode and gid in _getgroups(uid):
                access = True
            elif oth & s.st_mode:
                access = True
    if access:
        if not os.access(spath, amode):
            access = False
            log.msg("Filesystem grants permission to UID %d but it is inaccessible to me running as UID %d" % (
                uid, os.getuid()))
    return access

class FTPAnonymousShell(object):
    implements(IFTPShell)

    def __init__(self, filesystemRoot):
        self.filesystemRoot = filesystemRoot

    def _path(self, path):
        return reduce(filepath.FilePath.child, path, self.filesystemRoot)

    def makeDirectory(self, path):
        return defer.fail(AnonUserDeniedError())

    def removeDirectory(self, path):
        return defer.fail(AnonUserDeniedError())

    def removeFile(self, path):
        return defer.fail(AnonUserDeniedError())

    def rename(self, fromPath, toPath):
        return defer.fail(AnonUserDeniedError())

    def receive(self, path):
        path = self._path(path)
        return defer.fail(AnonUserDeniedError())

    def openForReading(self, path):
        p = self._path(path)
        if p.isdir():
            return defer.fail(IsADirectoryError(path))
        try:
            f = p.open('r')
        except (IOError, OSError), e:
            return errnoToFailure(e.errno, path)
        except:
            return defer.fail()
        else:
            return defer.succeed(_FileReader(f))

    def openForWriting(self, path):
        return defer.fail(PermissionDeniedError("STOR not allowed"))

    def access(self, path):
        p = self._path(path)
        if not p.exists():
            return defer.fail(FileNotFoundError(path))
        try:
            p.listdir()
        except (IOError, OSError), e:
            return errnoToFailure(e.errno, path)
        except:
            return defer.fail()
        else:
            return defer.succeed(None)

    def stat(self, path, keys=()):
        p = self._path(path)
        if p.isdir():
            try:
                statResult = self._statNode(p, keys)
            except (IOError, OSError), e:
                return errnoToFailure(e.errno, path)
            except:
                return defer.fail()
            else:
                return defer.succeed(statResult)
        else:
            return self.list(path, keys).addCallback(lambda res: res[0][1])

    def list(self, path, keys=()):
        filePath = self._path(path)
        if filePath.isdir():
            entries = filePath.listdir()
            fileEntries = [filePath.child(p) for p in entries]
        elif filePath.isfile():
            entries = [os.path.join(*filePath.segmentsFrom(self.filesystemRoot))]
            fileEntries = [filePath]
        else:
            return defer.fail(FileNotFoundError(path))

        results = []
        for fileName, filePath in zip(entries, fileEntries):
            ent = []
            results.append((fileName, ent))
            if keys:
                try:
                    ent.extend(self._statNode(filePath, keys))
                except (IOError, OSError), e:
                    return errnoToFailure(e.errno, fileName)
                except:
                    return defer.fail()

        return defer.succeed(results)

    def _statNode(self, filePath, keys):
        filePath.restat()
        return [getattr(self, '_stat_' + k)(filePath.statinfo) for k in keys]

    _stat_size = operator.attrgetter('st_size')
    _stat_permissions = operator.attrgetter('st_mode')
    _stat_hardlinks = operator.attrgetter('st_nlink')
    _stat_modified = operator.attrgetter('st_mtime')

    def _stat_owner(self, st):
        if pwd is not None:
            try:
                return pwd.getpwuid(st.st_uid)[0]
            except KeyError:
                pass
        return str(st.st_uid)

    def _stat_group(self, st):
        if grp is not None:
            try:
                return grp.getgrgid(st.st_gid)[0]
            except KeyError:
                pass
        return str(st.st_gid)

    def _stat_directory(self, st):
        return bool(st.st_mode & stat.S_IFDIR)

class _FileReader(object):
    implements(IReadFile)

    def __init__(self, fObj):
        self.fObj = fObj
        self._send = False

    def _close(self, passthrough):
        self._send = True
        self.fObj.close()
        return passthrough

    def send(self, consumer):
        assert not self._send, "Can only call IReadFile.send *once* per instance"
        self._send = True
        d = basic.FileSender().beginFileTransfer(self.fObj, consumer)
        d.addBoth(self._close)
        return d

class FTPShell(FTPAnonymousShell):
    def makeDirectory(self, path):
        p = self._path(path)
        try:
            p.makedirs()
        except (IOError, OSError), e:
            return errnoToFailure(e.errno, path)
        except:
            return defer.fail()
        else:
            return defer.succeed(None)

    def removeDirectory(self, path):
        p = self._path(path)
        if p.isfile():
            return defer.fail(IsNotADirectoryError(path))
        try:
            os.rmdir(p.path)
        except (IOError, OSError), e:
            return errnoToFailure(e.errno, path)
        except:
            return defer.fail()
        else:
            return defer.succeed(None)

    def removeFile(self, path):
        p = self._path(path)
        if p.isdir():
            return defer.fail(IsADirectoryError(path))
        try:
            p.remove()
        except (IOError, OSError), e:
            return errnoToFailure(e.errno, path)
        except:
            return defer.fail()
        else:
            return defer.succeed(None)

    def rename(self, fromPath, toPath):
        fp = self._path(fromPath)
        tp = self._path(toPath)
        try:
            os.rename(fp.path, tp.path)
        except (IOError, OSError), e:
            return errnoToFailure(e.errno, fromPath)
        except:
            return defer.fail()
        else:
            return defer.succeed(None)

    def openForWriting(self, path):
        p = self._path(path)
        if p.isdir():
            # Normally, we would only check for EISDIR in open, but win32
            # returns EACCES in this case, so we check before
            return defer.fail(IsADirectoryError(path))
        try:
            fObj = p.open('w')
        except (IOError, OSError), e:
            return errnoToFailure(e.errno, path)
        except:
            return defer.fail()
        return defer.succeed(_FileWriter(fObj))

class _FileWriter(object):
    implements(IWriteFile)

    def __init__(self, fObj):
        self.fObj = fObj
        self._receive = False

    def receive(self):
        assert not self._receive, "Can only call IWriteFile.receive *once* per instance"
        self._receive = True
        return defer.succeed(FileConsumer(self.fObj))

    def close(self):
        return defer.succeed(None)

class FTPRealm:
    implements(portal.IRealm)

    def __init__(self, anonymousRoot):
        self.anonymousRoot = filepath.FilePath(anonymousRoot)

    def requestAvatar(self, avatarId, mind, *interfaces):
        for iface in interfaces:
            if iface is IFTPShell:
                if avatarId is checkers.ANONYMOUS:
                    avatar = FTPAnonymousShell(self.anonymousRoot)
                else:
                    avatar = FTPShell(filepath.FilePath("/home/" + avatarId))
                return IFTPShell, avatar, getattr(avatar, 'logout', lambda: None)
        raise NotImplementedError("Only IFTPShell interface is supported by this realm")

class ConnectionLost(FTPError):
    pass

class CommandFailed(FTPError):
    pass

class BadResponse(FTPError):
    pass

class UnexpectedResponse(FTPError):
    pass

class UnexpectedData(FTPError):
    pass

class FTPCommand:
    def __init__(self, text=None, public=0):
        self.text = text
        self.deferred = defer.Deferred()
        self.ready = 1
        self.public = public
        self.transferDeferred = None

    def fail(self, failure):
        if self.public:
            self.deferred.errback(failure)

class ProtocolWrapper(protocol.Protocol):
    def __init__(self, original, deferred):
        self.original = original
        self.deferred = deferred
    def makeConnection(self, transport):
        self.original.makeConnection(transport)
    def dataReceived(self, data):
        self.original.dataReceived(data)
    def connectionLost(self, reason):
        self.original.connectionLost(reason)
        self.deferred.callback(None)

class SenderProtocol(protocol.Protocol):
    implements(interfaces.IFinishableConsumer)

    def __init__(self):
        self.connectedDeferred = defer.Deferred()
        self.deferred = defer.Deferred()

    def dataReceived(self, data):
        raise UnexpectedData(
            "Received data from the server on a "
            "send-only data-connection"
        )

    def makeConnection(self, transport):
        protocol.Protocol.makeConnection(self, transport)
        self.connectedDeferred.callback(self)

    def connectionLost(self, reason):
        if reason.check(error.ConnectionDone):
            self.deferred.callback('connection done')
        else:
            self.deferred.errback(reason)

    def write(self, data):
        self.transport.write(data)

    def registerProducer(self, producer, streaming):
        self.transport.registerProducer(producer, streaming)

    def unregisterProducer(self):
        self.transport.unregisterProducer()

    def finish(self):
        self.transport.loseConnection()

def decodeHostPort(line):
    abcdef = re.sub('[^0-9, ]', '', line)
    parsed = [int(p.strip()) for p in abcdef.split(',')]
    for x in parsed:
        if x < 0 or x > 255:
            raise ValueError("Out of range", line, x)
    a, b, c, d, e, f = parsed
    host = "%s.%s.%s.%s" % (a, b, c, d)
    port = (int(e) << 8) + int(f)
    return host, port

def encodeHostPort(host, port):
    numbers = host.split('.') + [str(port >> 8), str(port % 256)]
    return ','.join(numbers)

def _unwrapFirstError(failure):
    failure.trap(defer.FirstError)
    return failure.value.subFailure

class FTPDataPortFactory(protocol.ServerFactory):
    noisy = 0
    def buildProtocol(self, addr):
        self.protocol.factory = self
        self.port.loseConnection()
        return self.protocol

class FTPClientBasic(basic.LineReceiver):
    debug = False

    def __init__(self):
        self.actionQueue = []
        self.greeting = None
        self.nextDeferred = defer.Deferred().addCallback(self._cb_greeting)
        self.nextDeferred.addErrback(self.fail)
        self.response = []
        self._failed = 0

    def fail(self, error):
        self._fail(error)

    def _fail(self, error):
        if self._failed:
            return error
        self._failed = 1
        if self.nextDeferred:
            try:
                self.nextDeferred.errback(failure.Failure(ConnectionLost('FTP connection lost', error)))
            except defer.AlreadyCalledError:
                pass
        for ftpCommand in self.actionQueue:
            ftpCommand.fail(failure.Failure(ConnectionLost('FTP connection lost', error)))
        return error

    def _cb_greeting(self, greeting):
        self.greeting = greeting

    def sendLine(self, line):
        if line is None:
            return
        basic.LineReceiver.sendLine(self, line)

    def sendNextCommand(self):
        ftpCommand = self.popCommandQueue()
        if ftpCommand is None:
            self.nextDeferred = None
            return
        if not ftpCommand.ready:
            self.actionQueue.insert(0, ftpCommand)
            reactor.callLater(1.0, self.sendNextCommand)
            self.nextDeferred = None
            return

        if ftpCommand.text == 'PORT':
            self.generatePortCommand(ftpCommand)

        if self.debug:
            log.msg('<-- %s' % ftpCommand.text)
        self.nextDeferred = ftpCommand.deferred
        self.sendLine(ftpCommand.text)

    def queueCommand(self, ftpCommand):
        self.actionQueue.append(ftpCommand)
        if (len(self.actionQueue) == 1 and self.transport is not None and
            self.nextDeferred is None):
            self.sendNextCommand()

    def queueStringCommand(self, command, public=1):
        ftpCommand = FTPCommand(command, public)
        self.queueCommand(ftpCommand)
        return ftpCommand.deferred

    def popCommandQueue(self):
        if self.actionQueue:
            return self.actionQueue.pop(0)
        else:
            return None

    def queueLogin(self, username, password):
        deferreds = []
        userDeferred = self.queueStringCommand('USER ' + username, public=0)
        deferreds.append(userDeferred)
        if password is not None:
            passwordCmd = FTPCommand('PASS ' + password, public=0)
            self.queueCommand(passwordCmd)
            deferreds.append(passwordCmd.deferred)

            def cancelPasswordIfNotNeeded(response):
                if response[0].startswith('230'):
                    self.actionQueue.remove(passwordCmd)
                return response
            userDeferred.addCallback(cancelPasswordIfNotNeeded)

        for deferred in deferreds:
            deferred.addErrback(self.fail)
            deferred.addErrback(lambda x: None)

    def lineReceived(self, line):
        if self.debug:
            log.msg('--> %s' % line)
        self.response.append(line)
        codeIsValid = re.match(r'\d{3} ', line)
        if not codeIsValid:
            return

        code = line[0:3]
        if code[0] == '1':
            return
        if self.nextDeferred is None:
            self.fail(UnexpectedResponse(self.response))
            return
        response = self.response
        self.response = []

        if code[0] in ('2', '3'):
            self.nextDeferred.callback(response)
        elif code[0] in ('4', '5'):
            self.nextDeferred.errback(failure.Failure(CommandFailed(response)))
        else:
            log.msg('Server sent invalid response code %s' % (code,))
            self.nextDeferred.errback(failure.Failure(BadResponse(response)))
        self.sendNextCommand()

    def connectionLost(self, reason):
        self._fail(reason)

class _PassiveConnectionFactory(protocol.ClientFactory):
    noisy = False

    def __init__(self, protoInstance):
        self.protoInstance = protoInstance

    def buildProtocol(self, ignored):
        self.protoInstance.factory = self
        return self.protoInstance

    def clientConnectionFailed(self, connector, reason):
        e = FTPError('Connection Failed', reason)
        self.protoInstance.deferred.errback(e)

class FTPClient(FTPClientBasic):
    connectFactory = reactor.connectTCP

    def __init__(self, username='anonymous',
                 password='twisted@twistedmatrix.com',
                 passive=1):
        FTPClientBasic.__init__(self)
        self.queueLogin(username, password)

        self.passive = passive

    def fail(self, error):
        self.transport.loseConnection()
        self._fail(error)

    def receiveFromConnection(self, commands, protocol):
        protocol = interfaces.IProtocol(protocol)
        wrapper = ProtocolWrapper(protocol, defer.Deferred())
        return self._openDataConnection(commands, wrapper)

    def queueLogin(self, username, password):
        FTPClientBasic.queueLogin(self, username, password)
        d = self.queueStringCommand('TYPE I', public=0)
        d.addErrback(self.fail)
        d.addErrback(lambda x: None)

    def sendToConnection(self, commands):
        s = SenderProtocol()
        r = self._openDataConnection(commands, s)
        return (s.connectedDeferred, r)

    def _openDataConnection(self, commands, protocol):
        cmds = [FTPCommand(command, public=1) for command in commands]
        cmdsDeferred = defer.DeferredList([cmd.deferred for cmd in cmds],
                                    fireOnOneErrback=True, consumeErrors=True)
        cmdsDeferred.addErrback(_unwrapFirstError)
        if self.passive:
            _mutable = [None]
            def doPassive(response):
                """Connect to the port specified in the response to PASV"""
                host, port = decodeHostPort(response[-1][4:])

                f = _PassiveConnectionFactory(protocol)
                _mutable[0] = self.connectFactory(host, port, f)

            pasvCmd = FTPCommand('PASV')
            self.queueCommand(pasvCmd)
            pasvCmd.deferred.addCallback(doPassive).addErrback(self.fail)

            results = [cmdsDeferred, pasvCmd.deferred, protocol.deferred]
            d = defer.DeferredList(results, fireOnOneErrback=True, consumeErrors=True)
            d.addErrback(_unwrapFirstError)

            def close(x, m=_mutable):
                m[0] and m[0].disconnect()
                return x
            d.addBoth(close)
        else:
            portCmd = FTPCommand('PORT')
            portCmd.transferDeferred = protocol.deferred
            portCmd.protocol = protocol
            portCmd.deferred.addErrback(portCmd.transferDeferred.errback)
            self.queueCommand(portCmd)
            portCmd.loseConnection = lambda result: result
            portCmd.fail = lambda error: error
            cmdsDeferred.addErrback(lambda e, pc=portCmd: pc.fail(e) or e)
            results = [cmdsDeferred, portCmd.deferred, portCmd.transferDeferred]
            d = defer.DeferredList(results, fireOnOneErrback=True, consumeErrors=True)
            d.addErrback(_unwrapFirstError)

        for cmd in cmds:
            self.queueCommand(cmd)
        return d

    def generatePortCommand(self, portCmd):
        factory = FTPDataPortFactory()
        factory.protocol = portCmd.protocol
        listener = reactor.listenTCP(0, factory)
        factory.port = listener

        def listenerFail(error, listener=listener):
            if listener.connected:
                listener.loseConnection()
            return error
        portCmd.fail = listenerFail

        host = self.transport.getHost().host
        port = listener.getHost().port
        portCmd.text = 'PORT ' + encodeHostPort(host, port)

    def escapePath(self, path):
        return path.replace('\n', '\0')

    def retrieveFile(self, path, protocol, offset=0):
        cmds = ['RETR ' + self.escapePath(path)]
        if offset:
            cmds.insert(0, ('REST ' + str(offset)))
        return self.receiveFromConnection(cmds, protocol)

    retr = retrieveFile

    def storeFile(self, path, offset=0):
        cmds = ['STOR ' + self.escapePath(path)]
        if offset:
            cmds.insert(0, ('REST ' + str(offset)))
        return self.sendToConnection(cmds)

    stor = storeFile

    def rename(self, pathFrom, pathTo):
        renameFrom = self.queueStringCommand('RNFR ' + self.escapePath(pathFrom))
        renameTo = self.queueStringCommand('RNTO ' + self.escapePath(pathTo))
        fromResponse = []
        result = defer.Deferred()
        result.addCallback(lambda toResponse: (fromResponse, toResponse))

        def ebFrom(failure):
            self.popCommandQueue()
            result.errback(failure)

        renameFrom.addCallbacks(fromResponse.extend, ebFrom)
        renameTo.chainDeferred(result)
        return result

    def list(self, path, protocol):
        if path is None:
            path = ''
        return self.receiveFromConnection(['LIST ' + self.escapePath(path)], protocol)

    def nlst(self, path, protocol):
        if path is None:
            path = ''
        return self.receiveFromConnection(['NLST ' + self.escapePath(path)], protocol)

    def cwd(self, path):
        return self.queueStringCommand('CWD ' + self.escapePath(path))

    def changeDirectory(self, path):
        warnings.warn(
            "FTPClient.changeDirectory is deprecated in Twisted 8.2 and "
            "newer.  Use FTPClient.cwd instead.",
            category=DeprecationWarning,
            stacklevel=2)

        def cbResult(result):
            if result[-1][:3] != '250':
                return failure.Failure(CommandFailed(result))
            return True
        return self.cwd(path).addCallback(cbResult)

    def makeDirectory(self, path):
        return self.queueStringCommand('MKD ' + self.escapePath(path))

    def removeFile(self, path):
        return self.queueStringCommand('DELE ' + self.escapePath(path))

    def cdup(self):
        return self.queueStringCommand('CDUP')

    def pwd(self):
        return self.queueStringCommand('PWD')

    def getDirectory(self):

        def cbParse(result):
            try:
                if int(result[0].split(' ', 1)[0]) != 257:
                    raise ValueError
            except (IndexError, ValueError):
                return failure.Failure(CommandFailed(result))
            path = parsePWDResponse(result[0])
            if path is None:
                return failure.Failure(CommandFailed(result))
            return path
        return self.pwd().addCallback(cbParse)

    def quit(self):
        return self.queueStringCommand('QUIT')

class FTPFileListProtocol(basic.LineReceiver):
    fileLinePattern = re.compile(
        r'^(?P<filetype>.)(?P<perms>.{9})\s+(?P<nlinks>\d*)\s*'
        r'(?P<owner>\S+)\s+(?P<group>\S+)\s+(?P<size>\d+)\s+'
        r'(?P<date>...\s+\d+\s+[\d:]+)\s+(?P<filename>([^ ]|\\ )*?)'
        r'( -> (?P<linktarget>[^\r]*))?\r?$'
    )
    delimiter = '\n'
    def __init__(self):
        self.files = []

    def lineReceived(self, line):
        d = self.parseDirectoryLine(line)
        if d is None:
            self.unknownLine(line)
        else:
            self.addFile(d)

    def parseDirectoryLine(self, line):
        match = self.fileLinePattern.match(line)
        if match is None:
            return None
        else:
            d = match.groupdict()
            d['filename'] = d['filename'].replace(r'\ ', ' ')
            d['nlinks'] = int(d['nlinks'])
            d['size'] = int(d['size'])
            if d['linktarget']:
                d['linktarget'] = d['linktarget'].replace(r'\ ', ' ')
            return d

    def addFile(self, info):
        self.files.append(info)

    def unknownLine(self, line):
        pass

def parsePWDResponse(response):
    match = re.search('"(.*)"', response)
    if match:
        return match.groups()[0]
    else:
        return None
