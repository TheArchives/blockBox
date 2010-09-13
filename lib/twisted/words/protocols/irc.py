# -*- test-case-name: lib.twisted.words.test.test_irc -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import errno, os, random, re, stat, struct, sys, time, types, traceback
import string, socket
import warnings
from os import path
from lib.twisted.internet import reactor, protocol
from lib.twisted.persisted import styles
from lib.twisted.protocols import basic
from lib.twisted.python import log, reflect, text
NUL = chr(0)
CR = chr(015)
NL = chr(012)
LF = NL
SPC = chr(040)
CHANNEL_PREFIXES = '&#!+'
class IRCBadMessage(Exception):
    pass

class IRCPasswordMismatch(Exception):
    pass

class IRCBadModes(ValueError):

def parsemsg(s):
    prefix = ''
    trailing = []
    if not s:
        raise IRCBadMessage("Empty line.")
    if s[0] == ':':
        prefix, s = s[1:].split(' ', 1)
    if s.find(' :') != -1:
        s, trailing = s.split(' :', 1)
        args = s.split()
        args.append(trailing)
    else:
        args = s.split()
    command = args.pop(0)
    return prefix, command, args

def split(str, length = 80):
    if length <= 0:
        raise ValueError("Length must be a number greater than zero")
    r = []
    while len(str) > length:
        w, n = str[:length].rfind(' '), str[:length].find('\n')
        if w == -1 and n == -1:
            line, str = str[:length], str[length:]
        else:
            if n == -1:
                i = w
            else:
                i = n
            if i == 0:
                str = str[1:]
                continue
            line, str = str[:i], str[i+1:]
        r.append(line)
    if len(str):
        r.extend(str.split('\n'))
    return r

def _intOrDefault(value, default=None):
    if value:
        try:
            return int(value)
        except (TypeError, ValueError):
            pass
    return default

class UnhandledCommand(RuntimeError):

class _CommandDispatcherMixin(object):
    prefix = None
    def dispatch(self, commandName, *args):
        def _getMethodName(command):
            return '%s_%s' % (self.prefix, command)

        def _getMethod(name):
            return getattr(self, _getMethodName(name), None)

        method = _getMethod(commandName)
        if method is not None:
            return method(*args)

        method = _getMethod('unknown')
        if method is None:
            raise UnhandledCommand("No handler for %r could be found" % (_getMethodName(commandName),))
        return method(commandName, *args)

def parseModes(modes, params, paramModes=('', '')):
    if len(modes) == 0:
        raise IRCBadModes('Empty mode string')

    if modes[0] not in '+-':
        raise IRCBadModes('Malformed modes string: %r' % (modes,))
    changes = ([], [])
    direction = None
    count = -1
    for ch in modes:
        if ch in '+-':
            if count == 0:
                raise IRCBadModes('Empty mode sequence: %r' % (modes,))
            direction = '+-'.index(ch)
            count = 0
        else:
            param = None
            if ch in paramModes[direction]:
                try:
                    param = params.pop(0)
                except IndexError:
                    raise IRCBadModes('Not enough parameters: %r' % (ch,))
            changes[direction].append((ch, param))
            count += 1
    if len(params) > 0:
        raise IRCBadModes('Too many parameters: %r %r' % (modes, params))
    if count == 0:
        raise IRCBadModes('Empty mode sequence: %r' % (modes,))

    return changes

class IRC(protocol.Protocol):
    buffer = ""
    hostname = None
    encoding = None
    def connectionMade(self):
        self.channels = []
        if self.hostname is None:
            self.hostname = socket.getfqdn()

    def sendLine(self, line):
        if self.encoding is not None:
            if isinstance(line, unicode):
                line = line.encode(self.encoding)
        self.transport.write("%s%s%s" % (line, CR, LF))

    def sendMessage(self, command, *parameter_list, **prefix):
        if not command:
            raise ValueError, "IRC message requires a command."
        if ' ' in command or command[0] == ':':
            raise ValueError, "Somebody screwed up, 'cuz this doesn't" \
                  " look like a command to me: %s" % command

        line = string.join([command] + list(parameter_list))
        if prefix.has_key('prefix'):
            line = ":%s %s" % (prefix['prefix'], line)
        self.sendLine(line)
        if len(parameter_list) > 15:
            log.msg("Message has %d parameters (RFC allows 15):\n%s" %
                    (len(parameter_list), line))

    def dataReceived(self, data):
        lines = (self.buffer + data).split(LF)
        self.buffer = lines.pop()

        for line in lines:
            if len(line) <= 2:
                continue
            if line[-1] == CR:
                line = line[:-1]
            prefix, command, params = parsemsg(line)
            command = command.upper()
            self.handleCommand(command, prefix, params)

    def handleCommand(self, command, prefix, params):
        method = getattr(self, "irc_%s" % command, None)
        try:
            if method is not None:
                method(prefix, params)
            else:
                self.irc_unknown(prefix, command, params)
        except:
            log.deferr()

    def irc_unknown(self, prefix, command, params):
        raise NotImplementedError(command, prefix, params)

    def privmsg(self, sender, recip, message):
        self.sendLine(":%s PRIVMSG %s :%s" % (sender, recip, lowQuote(message)))

    def notice(self, sender, recip, message):
        self.sendLine(":%s NOTICE %s :%s" % (sender, recip, message))

    def action(self, sender, recip, message):
        self.sendLine(":%s ACTION %s :%s" % (sender, recip, message))

    def topic(self, user, channel, topic, author=None):
        if author is None:
            if topic is None:
                self.sendLine(':%s %s %s %s :%s' % (
                    self.hostname, RPL_NOTOPIC, user, channel, 'No topic is set.'))
            else:
                self.sendLine(":%s %s %s %s :%s" % (
                    self.hostname, RPL_TOPIC, user, channel, lowQuote(topic)))
        else:
            self.sendLine(":%s TOPIC %s :%s" % (author, channel, lowQuote(topic)))

    def topicAuthor(self, user, channel, author, date):
        self.sendLine(':%s %d %s %s %s %d' % (
            self.hostname, 333, user, channel, author, date))

    def names(self, user, channel, names):
        prefixLength = len(channel) + len(user) + 10
        namesLength = 512 - prefixLength
        L = []
        count = 0
        for n in names:
            if count + len(n) + 1 > namesLength:
                self.sendLine(":%s %s %s = %s :%s" % (
                    self.hostname, RPL_NAMREPLY, user, channel, ' '.join(L)))
                L = [n]
                count = len(n)
            else:
                L.append(n)
                count += len(n) + 1
        if L:
            self.sendLine(":%s %s %s = %s :%s" % (
                self.hostname, RPL_NAMREPLY, user, channel, ' '.join(L)))
        self.sendLine(":%s %s %s %s :End of /NAMES list" % (
            self.hostname, RPL_ENDOFNAMES, user, channel))

    def who(self, user, channel, memberInfo):
        for info in memberInfo:
            (username, hostmask, server, nickname, flag, hops, realName) = info
            assert flag in ("H", "G")
            self.sendLine(":%s %s %s %s %s %s %s %s %s :%d %s" % (
                self.hostname, RPL_WHOREPLY, user, channel,
                username, hostmask, server, nickname, flag, hops, realName))
        self.sendLine(":%s %s %s %s :End of /WHO list." % (
            self.hostname, RPL_ENDOFWHO, user, channel))

    def whois(self, user, nick, username, hostname, realName, server, serverInfo, oper, idle, signOn, channels):
        self.sendLine(":%s %s %s %s %s %s * :%s" % (
            self.hostname, RPL_WHOISUSER, user, nick, username, hostname, realName))
        self.sendLine(":%s %s %s %s %s :%s" % (
            self.hostname, RPL_WHOISSERVER, user, nick, server, serverInfo))
        if oper:
            self.sendLine(":%s %s %s %s :is an IRC operator" % (
                self.hostname, RPL_WHOISOPERATOR, user, nick))
        self.sendLine(":%s %s %s %s %d %d :seconds idle, signon time" % (
            self.hostname, RPL_WHOISIDLE, user, nick, idle, signOn))
        self.sendLine(":%s %s %s %s :%s" % (
            self.hostname, RPL_WHOISCHANNELS, user, nick, ' '.join(channels)))
        self.sendLine(":%s %s %s %s :End of WHOIS list." % (
            self.hostname, RPL_ENDOFWHOIS, user, nick))

    def join(self, who, where):
        self.sendLine(":%s JOIN %s" % (who, where))

    def part(self, who, where, reason=None):
        if reason:
            self.sendLine(":%s PART %s :%s" % (who, where, reason))
        else:
            self.sendLine(":%s PART %s" % (who, where))

    def channelMode(self, user, channel, mode, *args):
        self.sendLine(":%s %s %s %s %s %s" % (
            self.hostname, RPL_CHANNELMODEIS, user, channel, mode, ' '.join(args)))

class ServerSupportedFeatures(_CommandDispatcherMixin):
    prefix = 'isupport'
    def __init__(self):
        self._features = {
            'CHANNELLEN': 200,
            'CHANTYPES': tuple('#&'),
            'MODES': 3,
            'NICKLEN': 9,
            'PREFIX': self._parsePrefixParam('(ovh)@+%'),
            'CHANMODES': self._parseChanModesParam(['b', '', 'lk'])}

    def _splitParamArgs(cls, params, valueProcessor=None):
        if valueProcessor is None:
            valueProcessor = lambda x: x

        def _parse():
            for param in params:
                if ':' not in param:
                    param += ':'
                a, b = param.split(':', 1)
                yield a, valueProcessor(b)
        return list(_parse())
    _splitParamArgs = classmethod(_splitParamArgs)

    def _unescapeParamValue(cls, value):
        def _unescape():
            parts = value.split('\\x')
            yield parts.pop(0)
            for s in parts:
                octet, rest = s[:2], s[2:]
                try:
                    octet = int(octet, 16)
                except ValueError:
                    raise ValueError('Invalid hex octet: %r' % (octet,))
                yield chr(octet) + rest

        if '\\x' not in value:
            return value
        return ''.join(_unescape())
    _unescapeParamValue = classmethod(_unescapeParamValue)

    def _splitParam(cls, param):
        if '=' not in param:
            param += '='
        key, value = param.split('=', 1)
        return key, map(cls._unescapeParamValue, value.split(','))
    _splitParam = classmethod(_splitParam)

    def _parsePrefixParam(cls, prefix):
        if not prefix:
            return None
        if prefix[0] != '(' and ')' not in prefix:
            raise ValueError('Malformed PREFIX parameter')
        modes, symbols = prefix.split(')', 1)
        symbols = zip(symbols, xrange(len(symbols)))
        modes = modes[1:]
        return dict(zip(modes, symbols))
    _parsePrefixParam = classmethod(_parsePrefixParam)

    def _parseChanModesParam(self, params):
        names = ('addressModes', 'param', 'setParam', 'noParam')
        if len(params) > len(names):
            raise ValueError(
                'Expecting a maximum of %d channel mode parameters, got %d' % (
                    len(names), len(params)))
        items = map(lambda key, value: (key, value or ''), names, params)
        return dict(items)
    _parseChanModesParam = classmethod(_parseChanModesParam)

    def getFeature(self, feature, default=None):
        return self._features.get(feature, default)

    def hasFeature(self, feature):
        return self.getFeature(feature) is not None

    def parse(self, params):
        for param in params:
            key, value = self._splitParam(param)
            if key.startswith('-'):
                self._features.pop(key[1:], None)
            else:
                self._features[key] = self.dispatch(key, value)

    def isupport_unknown(self, command, params):
        return tuple(params)

    def isupport_CHANLIMIT(self, params):
        return self._splitParamArgs(params, _intOrDefault)

    def isupport_CHANMODES(self, params):
        try:
            return self._parseChanModesParam(params)
        except ValueError:
            return self.getFeature('CHANMODES')

    def isupport_CHANNELLEN(self, params):
        return _intOrDefault(params[0], self.getFeature('CHANNELLEN'))

    def isupport_CHANTYPES(self, params):
        return tuple(params[0])

    def isupport_EXCEPTS(self, params):
        return params[0] or 'e'

    def isupport_IDCHAN(self, params):
        return self._splitParamArgs(params)

    def isupport_INVEX(self, params):
        return params[0] or 'I'

    def isupport_KICKLEN(self, params):
        return _intOrDefault(params[0])

    def isupport_MAXLIST(self, params):
        return self._splitParamArgs(params, _intOrDefault)

    def isupport_MODES(self, params):
        return _intOrDefault(params[0])

    def isupport_NETWORK(self, params):
        return params[0]

    def isupport_NICKLEN(self, params):
        return _intOrDefault(params[0], self.getFeature('NICKLEN'))

    def isupport_PREFIX(self, params):
        try:
            return self._parsePrefixParam(params[0])
        except ValueError:
            return self.getFeature('PREFIX')

    def isupport_SAFELIST(self, params):
        return True

    def isupport_STATUSMSG(self, params):
        return params[0]

    def isupport_TARGMAX(self, params):
        return dict(self._splitParamArgs(params, _intOrDefault))

    def isupport_TOPICLEN(self, params):
        return _intOrDefault(params[0])

class IRCClient(basic.LineReceiver):
    motd = None
    nickname = 'irc'
    password = None
    realname = None
    username = None
    userinfo = None
    fingerReply = None
    versionName = None
    versionNum = None
    versionEnv = None
    sourceURL = "http://twistedmatrix.com/downloads/"
    dcc_destdir = '.'
    dcc_sessions = None
    performLogin = 1
    lineRate = None
    _queue = None
    _queueEmptying = None
    delimiter = '\n'
    __pychecker__ = 'unusednames=params,prefix,channel'
    _registered = False
    _attemptedNick = ''
    erroneousNickFallback = 'defaultnick'
    def _reallySendLine(self, line):
        return basic.LineReceiver.sendLine(self, lowQuote(line) + '\r')

    def sendLine(self, line):
        if self.lineRate is None:
            self._reallySendLine(line)
        else:
            self._queue.append(line)
            if not self._queueEmptying:
                self._sendLine()

    def _sendLine(self):
        if self._queue:
            self._reallySendLine(self._queue.pop(0))
            self._queueEmptying = reactor.callLater(self.lineRate,
                                                    self._sendLine)
        else:
            self._queueEmptying = None

    def created(self, when):

    def yourHost(self, info):

    def myInfo(self, servername, version, umodes, cmodes):

    def luserClient(self, info):

    def bounce(self, info):

    def isupport(self, options):

    def luserChannels(self, channels):

    def luserOp(self, ops):

    def luserMe(self, info):

    def privmsg(self, user, channel, message):
        pass

    def joined(self, channel):

    def left(self, channel):

    def noticed(self, user, channel, message):
        self.privmsg(user, channel, message)

    def modeChanged(self, user, channel, set, modes, args):

    def pong(self, user, secs):
        pass

    def signedOn(self):
        pass

    def kickedFrom(self, channel, kicker, message):
        pass

    def nickChanged(self, nick):
        self.nickname = nick

    def userJoined(self, user, channel):
        pass

    def userLeft(self, user, channel):
        pass

    def userQuit(self, user, quitMessage):
        pass

    def userKicked(self, kickee, channel, kicker, message):
        pass

    def action(self, user, channel, data):
        pass

    def topicUpdated(self, user, channel, newTopic):
        pass

    def userRenamed(self, oldname, newname):
        pass

    def receivedMOTD(self, motd):
        pass

    def join(self, channel, key=None):
        if channel[0] not in CHANNEL_PREFIXES:
            channel = '#' + channel
        if key:
            self.sendLine("JOIN %s %s" % (channel, key))
        else:
            self.sendLine("JOIN %s" % (channel,))

    def leave(self, channel, reason=None):
        if channel[0] not in CHANNEL_PREFIXES:
            channel = '#' + channel
        if reason:
            self.sendLine("PART %s :%s" % (channel, reason))
        else:
            self.sendLine("PART %s" % (channel,))

    def kick(self, channel, user, reason=None):
        if channel[0] not in CHANNEL_PREFIXES:
            channel = '#' + channel
        if reason:
            self.sendLine("KICK %s %s :%s" % (channel, user, reason))
        else:
            self.sendLine("KICK %s %s" % (channel, user))
    part = leave

    def topic(self, channel, topic=None):
        if channel[0] not in CHANNEL_PREFIXES:
            channel = '#' + channel
        if topic != None:
            self.sendLine("TOPIC %s :%s" % (channel, topic))
        else:
            self.sendLine("TOPIC %s" % (channel,))

    def mode(self, chan, set, modes, limit = None, user = None, mask = None):
        if set:
            line = 'MODE %s +%s' % (chan, modes)
        else:
            line = 'MODE %s -%s' % (chan, modes)
        if limit is not None:
            line = '%s %d' % (line, limit)
        elif user is not None:
            line = '%s %s' % (line, user)
        elif mask is not None:
            line = '%s %s' % (line, mask)
        self.sendLine(line)

    def say(self, channel, message, length = None):
        if channel[0] not in CHANNEL_PREFIXES:
            channel = '#' + channel
        self.msg(channel, message, length)

    def msg(self, user, message, length = None):
        fmt = "PRIVMSG %s :%%s" % (user,)

        if length is None:
            self.sendLine(fmt % (message,))
        else:
            minimumLength = len(fmt)
            if length <= minimumLength:
                raise ValueError("Maximum length must exceed %d for message "
                                 "to %s" % (minimumLength, user))
            lines = split(message, length - minimumLength)
            map(lambda line, self=self, fmt=fmt: self.sendLine(fmt % line),
                lines)

    def notice(self, user, message):
        self.sendLine("NOTICE %s :%s" % (user, message))

    def away(self, message=''):
        self.sendLine("AWAY :%s" % message)

    def back(self):
        self.away()

    def whois(self, nickname, server=None):
        if server is None:
            self.sendLine('WHOIS ' + nickname)
        else:
            self.sendLine('WHOIS %s %s' % (server, nickname))

    def register(self, nickname, hostname='foo', servername='bar'):
        if self.password is not None:
            self.sendLine("PASS %s" % self.password)
        self.setNick(nickname)
        if self.username is None:
            self.username = nickname
        self.sendLine("USER %s %s %s :%s" % (self.username, hostname, servername, self.realname))

    def setNick(self, nickname):
        self._attemptedNick = nickname
        self.sendLine("NICK %s" % nickname)

    def quit(self, message = ''):
        self.sendLine("QUIT :%s" % message)

    def describe(self, channel, action):
        self.ctcpMakeQuery(channel, [('ACTION', action)])

    def me(self, channel, action):
        warnings.warn("me() is deprecated since Twisted 9.0. Use IRCClient.describe().",
                DeprecationWarning, stacklevel=2)

        if channel[0] not in CHANNEL_PREFIXES:
            channel = '#' + channel
        self.describe(channel, action)
    _pings = None
    _MAX_PINGRING = 12

    def ping(self, user, text = None):
        if self._pings is None:
            self._pings = {}

        if text is None:
            chars = string.letters + string.digits + string.punctuation
            key = ''.join([random.choice(chars) for i in range(12)])
        else:
            key = str(text)
        self._pings[(user, key)] = time.time()
        self.ctcpMakeQuery(user, [('PING', key)])

        if len(self._pings) > self._MAX_PINGRING:
            byValue = [(v, k) for (k, v) in self._pings.items()]
            byValue.sort()
            excess = self._MAX_PINGRING - len(self._pings)
            for i in xrange(excess):
                del self._pings[byValue[i][1]]

    def dccSend(self, user, file):
        if type(file) == types.StringType:
            file = open(file, 'r')

        size = fileSize(file)

        name = getattr(file, "name", "file@%s" % (id(file),))

        factory = DccSendFactory(file)
        port = reactor.listenTCP(0, factory, 1)

        raise NotImplementedError,(
            "XXX!!! Help!  I need to bind a socket, have it listen, and tell me its address.  "
            "(and stop accepting once we've made a single connection.)")

        my_address = struct.pack("!I", my_address)
        args = ['SEND', name, my_address, str(port)]
        if not (size is None):
            args.append(size)
        args = string.join(args, ' ')
        self.ctcpMakeQuery(user, [('DCC', args)])

    def dccResume(self, user, fileName, port, resumePos):
        self.ctcpMakeQuery(user, [
            ('DCC', ['RESUME', fileName, port, resumePos])])

    def dccAcceptResume(self, user, fileName, port, resumePos):
        self.ctcpMakeQuery(user, [
            ('DCC', ['ACCEPT', fileName, port, resumePos])])

    def irc_ERR_NICKNAMEINUSE(self, prefix, params):
        self._attemptedNick = self.alterCollidedNick(self._attemptedNick)
        self.setNick(self._attemptedNick)


    def alterCollidedNick(self, nickname):
        return nickname + '_'

    def irc_ERR_ERRONEUSNICKNAME(self, prefix, params):
        if not self._registered:
            self.setNick(self.erroneousNickFallback)

    def irc_ERR_PASSWDMISMATCH(self, prefix, params):
        raise IRCPasswordMismatch("Password Incorrect.")

    def irc_RPL_WELCOME(self, prefix, params):
        self._registered = True
        self.nickname = self._attemptedNick
        self.signedOn()

    def irc_JOIN(self, prefix, params):
        nick = string.split(prefix,'!')[0]
        channel = params[-1]
        if nick == self.nickname:
            self.joined(channel)
        else:
            self.userJoined(nick, channel)

    def irc_PART(self, prefix, params):
        nick = string.split(prefix,'!')[0]
        channel = params[0]
        if nick == self.nickname:
            self.left(channel)
        else:
            self.userLeft(nick, channel)

    def irc_QUIT(self, prefix, params):
        nick = string.split(prefix,'!')[0]
        self.userQuit(nick, params[0])

    def irc_MODE(self, user, params):
        channel, modes, args = params[0], params[1], params[2:]

        if modes[0] not in '-+':
            modes = '+' + modes
        if channel == self.nickname:
            paramModes = self.getUserModeParams()
        else:
            paramModes = self.getChannelModeParams()

        try:
            added, removed = parseModes(modes, args, paramModes)
        except IRCBadModes:
            log.err(None, 'An error occured while parsing the following '
                          'MODE message: MODE %s' % (' '.join(params),))
        else:
            if added:
                modes, params = zip(*added)
                self.modeChanged(user, channel, True, ''.join(modes), params)

            if removed:
                modes, params = zip(*removed)
                self.modeChanged(user, channel, False, ''.join(modes), params)

    def irc_PING(self, prefix, params):
        self.sendLine("PONG %s" % params[-1])

    def irc_PRIVMSG(self, prefix, params):
        user = prefix
        channel = params[0]
        message = params[-1]
        if not message: return
        if message[0]==X_DELIM:
            m = ctcpExtract(message)
            if m['extended']:
                self.ctcpQuery(user, channel, m['extended'])
            if not m['normal']:
                return
            message = string.join(m['normal'], ' ')
        self.privmsg(user, channel, message)

    def irc_NOTICE(self, prefix, params):
        user = prefix
        channel = params[0]
        message = params[-1]

        if message[0]==X_DELIM:
            m = ctcpExtract(message)
            if m['extended']:
                self.ctcpReply(user, channel, m['extended'])

            if not m['normal']:
                return

            message = string.join(m['normal'], ' ')

        self.noticed(user, channel, message)

    def irc_NICK(self, prefix, params):
        nick = string.split(prefix,'!', 1)[0]
        if nick == self.nickname:
            self.nickChanged(params[0])
        else:
            self.userRenamed(nick, params[0])

    def irc_KICK(self, prefix, params):
        kicker = string.split(prefix,'!')[0]
        channel = params[0]
        kicked = params[1]
        message = params[-1]
        if string.lower(kicked) == string.lower(self.nickname):
            self.kickedFrom(channel, kicker, message)
        else:
            self.userKicked(kicked, channel, kicker, message)

    def irc_TOPIC(self, prefix, params):
        user = string.split(prefix, '!')[0]
        channel = params[0]
        newtopic = params[1]
        self.topicUpdated(user, channel, newtopic)

    def irc_RPL_TOPIC(self, prefix, params):
        user = string.split(prefix, '!')[0]
        channel = params[1]
        newtopic = params[2]
        self.topicUpdated(user, channel, newtopic)

    def irc_RPL_NOTOPIC(self, prefix, params):
        user = string.split(prefix, '!')[0]
        channel = params[1]
        newtopic = ""
        self.topicUpdated(user, channel, newtopic)

    def irc_RPL_MOTDSTART(self, prefix, params):
        if params[-1].startswith("- "):
            params[-1] = params[-1][2:]
        self.motd = [params[-1]]

    def irc_RPL_MOTD(self, prefix, params):
        if params[-1].startswith("- "):
            params[-1] = params[-1][2:]
        if self.motd is None:
            self.motd = []
        self.motd.append(params[-1])

    def irc_RPL_ENDOFMOTD(self, prefix, params):
        motd = self.motd
        self.motd = None
        self.receivedMOTD(motd)

    def irc_RPL_CREATED(self, prefix, params):
        self.created(params[1])

    def irc_RPL_YOURHOST(self, prefix, params):
        self.yourHost(params[1])

    def irc_RPL_MYINFO(self, prefix, params):
        info = params[1].split(None, 3)
        while len(info) < 4:
            info.append(None)
        self.myInfo(*info)

    def irc_RPL_BOUNCE(self, prefix, params):
        self.bounce(params[1])

    def irc_RPL_ISUPPORT(self, prefix, params):
        args = params[1:-1]
        self.supported.parse(args)
        self.isupport(args)

    def irc_RPL_LUSERCLIENT(self, prefix, params):
        self.luserClient(params[1])

    def irc_RPL_LUSEROP(self, prefix, params):
        try:
            self.luserOp(int(params[1]))
        except ValueError:
            pass

    def irc_RPL_LUSERCHANNELS(self, prefix, params):
        try:
            self.luserChannels(int(params[1]))
        except ValueError:
            pass

    def irc_RPL_LUSERME(self, prefix, params):
        self.luserMe(params[1])

    def irc_unknown(self, prefix, command, params):
        pass

    def ctcpQuery(self, user, channel, messages):
        for m in messages:
            method = getattr(self, "ctcpQuery_%s" % m[0], None)
            if method:
                method(user, channel, m[1])
            else:
                self.ctcpUnknownQuery(user, channel, m[0], m[1])

    def ctcpQuery_ACTION(self, user, channel, data):
        self.action(user, channel, data)

    def ctcpQuery_PING(self, user, channel, data):
        nick = string.split(user,"!")[0]
        self.ctcpMakeReply(nick, [("PING", data)])

    def ctcpQuery_FINGER(self, user, channel, data):
        if data is not None:
            self.quirkyMessage("Why did %s send '%s' with a FINGER query?"
                               % (user, data))
        if not self.fingerReply:
            return

        if callable(self.fingerReply):
            reply = self.fingerReply()
        else:
            reply = str(self.fingerReply)

        nick = string.split(user,"!")[0]
        self.ctcpMakeReply(nick, [('FINGER', reply)])

    def ctcpQuery_VERSION(self, user, channel, data):
        if data is not None:
            self.quirkyMessage("Why did %s send '%s' with a VERSION query?"
                               % (user, data))

        if self.versionName:
            nick = string.split(user,"!")[0]
            self.ctcpMakeReply(nick, [('VERSION', '%s:%s:%s' %
                                       (self.versionName,
                                        self.versionNum or '',
                                        self.versionEnv or ''))])

    def ctcpQuery_SOURCE(self, user, channel, data):
        if data is not None:
            self.quirkyMessage("Why did %s send '%s' with a SOURCE query?"
                               % (user, data))
        if self.sourceURL:
            nick = string.split(user,"!")[0]
            self.ctcpMakeReply(nick, [('SOURCE', self.sourceURL),
                                      ('SOURCE', None)])

    def ctcpQuery_USERINFO(self, user, channel, data):
        if data is not None:
            self.quirkyMessage("Why did %s send '%s' with a USERINFO query?"
                               % (user, data))
        if self.userinfo:
            nick = string.split(user,"!")[0]
            self.ctcpMakeReply(nick, [('USERINFO', self.userinfo)])

    def ctcpQuery_CLIENTINFO(self, user, channel, data):
        nick = string.split(user,"!")[0]
        if not data:
            names = reflect.prefixedMethodNames(self.__class__,
                                                'ctcpQuery_')

            self.ctcpMakeReply(nick, [('CLIENTINFO',
                                       string.join(names, ' '))])
        else:
            args = string.split(data)
            method = getattr(self, 'ctcpQuery_%s' % (args[0],), None)
            if not method:
                self.ctcpMakeReply(nick, [('ERRMSG',
                                           "CLIENTINFO %s :"
                                           "Unknown query '%s'"
                                           % (data, args[0]))])
                return
            doc = getattr(method, '__doc__', '')
            self.ctcpMakeReply(nick, [('CLIENTINFO', doc)])

    def ctcpQuery_ERRMSG(self, user, channel, data):
        nick = string.split(user,"!")[0]
        self.ctcpMakeReply(nick, [('ERRMSG',
                                   "%s :No error has occoured." % data)])

    def ctcpQuery_TIME(self, user, channel, data):
        if data is not None:
            self.quirkyMessage("Why did %s send '%s' with a TIME query?"
                               % (user, data))
        nick = string.split(user,"!")[0]
        self.ctcpMakeReply(nick,
                           [('TIME', ':%s' %
                             time.asctime(time.localtime(time.time())))])

    def ctcpQuery_DCC(self, user, channel, data):
        if not data: return
        dcctype = data.split(None, 1)[0].upper()
        handler = getattr(self, "dcc_" + dcctype, None)
        if handler:
            if self.dcc_sessions is None:
                self.dcc_sessions = []
            data = data[len(dcctype)+1:]
            handler(user, channel, data)
        else:
            nick = string.split(user,"!")[0]
            self.ctcpMakeReply(nick, [('ERRMSG',
                                       "DCC %s :Unknown DCC type '%s'"
                                       % (data, dcctype))])
            self.quirkyMessage("%s offered unknown DCC type %s"
                               % (user, dcctype))

    def dcc_SEND(self, user, channel, data):
        data = text.splitQuoted(data)
        if len(data) < 3:
            raise IRCBadMessage, "malformed DCC SEND request: %r" % (data,)

        (filename, address, port) = data[:3]

        address = dccParseAddress(address)
        try:
            port = int(port)
        except ValueError:
            raise IRCBadMessage, "Indecipherable port %r" % (port,)

        size = -1
        if len(data) >= 4:
            try:
                size = int(data[3])
            except ValueError:
                pass

        self.dccDoSend(user, address, port, filename, size, data)

    def dcc_ACCEPT(self, user, channel, data):
        data = text.splitQuoted(data)
        if len(data) < 3:
            raise IRCBadMessage, "malformed DCC SEND ACCEPT request: %r" % (data,)
        (filename, port, resumePos) = data[:3]
        try:
            port = int(port)
            resumePos = int(resumePos)
        except ValueError:
            return
        self.dccDoAcceptResume(user, filename, port, resumePos)

    def dcc_RESUME(self, user, channel, data):
        data = text.splitQuoted(data)
        if len(data) < 3:
            raise IRCBadMessage, "malformed DCC SEND RESUME request: %r" % (data,)
        (filename, port, resumePos) = data[:3]
        try:
            port = int(port)
            resumePos = int(resumePos)
        except ValueError:
            return
        self.dccDoResume(user, filename, port, resumePos)

    def dcc_CHAT(self, user, channel, data):
        data = text.splitQuoted(data)
        if len(data) < 3:
            raise IRCBadMessage, "malformed DCC CHAT request: %r" % (data,)

        (filename, address, port) = data[:3]

        address = dccParseAddress(address)
        try:
            port = int(port)
        except ValueError:
            raise IRCBadMessage, "Indecipherable port %r" % (port,)

        self.dccDoChat(user, channel, address, port, data)

    def dccDoSend(self, user, address, port, fileName, size, data):
        ## filename = path.basename(arg)
        ## protocol = DccFileReceive(filename, size,
        ##                           (user,channel,data),self.dcc_destdir)
        ## reactor.clientTCP(address, port, protocol)
        ## self.dcc_sessions.append(protocol)
        pass

    def dccDoResume(self, user, file, port, resumePos):
        pass

    def dccDoAcceptResume(self, user, file, port, resumePos):
        pass

    def dccDoChat(self, user, channel, address, port, data):
        pass
        #factory = DccChatFactory(self, queryData=(user, channel, data))
        #reactor.connectTCP(address, port, factory)
        #self.dcc_sessions.append(factory)

    #def ctcpQuery_SED(self, user, data):
    #    raise NotImplementedError

    def ctcpUnknownQuery(self, user, channel, tag, data):
        nick = string.split(user,"!")[0]
        self.ctcpMakeReply(nick, [('ERRMSG',
                                   "%s %s: Unknown query '%s'"
                                   % (tag, data, tag))])

        log.msg("Unknown CTCP query from %s: %s %s\n"
                 % (user, tag, data))

    def ctcpMakeReply(self, user, messages):
        self.notice(user, ctcpStringify(messages))

    def ctcpMakeQuery(self, user, messages):
        self.msg(user, ctcpStringify(messages))

    def ctcpReply(self, user, channel, messages):
        for m in messages:
            method = getattr(self, "ctcpReply_%s" % m[0], None)
            if method:
                method(user, channel, m[1])
            else:
                self.ctcpUnknownReply(user, channel, m[0], m[1])

    def ctcpReply_PING(self, user, channel, data):
        nick = user.split('!', 1)[0]
        if (not self._pings) or (not self._pings.has_key((nick, data))):
            raise IRCBadMessage,\
                  "Bogus PING response from %s: %s" % (user, data)

        t0 = self._pings[(nick, data)]
        self.pong(user, time.time() - t0)

    def ctcpUnknownReply(self, user, channel, tag, data):
        log.msg("Unknown CTCP reply from %s: %s %s\n"
                 % (user, tag, data))

    def badMessage(self, line, excType, excValue, tb):
        log.msg(line)
        log.msg(string.join(traceback.format_exception(excType,
                                                        excValue,
                                                        tb),''))

    def quirkyMessage(self, s):
        log.msg(s + '\n')

    def connectionMade(self):
        self.supported = ServerSupportedFeatures()
        self._queue = []
        if self.performLogin:
            self.register(self.nickname)

    def dataReceived(self, data):
        basic.LineReceiver.dataReceived(self, data.replace('\r', ''))

    def lineReceived(self, line):
        line = lowDequote(line)
        try:
            prefix, command, params = parsemsg(line)
            if numeric_to_symbolic.has_key(command):
                command = numeric_to_symbolic[command]
            self.handleCommand(command, prefix, params)
        except IRCBadMessage:
            self.badMessage(line, *sys.exc_info())

    def getUserModeParams(self):
        return ['', '']

    def getChannelModeParams(self):
        params = ['', '']
        prefixes = self.supported.getFeature('PREFIX', {})
        params[0] = params[1] = ''.join(prefixes.iterkeys())

        chanmodes = self.supported.getFeature('CHANMODES')
        if chanmodes is not None:
            params[0] += chanmodes.get('addressModes', '')
            params[0] += chanmodes.get('param', '')
            params[1] = params[0]
            params[0] += chanmodes.get('setParam', '')
        return params

    def handleCommand(self, command, prefix, params):
        method = getattr(self, "irc_%s" % command, None)
        try:
            if method is not None:
                method(prefix, params)
            else:
                self.irc_unknown(prefix, command, params)
        except:
            log.deferr()

    def __getstate__(self):
        dct = self.__dict__.copy()
        dct['dcc_sessions'] = None
        dct['_pings'] = None
        return dct

def dccParseAddress(address):
    if '.' in address:
        pass
    else:
        try:
            address = long(address)
        except ValueError:
            raise IRCBadMessage,\
                  "Indecipherable address %r" % (address,)
        else:
            address = (
                (address >> 24) & 0xFF,
                (address >> 16) & 0xFF,
                (address >> 8) & 0xFF,
                address & 0xFF,
                )
            address = '.'.join(map(str,address))
    return address

class DccFileReceiveBasic(protocol.Protocol, styles.Ephemeral):
    bytesReceived = 0

    def __init__(self, resumeOffset=0):
        self.bytesReceived = resumeOffset
        self.resume = (resumeOffset != 0)

    def dataReceived(self, data):
        self.bytesReceived = self.bytesReceived + len(data)
        self.transport.write(struct.pack('!i', self.bytesReceived))

class DccSendProtocol(protocol.Protocol, styles.Ephemeral):
    blocksize = 1024
    file = None
    bytesSent = 0
    completed = 0
    connected = 0

    def __init__(self, file):
        if type(file) is types.StringType:
            self.file = open(file, 'r')

    def connectionMade(self):
        self.connected = 1
        self.sendBlock()

    def dataReceived(self, data):
        bytesShesGot = struct.unpack("!I", data)
        if bytesShesGot < self.bytesSent:
            return
        elif bytesShesGot > self.bytesSent:
            self.transport.loseConnection()
            return
        self.sendBlock()

    def sendBlock(self):
        block = self.file.read(self.blocksize)
        if block:
            self.transport.write(block)
            self.bytesSent = self.bytesSent + len(block)
        else:
            self.transport.loseConnection()
            self.completed = 1

    def connectionLost(self, reason):
        self.connected = 0
        if hasattr(self.file, "close"):
            self.file.close()

class DccSendFactory(protocol.Factory):
    protocol = DccSendProtocol
    def __init__(self, file):
        self.file = file

    def buildProtocol(self, connection):
        p = self.protocol(self.file)
        p.factory = self
        return p

def fileSize(file):
    size = None
    if hasattr(file, "fileno"):
        fileno = file.fileno()
        try:
            stat_ = os.fstat(fileno)
            size = stat_[stat.ST_SIZE]
        except:
            pass
        else:
            return size

    if hasattr(file, "name") and path.exists(file.name):
        try:
            size = path.getsize(file.name)
        except:
            pass
        else:
            return size

    if hasattr(file, "seek") and hasattr(file, "tell"):
        try:
            try:
                file.seek(0, 2)
                size = file.tell()
            finally:
                file.seek(0, 0)
        except:
            pass
        else:
            return size

    return size

class DccChat(basic.LineReceiver, styles.Ephemeral):
    queryData = None
    delimiter = CR + NL
    client = None
    remoteParty = None
    buffer = ""

    def __init__(self, client, queryData=None):
        self.client = client
        if queryData:
            self.queryData = queryData
            self.remoteParty = self.queryData[0]

    def dataReceived(self, data):
        self.buffer = self.buffer + data
        lines = string.split(self.buffer, LF)
        self.buffer = lines.pop()

        for line in lines:
            if line[-1] == CR:
                line = line[:-1]
            self.lineReceived(line)

    def lineReceived(self, line):
        log.msg("DCC CHAT<%s> %s" % (self.remoteParty, line))
        self.client.privmsg(self.remoteParty,
                            self.client.nickname, line)

class DccChatFactory(protocol.ClientFactory):
    protocol = DccChat
    noisy = 0
    def __init__(self, client, queryData):
        self.client = client
        self.queryData = queryData

    def buildProtocol(self, addr):
        p = self.protocol(client=self.client, queryData=self.queryData)
        p.factory = self

    def clientConnectionFailed(self, unused_connector, unused_reason):
        self.client.dcc_sessions.remove(self)

    def clientConnectionLost(self, unused_connector, unused_reason):
        self.client.dcc_sessions.remove(self)

def dccDescribe(data):
    orig_data = data
    data = string.split(data)
    if len(data) < 4:
        return orig_data

    (dcctype, arg, address, port) = data[:4]

    if '.' in address:
        pass
    else:
        try:
            address = long(address)
        except ValueError:
            pass
        else:
            address = (
                (address >> 24) & 0xFF,
                (address >> 16) & 0xFF,
                (address >> 8) & 0xFF,
                address & 0xFF,
                )
            address = string.join(map(str,map(int,address)), ".")

    if dcctype == 'SEND':
        filename = arg

        size_txt = ''
        if len(data) >= 5:
            try:
                size = int(data[4])
                size_txt = ' of size %d bytes' % (size,)
            except ValueError:
                pass

        dcc_text = ("SEND for file '%s'%s at host %s, port %s"
                    % (filename, size_txt, address, port))
    elif dcctype == 'CHAT':
        dcc_text = ("CHAT for host %s, port %s"
                    % (address, port))
    else:
        dcc_text = orig_data

    return dcc_text

class DccFileReceive(DccFileReceiveBasic):
    filename = 'dcc'
    fileSize = -1
    destDir = '.'
    overwrite = 0
    fromUser = None
    queryData = None

    def __init__(self, filename, fileSize=-1, queryData=None,
                 destDir='.', resumeOffset=0):
        DccFileReceiveBasic.__init__(self, resumeOffset=resumeOffset)
        self.filename = filename
        self.destDir = destDir
        self.fileSize = fileSize

        if queryData:
            self.queryData = queryData
            self.fromUser = self.queryData[0]

    def set_directory(self, directory):
        if not path.exists(directory):
            raise OSError(errno.ENOENT, "You see no directory there.",
                          directory)
        if not path.isdir(directory):
            raise OSError(errno.ENOTDIR, "You cannot put a file into "
                          "something which is not a directory.",
                          directory)
        if not os.access(directory, os.X_OK | os.W_OK):
            raise OSError(errno.EACCES,
                          "This directory is too hard to write in to.",
                          directory)
        self.destDir = directory

    def set_filename(self, filename):
        self.filename = filename

    def set_overwrite(self, boolean):
        self.overwrite = boolean

    def connectionMade(self):
        dst = path.abspath(path.join(self.destDir,self.filename))
        exists = path.exists(dst)
        if self.resume and exists:
            self.file = open(dst, 'ab')
            log.msg("Attempting to resume %s - starting from %d bytes" %
                    (self.file, self.file.tell()))
        elif self.overwrite or not exists:
            self.file = open(dst, 'wb')
        else:
            raise OSError(errno.EEXIST,
                          "There's a file in the way.  "
                          "Perhaps that's why you cannot open it.",
                          dst)

    def dataReceived(self, data):
        self.file.write(data)
        DccFileReceiveBasic.dataReceived(self, data)

    def connectionLost(self, reason):
        self.connected = 0
        logmsg = ("%s closed." % (self,))
        if self.fileSize > 0:
            logmsg = ("%s  %d/%d bytes received"
                      % (logmsg, self.bytesReceived, self.fileSize))
            if self.bytesReceived == self.fileSize:
                pass # Hooray!
            elif self.bytesReceived < self.fileSize:
                logmsg = ("%s (Warning: %d bytes short)"
                          % (logmsg, self.fileSize - self.bytesReceived))
            else:
                logmsg = ("%s (file larger than expected)"
                          % (logmsg,))
        else:
            logmsg = ("%s  %d bytes received"
                      % (logmsg, self.bytesReceived))

        if hasattr(self, 'file'):
            logmsg = "%s and written to %s.\n" % (logmsg, self.file.name)
            if hasattr(self.file, 'close'): self.file.close()
        # self.transport.log(logmsg)

    def __str__(self):
        if not self.connected:
            return "<Unconnected DccFileReceive object at %x>" % (id(self),)
        from_ = self.transport.getPeer()
        if self.fromUser:
            from_ = "%s (%s)" % (self.fromUser, from_)

        s = ("DCC transfer of '%s' from %s" % (self.filename, from_))
        return s

    def __repr__(self):
        s = ("<%s at %x: GET %s>"
             % (self.__class__, id(self), self.filename))
        return s

X_DELIM = chr(001)

def ctcpExtract(message):
    extended_messages = []
    normal_messages = []
    retval = {'extended': extended_messages,
              'normal': normal_messages }

    messages = string.split(message, X_DELIM)
    odd = 0

    while messages:
        if odd:
            extended_messages.append(messages.pop(0))
        else:
            normal_messages.append(messages.pop(0))
        odd = not odd

    extended_messages[:] = filter(None, extended_messages)
    normal_messages[:] = filter(None, normal_messages)

    extended_messages[:] = map(ctcpDequote, extended_messages)
    for i in xrange(len(extended_messages)):
        m = string.split(extended_messages[i], SPC, 1)
        tag = m[0]
        if len(m) > 1:
            data = m[1]
        else:
            data = None

        extended_messages[i] = (tag, data)

    return retval

M_QUOTE= chr(020)
mQuoteTable = {
    NUL: M_QUOTE + '0',
    NL: M_QUOTE + 'n',
    CR: M_QUOTE + 'r',
    M_QUOTE: M_QUOTE + M_QUOTE
    }
mDequoteTable = {}
for k, v in mQuoteTable.items():
    mDequoteTable[v[-1]] = k
del k, v
mEscape_re = re.compile('%s.' % (re.escape(M_QUOTE),), re.DOTALL)

def lowQuote(s):
    for c in (M_QUOTE, NUL, NL, CR):
        s = string.replace(s, c, mQuoteTable[c])
    return s

def lowDequote(s):
    def sub(matchobj, mDequoteTable=mDequoteTable):
        s = matchobj.group()[1]
        try:
            s = mDequoteTable[s]
        except KeyError:
            s = s
        return s

    return mEscape_re.sub(sub, s)
X_QUOTE = '\\'

xQuoteTable = {
    X_DELIM: X_QUOTE + 'a',
    X_QUOTE: X_QUOTE + X_QUOTE
    }
xDequoteTable = {}

for k, v in xQuoteTable.items():
    xDequoteTable[v[-1]] = k

xEscape_re = re.compile('%s.' % (re.escape(X_QUOTE),), re.DOTALL)

def ctcpQuote(s):
    for c in (X_QUOTE, X_DELIM):
        s = string.replace(s, c, xQuoteTable[c])
    return s

def ctcpDequote(s):
    def sub(matchobj, xDequoteTable=xDequoteTable):
        s = matchobj.group()[1]
        try:
            s = xDequoteTable[s]
        except KeyError:
            s = s
        return s

    return xEscape_re.sub(sub, s)

def ctcpStringify(messages):
    coded_messages = []
    for (tag, data) in messages:
        if data:
            if not isinstance(data, types.StringType):
                try:
                    data = " ".join(map(str, data))
                except TypeError:
                    pass
            m = "%s %s" % (tag, data)
        else:
            m = str(tag)
        m = ctcpQuote(m)
        m = "%s%s%s" % (X_DELIM, m, X_DELIM)
        coded_messages.append(m)

    line = string.join(coded_messages, '')
    return line
RPL_WELCOME = '001'
RPL_YOURHOST = '002'
RPL_CREATED = '003'
RPL_MYINFO = '004'
RPL_ISUPPORT = '005'
RPL_BOUNCE = '010'
RPL_USERHOST = '302'
RPL_ISON = '303'
RPL_AWAY = '301'
RPL_UNAWAY = '305'
RPL_NOWAWAY = '306'
RPL_WHOISUSER = '311'
RPL_WHOISSERVER = '312'
RPL_WHOISOPERATOR = '313'
RPL_WHOISIDLE = '317'
RPL_ENDOFWHOIS = '318'
RPL_WHOISCHANNELS = '319'
RPL_WHOWASUSER = '314'
RPL_ENDOFWHOWAS = '369'
RPL_LISTSTART = '321'
RPL_LIST = '322'
RPL_LISTEND = '323'
RPL_UNIQOPIS = '325'
RPL_CHANNELMODEIS = '324'
RPL_NOTOPIC = '331'
RPL_TOPIC = '332'
RPL_INVITING = '341'
RPL_SUMMONING = '342'
RPL_INVITELIST = '346'
RPL_ENDOFINVITELIST = '347'
RPL_EXCEPTLIST = '348'
RPL_ENDOFEXCEPTLIST = '349'
RPL_VERSION = '351'
RPL_WHOREPLY = '352'
RPL_ENDOFWHO = '315'
RPL_NAMREPLY = '353'
RPL_ENDOFNAMES = '366'
RPL_LINKS = '364'
RPL_ENDOFLINKS = '365'
RPL_BANLIST = '367'
RPL_ENDOFBANLIST = '368'
RPL_INFO = '371'
RPL_ENDOFINFO = '374'
RPL_MOTDSTART = '375'
RPL_MOTD = '372'
RPL_ENDOFMOTD = '376'
RPL_YOUREOPER = '381'
RPL_REHASHING = '382'
RPL_YOURESERVICE = '383'
RPL_TIME = '391'
RPL_USERSSTART = '392'
RPL_USERS = '393'
RPL_ENDOFUSERS = '394'
RPL_NOUSERS = '395'
RPL_TRACELINK = '200'
RPL_TRACECONNECTING = '201'
RPL_TRACEHANDSHAKE = '202'
RPL_TRACEUNKNOWN = '203'
RPL_TRACEOPERATOR = '204'
RPL_TRACEUSER = '205'
RPL_TRACESERVER = '206'
RPL_TRACESERVICE = '207'
RPL_TRACENEWTYPE = '208'
RPL_TRACECLASS = '209'
RPL_TRACERECONNECT = '210'
RPL_TRACELOG = '261'
RPL_TRACEEND = '262'
RPL_STATSLINKINFO = '211'
RPL_STATSCOMMANDS = '212'
RPL_ENDOFSTATS = '219'
RPL_STATSUPTIME = '242'
RPL_STATSOLINE = '243'
RPL_UMODEIS = '221'
RPL_SERVLIST = '234'
RPL_SERVLISTEND = '235'
RPL_LUSERCLIENT = '251'
RPL_LUSEROP = '252'
RPL_LUSERUNKNOWN = '253'
RPL_LUSERCHANNELS = '254'
RPL_LUSERME = '255'
RPL_ADMINME = '256'
RPL_ADMINLOC = '257'
RPL_ADMINLOC = '258'
RPL_ADMINEMAIL = '259'
RPL_TRYAGAIN = '263'
ERR_NOSUCHNICK = '401'
ERR_NOSUCHSERVER = '402'
ERR_NOSUCHCHANNEL = '403'
ERR_CANNOTSENDTOCHAN = '404'
ERR_TOOMANYCHANNELS = '405'
ERR_WASNOSUCHNICK = '406'
ERR_TOOMANYTARGETS = '407'
ERR_NOSUCHSERVICE = '408'
ERR_NOORIGIN = '409'
ERR_NORECIPIENT = '411'
ERR_NOTEXTTOSEND = '412'
ERR_NOTOPLEVEL = '413'
ERR_WILDTOPLEVEL = '414'
ERR_BADMASK = '415'
ERR_UNKNOWNCOMMAND = '421'
ERR_NOMOTD = '422'
ERR_NOADMININFO = '423'
ERR_FILEERROR = '424'
ERR_NONICKNAMEGIVEN = '431'
ERR_ERRONEUSNICKNAME = '432'
ERR_NICKNAMEINUSE = '433'
ERR_NICKCOLLISION = '436'
ERR_UNAVAILRESOURCE = '437'
ERR_USERNOTINCHANNEL = '441'
ERR_NOTONCHANNEL = '442'
ERR_USERONCHANNEL = '443'
ERR_NOLOGIN = '444'
ERR_SUMMONDISABLED = '445'
ERR_USERSDISABLED = '446'
ERR_NOTREGISTERED = '451'
ERR_NEEDMOREPARAMS = '461'
ERR_ALREADYREGISTRED = '462'
ERR_NOPERMFORHOST = '463'
ERR_PASSWDMISMATCH = '464'
ERR_YOUREBANNEDCREEP = '465'
ERR_YOUWILLBEBANNED = '466'
ERR_KEYSET = '467'
ERR_CHANNELISFULL = '471'
ERR_UNKNOWNMODE = '472'
ERR_INVITEONLYCHAN = '473'
ERR_BANNEDFROMCHAN = '474'
ERR_BADCHANNELKEY = '475'
ERR_BADCHANMASK = '476'
ERR_NOCHANMODES = '477'
ERR_BANLISTFULL = '478'
ERR_NOPRIVILEGES = '481'
ERR_CHANOPRIVSNEEDED = '482'
ERR_CANTKILLSERVER = '483'
ERR_RESTRICTED = '484'
ERR_UNIQOPPRIVSNEEDED = '485'
ERR_NOOPERHOST = '491'
ERR_NOSERVICEHOST = '492'
ERR_UMODEUNKNOWNFLAG = '501'
ERR_USERSDONTMATCH = '502'
symbolic_to_numeric = {
    "RPL_WELCOME": '001',
    "RPL_YOURHOST": '002',
    "RPL_CREATED": '003',
    "RPL_MYINFO": '004',
    "RPL_ISUPPORT": '005',
    "RPL_BOUNCE": '010',
    "RPL_USERHOST": '302',
    "RPL_ISON": '303',
    "RPL_AWAY": '301',
    "RPL_UNAWAY": '305',
    "RPL_NOWAWAY": '306',
    "RPL_WHOISUSER": '311',
    "RPL_WHOISSERVER": '312',
    "RPL_WHOISOPERATOR": '313',
    "RPL_WHOISIDLE": '317',
    "RPL_ENDOFWHOIS": '318',
    "RPL_WHOISCHANNELS": '319',
    "RPL_WHOWASUSER": '314',
    "RPL_ENDOFWHOWAS": '369',
    "RPL_LISTSTART": '321',
    "RPL_LIST": '322',
    "RPL_LISTEND": '323',
    "RPL_UNIQOPIS": '325',
    "RPL_CHANNELMODEIS": '324',
    "RPL_NOTOPIC": '331',
    "RPL_TOPIC": '332',
    "RPL_INVITING": '341',
    "RPL_SUMMONING": '342',
    "RPL_INVITELIST": '346',
    "RPL_ENDOFINVITELIST": '347',
    "RPL_EXCEPTLIST": '348',
    "RPL_ENDOFEXCEPTLIST": '349',
    "RPL_VERSION": '351',
    "RPL_WHOREPLY": '352',
    "RPL_ENDOFWHO": '315',
    "RPL_NAMREPLY": '353',
    "RPL_ENDOFNAMES": '366',
    "RPL_LINKS": '364',
    "RPL_ENDOFLINKS": '365',
    "RPL_BANLIST": '367',
    "RPL_ENDOFBANLIST": '368',
    "RPL_INFO": '371',
    "RPL_ENDOFINFO": '374',
    "RPL_MOTDSTART": '375',
    "RPL_MOTD": '372',
    "RPL_ENDOFMOTD": '376',
    "RPL_YOUREOPER": '381',
    "RPL_REHASHING": '382',
    "RPL_YOURESERVICE": '383',
    "RPL_TIME": '391',
    "RPL_USERSSTART": '392',
    "RPL_USERS": '393',
    "RPL_ENDOFUSERS": '394',
    "RPL_NOUSERS": '395',
    "RPL_TRACELINK": '200',
    "RPL_TRACECONNECTING": '201',
    "RPL_TRACEHANDSHAKE": '202',
    "RPL_TRACEUNKNOWN": '203',
    "RPL_TRACEOPERATOR": '204',
    "RPL_TRACEUSER": '205',
    "RPL_TRACESERVER": '206',
    "RPL_TRACESERVICE": '207',
    "RPL_TRACENEWTYPE": '208',
    "RPL_TRACECLASS": '209',
    "RPL_TRACERECONNECT": '210',
    "RPL_TRACELOG": '261',
    "RPL_TRACEEND": '262',
    "RPL_STATSLINKINFO": '211',
    "RPL_STATSCOMMANDS": '212',
    "RPL_ENDOFSTATS": '219',
    "RPL_STATSUPTIME": '242',
    "RPL_STATSOLINE": '243',
    "RPL_UMODEIS": '221',
    "RPL_SERVLIST": '234',
    "RPL_SERVLISTEND": '235',
    "RPL_LUSERCLIENT": '251',
    "RPL_LUSEROP": '252',
    "RPL_LUSERUNKNOWN": '253',
    "RPL_LUSERCHANNELS": '254',
    "RPL_LUSERME": '255',
    "RPL_ADMINME": '256',
    "RPL_ADMINLOC": '257',
    "RPL_ADMINLOC": '258',
    "RPL_ADMINEMAIL": '259',
    "RPL_TRYAGAIN": '263',
    "ERR_NOSUCHNICK": '401',
    "ERR_NOSUCHSERVER": '402',
    "ERR_NOSUCHCHANNEL": '403',
    "ERR_CANNOTSENDTOCHAN": '404',
    "ERR_TOOMANYCHANNELS": '405',
    "ERR_WASNOSUCHNICK": '406',
    "ERR_TOOMANYTARGETS": '407',
    "ERR_NOSUCHSERVICE": '408',
    "ERR_NOORIGIN": '409',
    "ERR_NORECIPIENT": '411',
    "ERR_NOTEXTTOSEND": '412',
    "ERR_NOTOPLEVEL": '413',
    "ERR_WILDTOPLEVEL": '414',
    "ERR_BADMASK": '415',
    "ERR_UNKNOWNCOMMAND": '421',
    "ERR_NOMOTD": '422',
    "ERR_NOADMININFO": '423',
    "ERR_FILEERROR": '424',
    "ERR_NONICKNAMEGIVEN": '431',
    "ERR_ERRONEUSNICKNAME": '432',
    "ERR_NICKNAMEINUSE": '433',
    "ERR_NICKCOLLISION": '436',
    "ERR_UNAVAILRESOURCE": '437',
    "ERR_USERNOTINCHANNEL": '441',
    "ERR_NOTONCHANNEL": '442',
    "ERR_USERONCHANNEL": '443',
    "ERR_NOLOGIN": '444',
    "ERR_SUMMONDISABLED": '445',
    "ERR_USERSDISABLED": '446',
    "ERR_NOTREGISTERED": '451',
    "ERR_NEEDMOREPARAMS": '461',
    "ERR_ALREADYREGISTRED": '462',
    "ERR_NOPERMFORHOST": '463',
    "ERR_PASSWDMISMATCH": '464',
    "ERR_YOUREBANNEDCREEP": '465',
    "ERR_YOUWILLBEBANNED": '466',
    "ERR_KEYSET": '467',
    "ERR_CHANNELISFULL": '471',
    "ERR_UNKNOWNMODE": '472',
    "ERR_INVITEONLYCHAN": '473',
    "ERR_BANNEDFROMCHAN": '474',
    "ERR_BADCHANNELKEY": '475',
    "ERR_BADCHANMASK": '476',
    "ERR_NOCHANMODES": '477',
    "ERR_BANLISTFULL": '478',
    "ERR_NOPRIVILEGES": '481',
    "ERR_CHANOPRIVSNEEDED": '482',
    "ERR_CANTKILLSERVER": '483',
    "ERR_RESTRICTED": '484',
    "ERR_UNIQOPPRIVSNEEDED": '485',
    "ERR_NOOPERHOST": '491',
    "ERR_NOSERVICEHOST": '492',
    "ERR_UMODEUNKNOWNFLAG": '501',
    "ERR_USERSDONTMATCH": '502',
}
numeric_to_symbolic = {}
for k, v in symbolic_to_numeric.items():
    numeric_to_symbolic[v] = k
