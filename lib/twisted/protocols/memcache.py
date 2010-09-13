# -*- test-case-name: lib.twisted.test.test_memcache -*-
# Copyright (c) 2007-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
try:
    from collections import deque
except ImportError:
    class deque(list):
        def popleft(self):
            return self.pop(0)
from lib.twisted.protocols.basic import LineReceiver
from lib.twisted.protocols.policies import TimeoutMixin
from lib.twisted.internet.defer import Deferred, fail, TimeoutError
from lib.twisted.python import log
DEFAULT_PORT = 11211

class NoSuchCommand(Exception):

class ClientError(Exception):

class ServerError(Exception):

class Command(object):
    def __init__(self, command, **kwargs):
        self.command = command
        self._deferred = Deferred()
        for k, v in kwargs.items():
            setattr(self, k, v)

    def success(self, value):
        self._deferred.callback(value)

    def fail(self, error):
        self._deferred.errback(error)

class MemCacheProtocol(LineReceiver, TimeoutMixin):
    MAX_KEY_LENGTH = 250
    _disconnected = False

    def __init__(self, timeOut=60):
        self._current = deque()
        self._lenExpected = None
        self._getBuffer = None
        self._bufferLength = None
        self.persistentTimeOut = self.timeOut = timeOut

    def _cancelCommands(self, reason):
        while self._current:
            cmd = self._current.popleft()
            cmd.fail(reason)

    def timeoutConnection(self):
        self._cancelCommands(TimeoutError("Connection timeout"))
        self.transport.loseConnection()

    def connectionLost(self, reason):
        self._disconnected = True
        self._cancelCommands(reason)
        LineReceiver.connectionLost(self, reason)

    def sendLine(self, line):
        if not self._current:
            self.setTimeout(self.persistentTimeOut)
        LineReceiver.sendLine(self, line)

    def rawDataReceived(self, data):
        self.resetTimeout()
        self._getBuffer.append(data)
        self._bufferLength += len(data)
        if self._bufferLength >= self._lenExpected + 2:
            data = "".join(self._getBuffer)
            buf = data[:self._lenExpected]
            rem = data[self._lenExpected + 2:]
            val = buf
            self._lenExpected = None
            self._getBuffer = None
            self._bufferLength = None
            cmd = self._current[0]
            if cmd.multiple:
                flags, cas = cmd.values[cmd.currentKey]
                cmd.values[cmd.currentKey] = (flags, cas, val)
            else:
                cmd.value = val
            self.setLineMode(rem)

    def cmd_STORED(self):
        self._current.popleft().success(True)

    def cmd_NOT_STORED(self):
        self._current.popleft().success(False)

    def cmd_END(self):
        cmd = self._current.popleft()
        if cmd.command == "get":
            if cmd.multiple:
                values = dict([(key, val[::2]) for key, val in
                               cmd.values.iteritems()])
                cmd.success(values)
            else:
                cmd.success((cmd.flags, cmd.value))
        elif cmd.command == "gets":
            if cmd.multiple:
                cmd.success(cmd.values)
            else:
                cmd.success((cmd.flags, cmd.cas, cmd.value))
        elif cmd.command == "stats":
            cmd.success(cmd.values)

    def cmd_NOT_FOUND(self):
        self._current.popleft().success(False)

    def cmd_VALUE(self, line):
        cmd = self._current[0]
        if cmd.command == "get":
            key, flags, length = line.split()
            cas = ""
        else:
            key, flags, length, cas = line.split()
        self._lenExpected = int(length)
        self._getBuffer = []
        self._bufferLength = 0
        if cmd.multiple:
            if key not in cmd.keys:
                raise RuntimeError("Unexpected commands answer.")
            cmd.currentKey = key
            cmd.values[key] = [int(flags), cas]
        else:
            if cmd.key != key:
                raise RuntimeError("Unexpected commands answer.")
            cmd.flags = int(flags)
            cmd.cas = cas
        self.setRawMode()

    def cmd_STAT(self, line):
        cmd = self._current[0]
        key, val = line.split(" ", 1)
        cmd.values[key] = val

    def cmd_VERSION(self, versionData):
        self._current.popleft().success(versionData)

    def cmd_ERROR(self):
        log.err("Non-existent command sent.")
        cmd = self._current.popleft()
        cmd.fail(NoSuchCommand())

    def cmd_CLIENT_ERROR(self, errText):
        log.err("Invalid input: %s" % (errText,))
        cmd = self._current.popleft()
        cmd.fail(ClientError(errText))

    def cmd_SERVER_ERROR(self, errText):
        log.err("Server error: %s" % (errText,))
        cmd = self._current.popleft()
        cmd.fail(ServerError(errText))

    def cmd_DELETED(self):
        self._current.popleft().success(True)

    def cmd_OK(self):
        self._current.popleft().success(True)

    def cmd_EXISTS(self):
        self._current.popleft().success(False)

    def lineReceived(self, line):
        self.resetTimeout()
        token = line.split(" ", 1)[0]
        cmd = getattr(self, "cmd_%s" % (token,), None)
        if cmd is not None:
            args = line.split(" ", 1)[1:]
            if args:
                cmd(args[0])
            else:
                cmd()
        else:
            line = line.replace(" ", "_")
            cmd = getattr(self, "cmd_%s" % (line,), None)
            if cmd is not None:
                cmd()
            else:
                cmd = self._current.popleft()
                val = int(line)
                cmd.success(val)
        if not self._current:
            self.setTimeout(None)

    def increment(self, key, val=1):
        return self._incrdecr("incr", key, val)

    def decrement(self, key, val=1):
        return self._incrdecr("decr", key, val)

    def _incrdecr(self, cmd, key, val):
        if self._disconnected:
            return fail(RuntimeError("not connected"))
        if not isinstance(key, str):
            return fail(ClientError(
                "Invalid type for key: %s, expecting a string" % (type(key),)))
        if len(key) > self.MAX_KEY_LENGTH:
            return fail(ClientError("Key too long"))
        fullcmd = "%s %s %d" % (cmd, key, int(val))
        self.sendLine(fullcmd)
        cmdObj = Command(cmd, key=key)
        self._current.append(cmdObj)
        return cmdObj._deferred

    def replace(self, key, val, flags=0, expireTime=0):
        return self._set("replace", key, val, flags, expireTime, "")

    def add(self, key, val, flags=0, expireTime=0):
        return self._set("add", key, val, flags, expireTime, "")

    def set(self, key, val, flags=0, expireTime=0):
        return self._set("set", key, val, flags, expireTime, "")

    def checkAndSet(self, key, val, cas, flags=0, expireTime=0):
        return self._set("cas", key, val, flags, expireTime, cas)

    def _set(self, cmd, key, val, flags, expireTime, cas):
        if self._disconnected:
            return fail(RuntimeError("not connected"))
        if not isinstance(key, str):
            return fail(ClientError(
                "Invalid type for key: %s, expecting a string" % (type(key),)))
        if len(key) > self.MAX_KEY_LENGTH:
            return fail(ClientError("Key too long"))
        if not isinstance(val, str):
            return fail(ClientError(
                "Invalid type for value: %s, expecting a string" %
                (type(val),)))
        if cas:
            cas = " " + cas
        length = len(val)
        fullcmd = "%s %s %d %d %d%s" % (
            cmd, key, flags, expireTime, length, cas)
        self.sendLine(fullcmd)
        self.sendLine(val)
        cmdObj = Command(cmd, key=key, flags=flags, length=length)
        self._current.append(cmdObj)
        return cmdObj._deferred

    def append(self, key, val):
        return self._set("append", key, val, 0, 0, "")

    def prepend(self, key, val):
        return self._set("prepend", key, val, 0, 0, "")

    def get(self, key, withIdentifier=False):
        return self._get([key], withIdentifier, False)

    def getMultiple(self, keys, withIdentifier=False):
        return self._get(keys, withIdentifier, True)

    def _get(self, keys, withIdentifier, multiple):
        if self._disconnected:
            return fail(RuntimeError("not connected"))
        for key in keys:
            if not isinstance(key, str):
                return fail(ClientError(
                    "Invalid type for key: %s, expecting a string" % (type(key),)))
            if len(key) > self.MAX_KEY_LENGTH:
                return fail(ClientError("Key too long"))
        if withIdentifier:
            cmd = "gets"
        else:
            cmd = "get"
        fullcmd = "%s %s" % (cmd, " ".join(keys))
        self.sendLine(fullcmd)
        if multiple:
            values = dict([(key, (0, "", None)) for key in keys])
            cmdObj = Command(cmd, keys=keys, values=values, multiple=True)
        else:
            cmdObj = Command(cmd, key=keys[0], value=None, flags=0, cas="",
                             multiple=False)
        self._current.append(cmdObj)
        return cmdObj._deferred

    def stats(self, arg=None):
        if arg:
            cmd = "stats " + arg
        else:
            cmd = "stats"
        if self._disconnected:
            return fail(RuntimeError("not connected"))
        self.sendLine(cmd)
        cmdObj = Command("stats", values={})
        self._current.append(cmdObj)
        return cmdObj._deferred

    def version(self):
        if self._disconnected:
            return fail(RuntimeError("not connected"))
        self.sendLine("version")
        cmdObj = Command("version")
        self._current.append(cmdObj)
        return cmdObj._deferred

    def delete(self, key):
        if self._disconnected:
            return fail(RuntimeError("not connected"))
        if not isinstance(key, str):
            return fail(ClientError(
                "Invalid type for key: %s, expecting a string" % (type(key),)))
        self.sendLine("delete %s" % key)
        cmdObj = Command("delete", key=key)
        self._current.append(cmdObj)
        return cmdObj._deferred

    def flushAll(self):
        if self._disconnected:
            return fail(RuntimeError("not connected"))
        self.sendLine("flush_all")
        cmdObj = Command("flush_all")
        self._current.append(cmdObj)
        return cmdObj._deferred

__all__ = ["MemCacheProtocol", "DEFAULT_PORT", "NoSuchCommand", "ClientError",
           "ServerError"]
