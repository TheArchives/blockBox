# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import time, struct
from lib.zope.interface import implements
from lib.twisted.internet import protocol, interfaces

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        self.transport.write(data)

class Discard(protocol.Protocol):
    def dataReceived(self, data):
        pass

class Chargen(protocol.Protocol):
    noise = r'@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&?'
    implements(interfaces.IProducer)

    def connectionMade(self):
        self.transport.registerProducer(self, 0)

    def resumeProducing(self):
        self.transport.write(self.noise)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class QOTD(protocol.Protocol):
    def connectionMade(self):
        self.transport.write(self.getQuote())
        self.transport.loseConnection()

    def getQuote(self):
        return "An apple a day keeps the doctor away.\r\n"

class Who(protocol.Protocol):
    def connectionMade(self):
        self.transport.write(self.getUsers())
        self.transport.loseConnection()
    
    def getUsers(self):
        return "root\r\n"

class Daytime(protocol.Protocol):
    def connectionMade(self):
        self.transport.write(time.asctime(time.gmtime(time.time())) + '\r\n')
        self.transport.loseConnection()

class Time(protocol.Protocol):
    def connectionMade(self):
        result = struct.pack("!i", int(time.time()))
        self.transport.write(result)
        self.transport.loseConnection()

