# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

from lib.zope.interface import Interface, Attribute
from lib.twisted.python.deprecate import deprecatedModuleAttribute
from lib.twisted.python.versions import Version


class IAddress(Interface):

### Reactor Interfaces

class IConnector(Interface):

    def stopConnecting():

    def disconnect():

    def connect():

    def getDestination():

class IResolverSimple(Interface):

    def getHostByName(name, timeout = (1, 3, 11, 45)):

class IResolver(IResolverSimple):
    def lookupRecord(name, cls, type, timeout = 10):

    def query(query, timeout = 10):

    def lookupAddress(name, timeout = 10):

    def lookupAddress6(name, timeout = 10):

    def lookupIPV6Address(name, timeout = 10):

    def lookupMailExchange(name, timeout = 10):

    def lookupNameservers(name, timeout = 10):

    def lookupCanonicalName(name, timeout = 10):

    def lookupMailBox(name, timeout = 10):

    def lookupMailGroup(name, timeout = 10):

    def lookupMailRename(name, timeout = 10):

    def lookupPointer(name, timeout = 10):

    def lookupAuthority(name, timeout = 10):

    def lookupNull(name, timeout = 10):

    def lookupWellKnownServices(name, timeout = 10):

    def lookupHostInfo(name, timeout = 10):

    def lookupMailboxInfo(name, timeout = 10):

    def lookupText(name, timeout = 10):

    def lookupResponsibility(name, timeout = 10):

    def lookupAFSDatabase(name, timeout = 10):

    def lookupService(name, timeout = 10):

    def lookupAllRecords(name, timeout = 10):

    def lookupZone(name, timeout = 10):


class IReactorArbitrary(Interface):

    deprecatedModuleAttribute(
        Version("Twisted", 10, 1, 0),
        "See IReactorFDSet.",
        __name__,
        "IReactorArbitrary")


    def listenWith(portType, *args, **kw):

    def connectWith(connectorType, *args, **kw):

_IReactorArbitrary = IReactorArbitrary



class IReactorTCP(Interface):

    def listenTCP(port, factory, backlog=50, interface=''):

    def connectTCP(host, port, factory, timeout=30, bindAddress=None):

class IReactorSSL(Interface):

    def connectSSL(host, port, factory, contextFactory, timeout=30, bindAddress=None):

    def listenSSL(port, factory, contextFactory, backlog=50, interface=''):

class IReactorUNIX(Interface):

    def connectUNIX(address, factory, timeout=30, checkPID=0):

    def listenUNIX(address, factory, backlog=50, mode=0666, wantPID=0):

class IReactorUNIXDatagram(Interface):

    def connectUNIXDatagram(address, protocol, maxPacketSize=8192, mode=0666, bindAddress=None):

    def listenUNIXDatagram(address, protocol, maxPacketSize=8192, mode=0666):

class IReactorUDP(Interface):

    def listenUDP(port, protocol, interface='', maxPacketSize=8192):

class IReactorMulticast(Interface):

    def listenMulticast(port, protocol, interface='', maxPacketSize=8192,
                        listenMultiple=False):

class IReactorProcess(Interface):

    def spawnProcess(processProtocol, executable, args=(), env={}, path=None,
                     uid=None, gid=None, usePTY=0, childFDs=None):

class IReactorTime(Interface):

    def seconds():

    def callLater(delay, callable, *args, **kw):

    def cancelCallLater(callID):

    def getDelayedCalls():

class IDelayedCall(Interface):

    def getTime():

    def cancel():

    def delay(secondsLater):

    def reset(secondsFromNow):

    def active():

class IReactorThreads(Interface):

    def getThreadPool():

    def callInThread(callable, *args, **kwargs):

    def callFromThread(callable, *args, **kw):

    def suggestThreadPoolSize(size):


class IReactorCore(Interface):

    running = Attribute(
        "A C{bool} which is C{True} from I{during startup} to "
        "I{during shutdown} and C{False} the rest of the time.")


    def resolve(name, timeout=10):

    def run():

    def stop():

    def crash():

    def iterate(delay=0):

    def fireSystemEvent(eventType):

    def addSystemEventTrigger(phase, eventType, callable, *args, **kw):

    def removeSystemEventTrigger(triggerID):

    def callWhenRunning(callable, *args, **kw):

class IReactorPluggableResolver(Interface):

    def installResolver(resolver):

class IReactorFDSet(Interface):

    def addReader(reader):

    def addWriter(writer):

    def removeReader(reader):

    def removeWriter(writer):

    def removeAll():

    def getReaders():

    def getWriters():

class IListeningPort(Interface):

    def startListening():

    def stopListening():

    def getHost():

class ILoggingContext(Interface):

    def logPrefix():

class IFileDescriptor(ILoggingContext):

    def fileno():

    def connectionLost(reason):

class IReadDescriptor(IFileDescriptor):

    def doRead():
        """
        Some data is available for reading on your descriptor.
        """


class IWriteDescriptor(IFileDescriptor):

    def doWrite():


class IReadWriteDescriptor(IReadDescriptor, IWriteDescriptor):

class IHalfCloseableDescriptor(Interface):

    def writeConnectionLost(reason):

    def readConnectionLost(reason):

class ISystemHandle(Interface):

    def getHandle():

class IConsumer(Interface):

    def registerProducer(producer, streaming):

    def unregisterProducer():

    def write(data):

class IFinishableConsumer(IConsumer):

    def finish():

class IProducer(Interface):

    def stopProducing():

class IPushProducer(IProducer):

    def pauseProducing():

    def resumeProducing():

class IPullProducer(IProducer):

    def resumeProducing():

class IProtocol(Interface):

    def dataReceived(data):

    def connectionLost(reason):

    def makeConnection(transport):

    def connectionMade():

class IProcessProtocol(Interface):

    def makeConnection(process):

    def childDataReceived(childFD, data):

    def childConnectionLost(childFD):

    def processExited(reason):

    def processEnded(reason):

class IHalfCloseableProtocol(Interface):

    def readConnectionLost():

    def writeConnectionLost():

class IProtocolFactory(Interface):

    def buildProtocol(addr):

    def doStart():

    def doStop():

class ITransport(Interface):

    def write(data):

    def writeSequence(data):

    def loseConnection():

    def getPeer():

    def getHost():

class ITCPTransport(ITransport):

    def loseWriteConnection():

    def getTcpNoDelay():

    def setTcpNoDelay(enabled):

    def getTcpKeepAlive():

    def setTcpKeepAlive(enabled):

    def getHost():

    def getPeer():

class ITLSTransport(ITCPTransport):

    def startTLS(contextFactory):

class ISSLTransport(ITCPTransport):

    def getPeerCertificate():

class IProcessTransport(ITransport):

    pid = Attribute(
        "From before L{IProcessProtocol.makeConnection} is called to before "
        "L{IProcessProtocol.processEnded} is called, C{pid} is an L{int} "
        "giving the platform process ID of this process.  C{pid} is L{None} "
        "at all other times.")

    def closeStdin():

    def closeStdout():

    def closeStderr():

    def closeChildFD(descriptor):

    def writeToChild(childFD, data):

    def loseConnection():

    def signalProcess(signalID):

class IServiceCollection(Interface):

    def getServiceNamed(serviceName):

    def addService(service):

    def removeService(service):

class IUDPTransport(Interface):

    def write(packet, addr=None):

    def connect(host, port):

    def getHost():

    def stopListening():

class IUNIXDatagramTransport(Interface):

    def write(packet, address):

    def getHost():

class IUNIXDatagramConnectedTransport(Interface):

    def write(packet):

    def getHost():

    def getPeer():

class IMulticastTransport(Interface):

    def getOutgoingInterface():

    def setOutgoingInterface(addr):

    def getLoopbackMode():

    def setLoopbackMode(mode):

    def getTTL():

    def setTTL(ttl):

    def joinGroup(addr, interface=""):

    def leaveGroup(addr, interface=""):

class IStreamClientEndpoint(Interface):

    def connect(protocolFactory):

class IStreamServerEndpoint(Interface):

    def listen(protocolFactory):
