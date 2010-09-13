# -*- test-case-name: lib.twisted.test.test_internet -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

import socket # needed only for sync-dns
from lib.zope.interface import implements, classImplements

import sys
import warnings
from heapq import heappush, heappop, heapify

import traceback

from lib.twisted.python.compat import set
from lib.twisted.python.util import unsignedID
from lib.twisted.internet.interfaces import IReactorCore, IReactorTime, IReactorThreads
from lib.twisted.internet.interfaces import IResolverSimple, IReactorPluggableResolver
from lib.twisted.internet.interfaces import IConnector, IDelayedCall
from lib.twisted.internet import fdesc, main, error, abstract, defer, threads
from lib.twisted.python import log, failure, reflect
from lib.twisted.python.runtime import seconds as runtimeSeconds, platform
from lib.twisted.internet.defer import Deferred, DeferredList
from lib.twisted.persisted import styles
from lib.twisted.python import threadable

class DelayedCall(styles.Ephemeral):

    implements(IDelayedCall)
    debug = False
    _str = None

    def __init__(self, time, func, args, kw, cancel, reset,
                 seconds=runtimeSeconds):
        self.time, self.func, self.args, self.kw = time, func, args, kw
        self.resetter = reset
        self.canceller = cancel
        self.seconds = seconds
        self.cancelled = self.called = 0
        self.delayed_time = 0
        if self.debug:
            self.creator = traceback.format_stack()[:-2]

    def getTime(self):
        return self.time + self.delayed_time

    def cancel(self):
        if self.cancelled:
            raise error.AlreadyCancelled
        elif self.called:
            raise error.AlreadyCalled
        else:
            self.canceller(self)
            self.cancelled = 1
            if self.debug:
                self._str = str(self)
            del self.func, self.args, self.kw

    def reset(self, secondsFromNow):
        if self.cancelled:
            raise error.AlreadyCancelled
        elif self.called:
            raise error.AlreadyCalled
        else:
            newTime = self.seconds() + secondsFromNow
            if newTime < self.time:
                self.delayed_time = 0
                self.time = newTime
                self.resetter(self)
            else:
                self.delayed_time = newTime - self.time

    def delay(self, secondsLater):
        if self.cancelled:
            raise error.AlreadyCancelled
        elif self.called:
            raise error.AlreadyCalled
        else:
            self.delayed_time += secondsLater
            if self.delayed_time < 0:
                self.activate_delay()
                self.resetter(self)

    def activate_delay(self):
        self.time += self.delayed_time
        self.delayed_time = 0

    def active(self):
        return not (self.cancelled or self.called)

    def __le__(self, other):
        return self.time <= other.time


    def __lt__(self, other):
        return self.time < other.time


    def __str__(self):
        if self._str is not None:
            return self._str
        if hasattr(self, 'func'):
            if hasattr(self.func, 'func_name'):
                func = self.func.func_name
                if hasattr(self.func, 'im_class'):
                    func = self.func.im_class.__name__ + '.' + func
            else:
                func = reflect.safe_repr(self.func)
        else:
            func = None

        now = self.seconds()
        L = ["<DelayedCall 0x%x [%ss] called=%s cancelled=%s" % (
                unsignedID(self), self.time - now, self.called,
                self.cancelled)]
        if func is not None:
            L.extend((" ", func, "("))
            if self.args:
                L.append(", ".join([reflect.safe_repr(e) for e in self.args]))
                if self.kw:
                    L.append(", ")
            if self.kw:
                L.append(", ".join(['%s=%s' % (k, reflect.safe_repr(v)) for (k, v) in self.kw.iteritems()]))
            L.append(")")

        if self.debug:
            L.append("\n\ntraceback at creation: \n\n%s" % ('    '.join(self.creator)))
        L.append('>')

        return "".join(L)

class ThreadedResolver(object):
    implements(IResolverSimple)

    def __init__(self, reactor):
        self.reactor = reactor
        self._runningQueries = {}

    def _fail(self, name, err):
        err = error.DNSLookupError("address %r not found: %s" % (name, err))
        return failure.Failure(err)

    def _cleanup(self, name, lookupDeferred):
        userDeferred, cancelCall = self._runningQueries[lookupDeferred]
        del self._runningQueries[lookupDeferred]
        userDeferred.errback(self._fail(name, "timeout error"))

    def _checkTimeout(self, result, name, lookupDeferred):
        try:
            userDeferred, cancelCall = self._runningQueries[lookupDeferred]
        except KeyError:
            pass
        else:
            del self._runningQueries[lookupDeferred]
            cancelCall.cancel()

            if isinstance(result, failure.Failure):
                userDeferred.errback(self._fail(name, result.getErrorMessage()))
            else:
                userDeferred.callback(result)

    def getHostByName(self, name, timeout = (1, 3, 11, 45)):
        if timeout:
            timeoutDelay = sum(timeout)
        else:
            timeoutDelay = 60
        userDeferred = defer.Deferred()
        lookupDeferred = threads.deferToThreadPool(
            self.reactor, self.reactor.getThreadPool(),
            socket.gethostbyname, name)
        cancelCall = self.reactor.callLater(
            timeoutDelay, self._cleanup, name, lookupDeferred)
        self._runningQueries[lookupDeferred] = (userDeferred, cancelCall)
        lookupDeferred.addBoth(self._checkTimeout, name, lookupDeferred)
        return userDeferred

class BlockingResolver:
    implements(IResolverSimple)

    def getHostByName(self, name, timeout = (1, 3, 11, 45)):
        try:
            address = socket.gethostbyname(name)
        except socket.error:
            msg = "address %r not found" % (name,)
            err = error.DNSLookupError(msg)
            return defer.fail(err)
        else:
            return defer.succeed(address)

class _ThreePhaseEvent(object):

    def __init__(self):
        self.before = []
        self.during = []
        self.after = []
        self.state = 'BASE'

    def addTrigger(self, phase, callable, *args, **kwargs):
        if phase not in ('before', 'during', 'after'):
            raise KeyError("invalid phase")
        getattr(self, phase).append((callable, args, kwargs))
        return phase, callable, args, kwargs

    def removeTrigger(self, handle):
        return getattr(self, 'removeTrigger_' + self.state)(handle)

    def removeTrigger_BASE(self, handle):
        try:
            phase, callable, args, kwargs = handle
        except (TypeError, ValueError), e:
            raise ValueError("invalid trigger handle")
        else:
            if phase not in ('before', 'during', 'after'):
                raise KeyError("invalid phase")
            getattr(self, phase).remove((callable, args, kwargs))

    def removeTrigger_BEFORE(self, handle):
        phase, callable, args, kwargs = handle
        if phase != 'before':
            return self.removeTrigger_BASE(handle)
        if (callable, args, kwargs) in self.finishedBefore:
            warnings.warn(
                "Removing already-fired system event triggers will raise an "
                "exception in a future version of Twisted.",
                category=DeprecationWarning,
                stacklevel=3)
        else:
            self.removeTrigger_BASE(handle)

    def fireEvent(self):
        self.state = 'BEFORE'
        self.finishedBefore = []
        beforeResults = []
        while self.before:
            callable, args, kwargs = self.before.pop(0)
            self.finishedBefore.append((callable, args, kwargs))
            try:
                result = callable(*args, **kwargs)
            except:
                log.err()
            else:
                if isinstance(result, Deferred):
                    beforeResults.append(result)
        DeferredList(beforeResults).addCallback(self._continueFiring)

    def _continueFiring(self, ignored):
        self.state = 'BASE'
        self.finishedBefore = []
        for phase in self.during, self.after:
            while phase:
                callable, args, kwargs = phase.pop(0)
                try:
                    callable(*args, **kwargs)
                except:
                    log.err()

class ReactorBase(object):
    implements(IReactorCore, IReactorTime, IReactorPluggableResolver)

    _stopped = True
    installed = False
    usingThreads = False
    resolver = BlockingResolver()

    __name__ = "lib.twisted.internet.reactor"

    def __init__(self):
        self.threadCallQueue = []
        self._eventTriggers = {}
        self._pendingTimedCalls = []
        self._newTimedCalls = []
        self._cancellations = 0
        self.running = False
        self._started = False
        self._justStopped = False
        self._internalReaders = set()
        self.waker = None
        self.addSystemEventTrigger(
            'during', 'startup', self._reallyStartRunning)
        self.addSystemEventTrigger('during', 'shutdown', self.crash)
        self.addSystemEventTrigger('during', 'shutdown', self.disconnectAll)
        if platform.supportsThreads():
            self._initThreads()
        self.installWaker()

    # override in subclasses

    _lock = None

    def installWaker(self):
        raise NotImplementedError(
            reflect.qual(self.__class__) + " did not implement installWaker")

    def installResolver(self, resolver):
        assert IResolverSimple.providedBy(resolver)
        oldResolver = self.resolver
        self.resolver = resolver
        return oldResolver

    def wakeUp(self):
        if self.waker:
            self.waker.wakeUp()

    def doIteration(self, delay):
        raise NotImplementedError(
            reflect.qual(self.__class__) + " did not implement doIteration")

    def addReader(self, reader):
        raise NotImplementedError(
            reflect.qual(self.__class__) + " did not implement addReader")

    def addWriter(self, writer):
        raise NotImplementedError(
            reflect.qual(self.__class__) + " did not implement addWriter")

    def removeReader(self, reader):
        raise NotImplementedError(
            reflect.qual(self.__class__) + " did not implement removeReader")

    def removeWriter(self, writer):
        raise NotImplementedError(
            reflect.qual(self.__class__) + " did not implement removeWriter")

    def removeAll(self):
        raise NotImplementedError(
            reflect.qual(self.__class__) + " did not implement removeAll")

    def getReaders(self):
        raise NotImplementedError(
            reflect.qual(self.__class__) + " did not implement getReaders")

    def getWriters(self):
        raise NotImplementedError(
            reflect.qual(self.__class__) + " did not implement getWriters")

    def resolve(self, name, timeout = (1, 3, 11, 45)):
        if not name:
            # XXX - This is *less than* '::', and will screw up IPv6 servers
            return defer.succeed('0.0.0.0')
        if abstract.isIPAddress(name):
            return defer.succeed(name)
        return self.resolver.getHostByName(name, timeout)

    def stop(self):
        if self._stopped:
            raise error.ReactorNotRunning(
                "Can't stop reactor that isn't running.")
        self._stopped = True
        self._justStopped = True


    def crash(self):
        self._started = False
        self.running = False
        self.addSystemEventTrigger(
            'during', 'startup', self._reallyStartRunning)

    def sigInt(self, *args):
        log.msg("Received SIGINT, shutting down.")
        self.callFromThread(self.stop)

    def sigBreak(self, *args):
        log.msg("Received SIGBREAK, shutting down.")
        self.callFromThread(self.stop)

    def sigTerm(self, *args):
        log.msg("Received SIGTERM, shutting down.")
        self.callFromThread(self.stop)

    def disconnectAll(self):
        selectables = self.removeAll()
        for reader in selectables:
            log.callWithLogger(reader,
                               reader.connectionLost,
                               failure.Failure(main.CONNECTION_LOST))


    def iterate(self, delay=0):
        self.runUntilCurrent()
        self.doIteration(delay)


    def fireSystemEvent(self, eventType):
        event = self._eventTriggers.get(eventType)
        if event is not None:
            event.fireEvent()

    def addSystemEventTrigger(self, _phase, _eventType, _f, *args, **kw):
        assert callable(_f), "%s is not callable" % _f
        if _eventType not in self._eventTriggers:
            self._eventTriggers[_eventType] = _ThreePhaseEvent()
        return (_eventType, self._eventTriggers[_eventType].addTrigger(
            _phase, _f, *args, **kw))

    def removeSystemEventTrigger(self, triggerID):
        eventType, handle = triggerID
        self._eventTriggers[eventType].removeTrigger(handle)

    def callWhenRunning(self, _callable, *args, **kw):
        if self.running:
            _callable(*args, **kw)
        else:
            return self.addSystemEventTrigger('after', 'startup',
                                              _callable, *args, **kw)

    def startRunning(self):
        if self._started:
            raise error.ReactorAlreadyRunning()
        self._started = True
        self._stopped = False
        threadable.registerAsIOThread()
        self.fireSystemEvent('startup')

    def _reallyStartRunning(self):
        self.running = True

    seconds = staticmethod(runtimeSeconds)

    def callLater(self, _seconds, _f, *args, **kw):
        assert callable(_f), "%s is not callable" % _f
        assert sys.maxint >= _seconds >= 0, \
               "%s is not greater than or equal to 0 seconds" % (_seconds,)
        tple = DelayedCall(self.seconds() + _seconds, _f, args, kw,
                           self._cancelCallLater,
                           self._moveCallLaterSooner,
                           seconds=self.seconds)
        self._newTimedCalls.append(tple)
        return tple

    def _moveCallLaterSooner(self, tple):
        # Linear time find: slow.
        heap = self._pendingTimedCalls
        try:
            pos = heap.index(tple)
            elt = heap[pos]
            while pos != 0:
                parent = (pos-1) // 2
                if heap[parent] <= elt:
                    break
                # move parent down
                heap[pos] = heap[parent]
                pos = parent
            heap[pos] = elt
        except ValueError:
            pass

    def _cancelCallLater(self, tple):
        self._cancellations+=1

    def cancelCallLater(self, callID):
        warnings.warn("reactor.cancelCallLater(callID) is deprecated - use callID.cancel() instead")
        callID.cancel()

    def getDelayedCalls(self):
        return [x for x in (self._pendingTimedCalls + self._newTimedCalls) if not x.cancelled]

    def _insertNewDelayedCalls(self):
        for call in self._newTimedCalls:
            if call.cancelled:
                self._cancellations-=1
            else:
                call.activate_delay()
                heappush(self._pendingTimedCalls, call)
        self._newTimedCalls = []

    def timeout(self):
        self._insertNewDelayedCalls()
        if not self._pendingTimedCalls:
            return None
        return max(0, self._pendingTimedCalls[0].time - self.seconds())

    def runUntilCurrent(self):
        if self.threadCallQueue:
            count = 0
            total = len(self.threadCallQueue)
            for (f, a, kw) in self.threadCallQueue:
                try:
                    f(*a, **kw)
                except:
                    log.err()
                count += 1
                if count == total:
                    break
            del self.threadCallQueue[:count]
            if self.threadCallQueue:
                self.wakeUp()

        self._insertNewDelayedCalls()

        now = self.seconds()
        while self._pendingTimedCalls and (self._pendingTimedCalls[0].time <= now):
            call = heappop(self._pendingTimedCalls)
            if call.cancelled:
                self._cancellations-=1
                continue

            if call.delayed_time > 0:
                call.activate_delay()
                heappush(self._pendingTimedCalls, call)
                continue

            try:
                call.called = 1
                call.func(*call.args, **call.kw)
            except:
                log.deferr()
                if hasattr(call, "creator"):
                    e = "\n"
                    e += " C: previous exception occurred in " + \
                         "a DelayedCall created here:\n"
                    e += " C:"
                    e += "".join(call.creator).rstrip().replace("\n","\n C:")
                    e += "\n"
                    log.msg(e)

        if (self._cancellations > 50 and
             self._cancellations > len(self._pendingTimedCalls) >> 1):
            self._cancellations = 0
            self._pendingTimedCalls = [x for x in self._pendingTimedCalls
                                       if not x.cancelled]
            heapify(self._pendingTimedCalls)

        if self._justStopped:
            self._justStopped = False
            self.fireSystemEvent("shutdown")

    def _checkProcessArgs(self, args, env):
        defaultEncoding = sys.getdefaultencoding()

        def argChecker(arg):
            if isinstance(arg, unicode):
                try:
                    arg = arg.encode(defaultEncoding)
                except UnicodeEncodeError:
                    return None
                warnings.warn(
                    "Argument strings and environment keys/values passed to "
                    "reactor.spawnProcess should be str, not unicode.",
                    category=DeprecationWarning,
                    stacklevel=4)
            if isinstance(arg, str) and '\0' not in arg:
                return arg
            return None

        if not isinstance(args, (tuple, list)):
            raise TypeError("Arguments must be a tuple or list")

        outputArgs = []
        for arg in args:
            arg = argChecker(arg)
            if arg is None:
                raise TypeError("Arguments contain a non-string value")
            else:
                outputArgs.append(arg)

        outputEnv = None
        if env is not None:
            outputEnv = {}
            for key, val in env.iteritems():
                key = argChecker(key)
                if key is None:
                    raise TypeError("Environment contains a non-string key")
                val = argChecker(val)
                if val is None:
                    raise TypeError("Environment contains a non-string value")
                outputEnv[key] = val
        return outputArgs, outputEnv

    if platform.supportsThreads():
        threadpool = None
        _threadpoolStartupID = None
        threadpoolShutdownID = None

        def _initThreads(self):
            self.usingThreads = True
            self.resolver = ThreadedResolver(self)

        def callFromThread(self, f, *args, **kw):
            assert callable(f), "%s is not callable" % (f,)
            self.threadCallQueue.append((f, args, kw))
            self.wakeUp()

        def _initThreadPool(self):
            from lib.twisted.python import threadpool
            self.threadpool = threadpool.ThreadPool(
                0, 10, 'lib.twisted.internet.reactor')
            self._threadpoolStartupID = self.callWhenRunning(
                self.threadpool.start)
            self.threadpoolShutdownID = self.addSystemEventTrigger(
                'during', 'shutdown', self._stopThreadPool)

        def _uninstallHandler(self):
            pass

        def _stopThreadPool(self):
            triggers = [self._threadpoolStartupID, self.threadpoolShutdownID]
            for trigger in filter(None, triggers):
                try:
                    self.removeSystemEventTrigger(trigger)
                except ValueError:
                    pass
            self._threadpoolStartupID = None
            self.threadpoolShutdownID = None
            self.threadpool.stop()
            self.threadpool = None

        def getThreadPool(self):
            if self.threadpool is None:
                self._initThreadPool()
            return self.threadpool

        def callInThread(self, _callable, *args, **kwargs):
            self.getThreadPool().callInThread(_callable, *args, **kwargs)

        def suggestThreadPoolSize(self, size):
            self.getThreadPool().adjustPoolsize(maxthreads=size)
    else:
        def callFromThread(self, f, *args, **kw):
            assert callable(f), "%s is not callable" % (f,)
            self.threadCallQueue.append((f, args, kw))

if platform.supportsThreads():
    classImplements(ReactorBase, IReactorThreads)

class BaseConnector(styles.Ephemeral):
    implements(IConnector)

    timeoutID = None
    factoryStarted = 0

    def __init__(self, factory, timeout, reactor):
        self.state = "disconnected"
        self.reactor = reactor
        self.factory = factory
        self.timeout = timeout

    def disconnect(self):
        if self.state == 'connecting':
            self.stopConnecting()
        elif self.state == 'connected':
            self.transport.loseConnection()

    def connect(self):
        if self.state != "disconnected":
            raise RuntimeError, "can't connect in this state"

        self.state = "connecting"
        if not self.factoryStarted:
            self.factory.doStart()
            self.factoryStarted = 1
        self.transport = transport = self._makeTransport()
        if self.timeout is not None:
            self.timeoutID = self.reactor.callLater(self.timeout, transport.failIfNotConnected, error.TimeoutError())
        self.factory.startedConnecting(self)

    def stopConnecting(self):
        if self.state != "connecting":
            raise error.NotConnectingError, "we're not trying to connect"

        self.state = "disconnected"
        self.transport.failIfNotConnected(error.UserError())
        del self.transport

    def cancelTimeout(self):
        if self.timeoutID is not None:
            try:
                self.timeoutID.cancel()
            except ValueError:
                pass
            del self.timeoutID

    def buildProtocol(self, addr):
        self.state = "connected"
        self.cancelTimeout()
        return self.factory.buildProtocol(addr)

    def connectionFailed(self, reason):
        self.cancelTimeout()
        self.transport = None
        self.state = "disconnected"
        self.factory.clientConnectionFailed(self, reason)
        if self.state == "disconnected":
            self.factory.doStop()
            self.factoryStarted = 0

    def connectionLost(self, reason):
        self.state = "disconnected"
        self.factory.clientConnectionLost(self, reason)
        if self.state == "disconnected":
            self.factory.doStop()
            self.factoryStarted = 0

    def getDestination(self):
        raise NotImplementedError(
            reflect.qual(self.__class__) + " did not implement "
            "getDestination")

class BasePort(abstract.FileDescriptor):

    addressFamily = None
    socketType = None

    def createInternetSocket(self):
        s = socket.socket(self.addressFamily, self.socketType)
        s.setblocking(0)
        fdesc._setCloseOnExec(s.fileno())
        return s

    def doWrite(self):
        raise RuntimeError, "doWrite called on a %s" % reflect.qual(self.__class__)

class _SignalReactorMixin(object):

    _installSignalHandlers = False

    def _handleSignals(self):
        try:
            import signal
        except ImportError:
            log.msg("Warning: signal module unavailable -- "
                    "not installing signal handlers.")
            return

        if signal.getsignal(signal.SIGINT) == signal.default_int_handler:
            signal.signal(signal.SIGINT, self.sigInt)
        signal.signal(signal.SIGTERM, self.sigTerm)

        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, self.sigBreak)

    def startRunning(self, installSignalHandlers=True):
        self._installSignalHandlers = installSignalHandlers
        ReactorBase.startRunning(self)

    def _reallyStartRunning(self):
        ReactorBase._reallyStartRunning(self)
        if self._installSignalHandlers:
            self._handleSignals()

    def run(self, installSignalHandlers=True):
        self.startRunning(installSignalHandlers=installSignalHandlers)
        self.mainLoop()

    def mainLoop(self):
        while self._started:
            try:
                while self._started:
                    self.runUntilCurrent()
                    t2 = self.timeout()
                    t = self.running and t2
                    self.doIteration(t)
            except:
                log.msg("Unexpected error in main loop.")
                log.err()
            else:
                log.msg('Main loop terminated.')

__all__ = []
