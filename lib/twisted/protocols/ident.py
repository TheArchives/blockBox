# -*- test-case-name: lib.twisted.test.test_ident -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
from __future__ import generators
import struct
from lib.twisted.internet import defer
from lib.twisted.protocols import basic
from lib.twisted.python import log, failure
_MIN_PORT = 1
_MAX_PORT = 2 ** 16 - 1

class IdentError(Exception):
    identDescription = 'UNKNOWN-ERROR'

    def __str__(self):
        return self.identDescription

class NoUser(IdentError):
    identDescription = 'NO-USER'

class InvalidPort(IdentError):
    identDescription = 'INVALID-PORT'

class HiddenUser(IdentError):
    identDescription = 'HIDDEN-USER'

class IdentServer(basic.LineOnlyReceiver):
    def lineReceived(self, line):
        parts = line.split(',')
        if len(parts) != 2:
            self.invalidQuery()
        else:
            try:
                portOnServer, portOnClient = map(int, parts)
            except ValueError:
                self.invalidQuery()
            else:
                if _MIN_PORT <= portOnServer <= _MAX_PORT and _MIN_PORT <= portOnClient <= _MAX_PORT:
                    self.validQuery(portOnServer, portOnClient)
                else:
                    self._ebLookup(failure.Failure(InvalidPort()), portOnServer, portOnClient)

    def invalidQuery(self):
        self.transport.loseConnection()

    def validQuery(self, portOnServer, portOnClient):
        serverAddr = self.transport.getHost().host, portOnServer
        clientAddr = self.transport.getPeer().host, portOnClient
        defer.maybeDeferred(self.lookup, serverAddr, clientAddr
            ).addCallback(self._cbLookup, portOnServer, portOnClient
            ).addErrback(self._ebLookup, portOnServer, portOnClient
            )

    def _cbLookup(self, (sysName, userId), sport, cport):
        self.sendLine('%d, %d : USERID : %s : %s' % (sport, cport, sysName, userId))

    def _ebLookup(self, failure, sport, cport):
        if failure.check(IdentError):
            self.sendLine('%d, %d : ERROR : %s' % (sport, cport, failure.value))
        else:
            log.err(failure)
            self.sendLine('%d, %d : ERROR : %s' % (sport, cport, IdentError(failure.value)))

    def lookup(self, serverAddress, clientAddress):
        raise IdentError()

class ProcServerMixin:
    SYSTEM_NAME = 'LINUX'

    try:
        from pwd import getpwuid
        def getUsername(self, uid, getpwuid=getpwuid):
            return getpwuid(uid)[0]
        del getpwuid
    except ImportError:
        def getUsername(self, uid):
            raise IdentError()

    def entries(self):
        f = file('/proc/net/tcp')
        f.readline()
        for L in f:
            yield L.strip()

    def dottedQuadFromHexString(self, hexstr):
        return '.'.join(map(str, struct.unpack('4B', struct.pack('=L', int(hexstr, 16)))))

    def unpackAddress(self, packed):
        addr, port = packed.split(':')
        addr = self.dottedQuadFromHexString(addr)
        port = int(port, 16)
        return addr, port

    def parseLine(self, line):
        parts = line.strip().split()
        localAddr, localPort = self.unpackAddress(parts[1])
        remoteAddr, remotePort = self.unpackAddress(parts[2])
        uid = int(parts[7])
        return (localAddr, localPort), (remoteAddr, remotePort), uid

    def lookup(self, serverAddress, clientAddress):
        for ent in self.entries():
            localAddr, remoteAddr, uid = self.parseLine(ent)
            if remoteAddr == clientAddress and localAddr[1] == serverAddress[1]:
                return (self.SYSTEM_NAME, self.getUsername(uid))
        raise NoUser()

class IdentClient(basic.LineOnlyReceiver):
    errorTypes = (IdentError, NoUser, InvalidPort, HiddenUser)

    def __init__(self):
        self.queries = []

    def lookup(self, portOnServer, portOnClient):
        self.queries.append((defer.Deferred(), portOnServer, portOnClient))
        if len(self.queries) > 1:
            return self.queries[-1][0]

        self.sendLine('%d, %d' % (portOnServer, portOnClient))
        return self.queries[-1][0]

    def lineReceived(self, line):
        if not self.queries:
            log.msg("Unexpected server response: %r" % (line,))
        else:
            d, _, _ = self.queries.pop(0)
            self.parseResponse(d, line)
            if self.queries:
                self.sendLine('%d, %d' % (self.queries[0][1], self.queries[0][2]))

    def connectionLost(self, reason):
        for q in self.queries:
            q[0].errback(IdentError(reason))
        self.queries = []

    def parseResponse(self, deferred, line):
        parts = line.split(':', 2)
        if len(parts) != 3:
            deferred.errback(IdentError(line))
        else:
            ports, type, addInfo = map(str.strip, parts)
            if type == 'ERROR':
                for et in self.errorTypes:
                    if et.identDescription == addInfo:
                        deferred.errback(et(line))
                        return
                deferred.errback(IdentError(line))
            else:
                deferred.callback((type, addInfo))

__all__ = ['IdentError', 'NoUser', 'InvalidPort', 'HiddenUser',
           'IdentServer', 'IdentClient',
           'ProcServerMixin']
