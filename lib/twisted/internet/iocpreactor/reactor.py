# -*- test-case-name: lib.twisted.internet.test.test_iocp -*-
# Copyright (c) 2008-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import warnings, socket, sys
from lib.zope.interface import implements
from lib.twisted.internet import base, interfaces, main, error
from lib.twisted.python import log, failure
from lib.twisted.internet._dumbwin32proc import Process
from lib.twisted.internet.iocpreactor import iocpsupport as _iocp
from lib.twisted.internet.iocpreactor.const import WAIT_TIMEOUT
from lib.twisted.internet.iocpreactor import tcp, udp
try:
    from lib.twisted.protocols.tls import TLSMemoryBIOFactory
except ImportError:
    TLSMemoryBIOFactory = None
    _extraInterfaces = ()
    warnings.warn(
        "pyOpenSSL 0.10 or newer is required for SSL support in iocpreactor. "
        "It is missing, so the reactor will not support SSL APIs.")
else:
    _extraInterfaces = (interfaces.IReactorSSL,)
from lib.twisted.python.compat import set
MAX_TIMEOUT = 2000 # 2 seconds, see doIteration for explanation
EVENTS_PER_LOOP = 1000 # XXX: what's a good value here?
KEY_NORMAL, KEY_WAKEUP = range(2)
_NO_GETHANDLE = error.ConnectionFdescWentAway(
                    'Handler has no getFileHandle method')
_NO_FILEDESC = error.ConnectionFdescWentAway('Filedescriptor went away')

class IOCPReactor(base._SignalReactorMixin, base.ReactorBase):
    implements(interfaces.IReactorTCP, interfaces.IReactorUDP,
               interfaces.IReactorMulticast, interfaces.IReactorProcess,
               *_extraInterfaces)
    port = None
    def __init__(self):
        base.ReactorBase.__init__(self)
        self.port = _iocp.CompletionPort()
        self.handles = set()

    def addActiveHandle(self, handle):
        self.handles.add(handle)

    def removeActiveHandle(self, handle):
        self.handles.discard(handle)

    def doIteration(self, timeout):
        processed_events = 0
        if timeout is None:
            timeout = MAX_TIMEOUT
        else:
            timeout = min(MAX_TIMEOUT, int(1000*timeout))
        rc, bytes, key, evt = self.port.getEvent(timeout)
        while processed_events < EVENTS_PER_LOOP:
            if rc == WAIT_TIMEOUT:
                break
            if key != KEY_WAKEUP:
                assert key == KEY_NORMAL
                if not evt.ignore:
                    log.callWithLogger(evt.owner, self._callEventCallback,
                                       rc, bytes, evt)
                    processed_events += 1
            rc, bytes, key, evt = self.port.getEvent(0)

    def _callEventCallback(self, rc, bytes, evt):
        owner = evt.owner
        why = None
        try:
            evt.callback(rc, bytes, evt)
            handfn = getattr(owner, 'getFileHandle', None)
            if not handfn:
                why = _NO_GETHANDLE
            elif handfn() == -1:
                why = _NO_FILEDESC
            if why:
                return
        except:
            why = sys.exc_info()[1]
            log.err()
        if why:
            owner.loseConnection(failure.Failure(why))

    def installWaker(self):
        pass

    def wakeUp(self):
        self.port.postEvent(0, KEY_WAKEUP, None)

    def registerHandle(self, handle):
        self.port.addHandle(handle, KEY_NORMAL)

    def createSocket(self, af, stype):
        skt = socket.socket(af, stype)
        self.registerHandle(skt.fileno())
        return skt

    def listenTCP(self, port, factory, backlog=50, interface=''):
        p = tcp.Port(port, factory, backlog, interface, self)
        p.startListening()
        return p

    def connectTCP(self, host, port, factory, timeout=30, bindAddress=None):
        c = tcp.Connector(host, port, factory, timeout, bindAddress, self)
        c.connect()
        return c

    if TLSMemoryBIOFactory is not None:
        def listenSSL(self, port, factory, contextFactory, backlog=50, interface=''):
            return self.listenTCP(
                port,
                TLSMemoryBIOFactory(contextFactory, False, factory),
                backlog, interface)

        def connectSSL(self, host, port, factory, contextFactory, timeout=30, bindAddress=None):
            return self.connectTCP(
                host, port,
                TLSMemoryBIOFactory(contextFactory, True, factory),
                timeout, bindAddress)
    else:
        def listenSSL(self, port, factory, contextFactory, backlog=50, interface=''):
            raise NotImplementedError(
                "pyOpenSSL 0.10 or newer is required for SSL support in "
                "iocpreactor. It is missing, so the reactor does not support "
                "SSL APIs.")

        def connectSSL(self, host, port, factory, contextFactory, timeout=30, bindAddress=None):
            raise NotImplementedError(
                "pyOpenSSL 0.10 or newer is required for SSL support in "
                "iocpreactor. It is missing, so the reactor does not support "
                "SSL APIs.")

    def listenUDP(self, port, protocol, interface='', maxPacketSize=8192):
        p = udp.Port(port, protocol, interface, maxPacketSize, self)
        p.startListening()
        return p

    def listenMulticast(self, port, protocol, interface='', maxPacketSize=8192,
                        listenMultiple=False):
        p = udp.MulticastPort(port, protocol, interface, maxPacketSize, self,
                              listenMultiple)
        p.startListening()
        return p

    def spawnProcess(self, processProtocol, executable, args=(), env={},
                     path=None, uid=None, gid=None, usePTY=0, childFDs=None):
        if uid is not None:
            raise ValueError("Setting UID is unsupported on this platform.")
        if gid is not None:
            raise ValueError("Setting GID is unsupported on this platform.")
        if usePTY:
            raise ValueError("PTYs are unsupported on this platform.")
        if childFDs is not None:
            raise ValueError(
                "Custom child file descriptor mappings are unsupported on "
                "this platform.")
        args, env = self._checkProcessArgs(args, env)
        return Process(self, processProtocol, executable, args, env, path)

    def removeAll(self):
        res = list(self.handles)
        self.handles.clear()
        return res

def install():
    r = IOCPReactor()
    main.installReactor(r)

__all__ = ['IOCPReactor', 'install']

