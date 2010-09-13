# -*- test-case-name: lib.twisted.test.test_defer,lib.twisted.test.test_defgen,lib.twisted.internet.test.test_inlinecb -*-
# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

import traceback
import warnings
from sys import exc_info

# Twisted imports
from lib.twisted.python import log, failure, lockfile
from lib.twisted.python.util import unsignedID, mergeFunctionMetadata



class AlreadyCalledError(Exception):
    pass


class CancelledError(Exception):

class TimeoutError(Exception):

def logError(err):
    log.err(err)
    return err

def succeed(result):
    d = Deferred()
    d.callback(result)
    return d

def fail(result=None):
    d = Deferred()
    d.errback(result)
    return d

def execute(callable, *args, **kw):
    try:
        result = callable(*args, **kw)
    except:
        return fail()
    else:
        return succeed(result)

def maybeDeferred(f, *args, **kw):
    try:
        result = f(*args, **kw)
    except:
        return fail(failure.Failure())

    if isinstance(result, Deferred):
        return result
    elif isinstance(result, failure.Failure):
        return fail(result)
    else:
        return succeed(result)

def timeout(deferred):
    deferred.errback(failure.Failure(TimeoutError("Callback timed out")))

def passthru(arg):
    return arg

def setDebugging(on):
    Deferred.debug=bool(on)

def getDebugging():

    return Deferred.debug

class Deferred:
    called = 0
    paused = 0
    timeoutCall = None
    _debugInfo = None
    _suppressAlreadyCalled = 0
    _runningCallbacks = False
    debug = False

    def __init__(self, canceller=None):
        self.callbacks = []
        self._canceller = canceller
        if self.debug:
            self._debugInfo = DebugInfo()
            self._debugInfo.creator = traceback.format_stack()[:-1]


    def addCallbacks(self, callback, errback=None,
                     callbackArgs=None, callbackKeywords=None,
                     errbackArgs=None, errbackKeywords=None):
        assert callable(callback)
        assert errback == None or callable(errback)
        cbs = ((callback, callbackArgs, callbackKeywords),
               (errback or (passthru), errbackArgs, errbackKeywords))
        self.callbacks.append(cbs)

        if self.called:
            self._runCallbacks()
        return self

    def addCallback(self, callback, *args, **kw):
        return self.addCallbacks(callback, callbackArgs=args,
                                 callbackKeywords=kw)

    def addErrback(self, errback, *args, **kw):
        return self.addCallbacks(passthru, errback,
                                 errbackArgs=args,
                                 errbackKeywords=kw)

    def addBoth(self, callback, *args, **kw):
        return self.addCallbacks(callback, callback,
                                 callbackArgs=args, errbackArgs=args,
                                 callbackKeywords=kw, errbackKeywords=kw)

    def chainDeferred(self, d):
        return self.addCallbacks(d.callback, d.errback)

    def callback(self, result):
        assert not isinstance(result, Deferred)
        self._startRunCallbacks(result)

    def errback(self, fail=None):
        if not isinstance(fail, failure.Failure):
            fail = failure.Failure(fail)

        self._startRunCallbacks(fail)

    def pause(self):
        self.paused = self.paused + 1


    def unpause(self):
        self.paused = self.paused - 1
        if self.paused:
            return
        if self.called:
            self._runCallbacks()

    def cancel(self):
        if not self.called:
            canceller = self._canceller
            if canceller:
                canceller(self)
            else:
                # Arrange to eat the callback that will eventually be fired
                # since there was no real canceller.
                self._suppressAlreadyCalled = 1
            if not self.called:
                # There was no canceller, or the canceller didn't call
                # callback or errback.
                self.errback(failure.Failure(CancelledError()))
        elif isinstance(self.result, Deferred):
            # Waiting for another deferred -- cancel it instead.
            self.result.cancel()

    def _continue(self, result):
        self.result = result
        self.unpause()

    def _startRunCallbacks(self, result):
        if self.called:
            if self._suppressAlreadyCalled:
                self._suppressAlreadyCalled = 0
                return
            if self.debug:
                if self._debugInfo is None:
                    self._debugInfo = DebugInfo()
                extra = "\n" + self._debugInfo._getDebugTracebacks()
                raise AlreadyCalledError(extra)
            raise AlreadyCalledError
        if self.debug:
            if self._debugInfo is None:
                self._debugInfo = DebugInfo()
            self._debugInfo.invoker = traceback.format_stack()[:-2]
        self.called = True
        self.result = result
        if self.timeoutCall:
            try:
                self.timeoutCall.cancel()
            except:
                pass

            del self.timeoutCall
        self._runCallbacks()

    def _runCallbacks(self):
        if self._runningCallbacks:
            # Don't recursively run callbacks
            return
        if not self.paused:
            while self.callbacks:
                item = self.callbacks.pop(0)
                callback, args, kw = item[
                    isinstance(self.result, failure.Failure)]
                args = args or ()
                kw = kw or {}
                try:
                    self._runningCallbacks = True
                    try:
                        self.result = callback(self.result, *args, **kw)
                    finally:
                        self._runningCallbacks = False
                    if isinstance(self.result, Deferred):
                        self.pause()
                        self.result.addBoth(self._continue)
                        break
                except:
                    self.result = failure.Failure()

        if isinstance(self.result, failure.Failure):
            self.result.cleanFailure()
            if self._debugInfo is None:
                self._debugInfo = DebugInfo()
            self._debugInfo.failResult = self.result
        else:
            if self._debugInfo is not None:
                self._debugInfo.failResult = None

    def setTimeout(self, seconds, timeoutFunc=timeout, *args, **kw):
        warnings.warn(
            "Deferred.setTimeout is deprecated.  Look for timeout "
            "support specific to the API you are using instead.",
            DeprecationWarning, stacklevel=2)

        if self.called:
            return
        assert not self.timeoutCall, "Don't call setTimeout twice on the same Deferred."

        from lib.twisted.internet import reactor
        self.timeoutCall = reactor.callLater(
            seconds,
            lambda: self.called or timeoutFunc(self, *args, **kw))
        return self.timeoutCall

    def __str__(self):
        cname = self.__class__.__name__
        if hasattr(self, 'result'):
            return "<%s at %s  current result: %r>" % (cname, hex(unsignedID(self)),
                                                       self.result)
        return "<%s at %s>" % (cname, hex(unsignedID(self)))
    __repr__ = __str__

class DebugInfo:
    failResult = None

    def _getDebugTracebacks(self):
        info = ''
        if hasattr(self, "creator"):
            info += " C: Deferred was created:\n C:"
            info += "".join(self.creator).rstrip().replace("\n","\n C:")
            info += "\n"
        if hasattr(self, "invoker"):
            info += " I: First Invoker was:\n I:"
            info += "".join(self.invoker).rstrip().replace("\n","\n I:")
            info += "\n"
        return info

    def __del__(self):
        if self.failResult is not None:
            log.msg("Unhandled error in Deferred:", isError=True)
            debugInfo = self._getDebugTracebacks()
            if debugInfo != '':
                log.msg("(debug: " + debugInfo + ")", isError=True)
            log.err(self.failResult)

class FirstError(Exception):

    def __init__(self, failure, index):
        Exception.__init__(self, failure, index)
        self.subFailure = failure
        self.index = index

    def __repr__(self):
        return 'FirstError[#%d, %r]' % (self.index, self.subFailure.value)

    def __str__(self):
        return 'FirstError[#%d, %s]' % (self.index, self.subFailure)

    def __cmp__(self, other):
        if isinstance(other, FirstError):
            return cmp(
                (self.index, self.subFailure),
                (other.index, other.subFailure))
        return -1

class DeferredList(Deferred):
    fireOnOneCallback = 0
    fireOnOneErrback = 0

    def __init__(self, deferredList, fireOnOneCallback=0, fireOnOneErrback=0,
                 consumeErrors=0):
        self.resultList = [None] * len(deferredList)
        Deferred.__init__(self)
        if len(deferredList) == 0 and not fireOnOneCallback:
            self.callback(self.resultList)

        self.fireOnOneCallback = fireOnOneCallback
        self.fireOnOneErrback = fireOnOneErrback
        self.consumeErrors = consumeErrors
        self.finishedCount = 0

        index = 0
        for deferred in deferredList:
            deferred.addCallbacks(self._cbDeferred, self._cbDeferred,
                                  callbackArgs=(index,SUCCESS),
                                  errbackArgs=(index,FAILURE))
            index = index + 1

    def _cbDeferred(self, result, index, succeeded):
        self.resultList[index] = (succeeded, result)

        self.finishedCount += 1
        if not self.called:
            if succeeded == SUCCESS and self.fireOnOneCallback:
                self.callback((result, index))
            elif succeeded == FAILURE and self.fireOnOneErrback:
                self.errback(failure.Failure(FirstError(result, index)))
            elif self.finishedCount == len(self.resultList):
                self.callback(self.resultList)

        if succeeded == FAILURE and self.consumeErrors:
            result = None

        return result

def _parseDListResult(l, fireOnOneErrback=0):
    if __debug__:
        for success, value in l:
            assert success
    return [x[1] for x in l]

def gatherResults(deferredList):
    d = DeferredList(deferredList, fireOnOneErrback=1)
    d.addCallback(_parseDListResult)
    return d

SUCCESS = True
FAILURE = False

class waitForDeferred:

    def __init__(self, d):
        if not isinstance(d, Deferred):
            raise TypeError("You must give waitForDeferred a Deferred. You gave it %r." % (d,))
        self.d = d

    def getResult(self):
        if isinstance(self.result, failure.Failure):
            self.result.raiseException()
        return self.result

def _deferGenerator(g, deferred):
    """
    See L{deferredGenerator}.
    """
    result = None
    waiting = [True, # defgen is waiting for result?
               None] # result

    while 1:
        try:
            result = g.next()
        except StopIteration:
            deferred.callback(result)
            return deferred
        except:
            deferred.errback()
            return deferred
        if isinstance(result, Deferred):
            return fail(TypeError("Yield waitForDeferred(d), not d!"))

        if isinstance(result, waitForDeferred):
            def gotResult(r, result=result):
                result.result = r
                if waiting[0]:
                    waiting[0] = False
                    waiting[1] = r
                else:
                    _deferGenerator(g, deferred)
            result.d.addBoth(gotResult)
            if waiting[0]:
                waiting[0] = False
                return deferred
            waiting[0] = True
            waiting[1] = None

            result = None

def deferredGenerator(f):
    def unwindGenerator(*args, **kwargs):
        return _deferGenerator(f(*args, **kwargs), Deferred())
    return mergeFunctionMetadata(f, unwindGenerator)
try:
    BaseException
except NameError:
    BaseException=Exception

class _DefGen_Return(BaseException):
    def __init__(self, value):
        self.value = value

def returnValue(val):
    raise _DefGen_Return(val)



def _inlineCallbacks(result, g, deferred):

    waiting = [True, # waiting for result?
               None] # result

    while 1:
        try:
            # Send the last result back as the result of the yield expression.
            isFailure = isinstance(result, failure.Failure)
            if isFailure:
                result = result.throwExceptionIntoGenerator(g)
            else:
                result = g.send(result)
        except StopIteration:
            # fell off the end, or "return" statement
            deferred.callback(None)
            return deferred
        except _DefGen_Return, e:
            appCodeTrace = exc_info()[2].tb_next
            if isFailure:
                appCodeTrace = appCodeTrace.tb_next
            if appCodeTrace.tb_next.tb_next:
                ultimateTrace = appCodeTrace
                while ultimateTrace.tb_next.tb_next:
                    ultimateTrace = ultimateTrace.tb_next
                filename = ultimateTrace.tb_frame.f_code.co_filename
                lineno = ultimateTrace.tb_lineno
                warnings.warn_explicit(
                    "returnValue() in %r causing %r to exit: "
                    "returnValue should only be invoked by functions decorated "
                    "with inlineCallbacks" % (
                        ultimateTrace.tb_frame.f_code.co_name,
                        appCodeTrace.tb_frame.f_code.co_name),
                    DeprecationWarning, filename, lineno)
            deferred.callback(e.value)
            return deferred
        except:
            deferred.errback()
            return deferred

        if isinstance(result, Deferred):
            # a deferred was yielded, get the result.
            def gotResult(r):
                if waiting[0]:
                    waiting[0] = False
                    waiting[1] = r
                else:
                    _inlineCallbacks(r, g, deferred)

            result.addBoth(gotResult)
            if waiting[0]:
                waiting[0] = False
                return deferred

            result = waiting[1]

            waiting[0] = True
            waiting[1] = None
    return deferred



def inlineCallbacks(f):
    def unwindGenerator(*args, **kwargs):
        return _inlineCallbacks(None, f(*args, **kwargs), Deferred())
    return mergeFunctionMetadata(f, unwindGenerator)

class _ConcurrencyPrimitive(object):
    def __init__(self):
        self.waiting = []

    def _releaseAndReturn(self, r):
        self.release()
        return r

    def run(*args, **kwargs):
        if len(args) < 2:
            if not args:
                raise TypeError("run() takes at least 2 arguments, none given.")
            raise TypeError("%s.run() takes at least 2 arguments, 1 given" % (
                args[0].__class__.__name__,))
        self, f = args[:2]
        args = args[2:]

        def execute(ignoredResult):
            d = maybeDeferred(f, *args, **kwargs)
            d.addBoth(self._releaseAndReturn)
            return d

        d = self.acquire()
        d.addCallback(execute)
        return d

class DeferredLock(_ConcurrencyPrimitive):
    locked = 0

    def _cancelAcquire(self, d):
        self.waiting.remove(d)

    def acquire(self):
        d = Deferred(canceller=self._cancelAcquire)
        if self.locked:
            self.waiting.append(d)
        else:
            self.locked = 1
            d.callback(self)
        return d

    def release(self):
        assert self.locked, "Tried to release an unlocked lock"
        self.locked = 0
        if self.waiting:
            # someone is waiting to acquire lock
            self.locked = 1
            d = self.waiting.pop(0)
            d.callback(self)

class DeferredSemaphore(_ConcurrencyPrimitive):

    def __init__(self, tokens):
        _ConcurrencyPrimitive.__init__(self)
        if tokens < 1:
            raise ValueError("DeferredSemaphore requires tokens >= 1")
        self.tokens = tokens
        self.limit = tokens

    def _cancelAcquire(self, d):
        self.waiting.remove(d)

    def acquire(self):
        assert self.tokens >= 0, "Internal inconsistency??  tokens should never be negative"
        d = Deferred(canceller=self._cancelAcquire)
        if not self.tokens:
            self.waiting.append(d)
        else:
            self.tokens = self.tokens - 1
            d.callback(self)
        return d


    def release(self):
        assert self.tokens < self.limit, "Someone released me too many times: too many tokens!"
        self.tokens = self.tokens + 1
        if self.waiting:
            # someone is waiting to acquire token
            self.tokens = self.tokens - 1
            d = self.waiting.pop(0)
            d.callback(self)

class QueueOverflow(Exception):
    pass

class QueueUnderflow(Exception):
    pass

class DeferredQueue(object):

    def __init__(self, size=None, backlog=None):
        self.waiting = []
        self.pending = []
        self.size = size
        self.backlog = backlog

    def _cancelGet(self, d):
        self.waiting.remove(d)

    def put(self, obj):
        if self.waiting:
            self.waiting.pop(0).callback(obj)
        elif self.size is None or len(self.pending) < self.size:
            self.pending.append(obj)
        else:
            raise QueueOverflow()

    def get(self):
        if self.pending:
            return succeed(self.pending.pop(0))
        elif self.backlog is None or len(self.waiting) < self.backlog:
            d = Deferred(canceller=self._cancelGet)
            self.waiting.append(d)
            return d
        else:
            raise QueueUnderflow()

class AlreadyTryingToLockError(Exception):

class DeferredFilesystemLock(lockfile.FilesystemLock):
    _interval = 1
    _tryLockCall = None
    _timeoutCall = None

    def __init__(self, name, scheduler=None):
        lockfile.FilesystemLock.__init__(self, name)

        if scheduler is None:
            from lib.twisted.internet import reactor
            scheduler = reactor

        self._scheduler = scheduler

    def deferUntilLocked(self, timeout=None):
        if self._tryLockCall is not None:
            return fail(
                AlreadyTryingToLockError(
                    "deferUntilLocked isn't safe for concurrent use."))

        d = Deferred()

        def _cancelLock():
            self._tryLockCall.cancel()
            self._tryLockCall = None
            self._timeoutCall = None

            if self.lock():
                d.callback(None)
            else:
                d.errback(failure.Failure(
                        TimeoutError("Timed out aquiring lock: %s after %fs" % (
                                self.name,
                                timeout))))

        def _tryLock():
            if self.lock():
                if self._timeoutCall is not None:
                    self._timeoutCall.cancel()
                    self._timeoutCall = None

                self._tryLockCall = None

                d.callback(None)
            else:
                if timeout is not None and self._timeoutCall is None:
                    self._timeoutCall = self._scheduler.callLater(
                        timeout, _cancelLock)

                self._tryLockCall = self._scheduler.callLater(
                    self._interval, _tryLock)

        _tryLock()
        return d

__all__ = ["Deferred", "DeferredList", "succeed", "fail", "FAILURE", "SUCCESS",
           "AlreadyCalledError", "TimeoutError", "gatherResults",
           "maybeDeferred",
           "waitForDeferred", "deferredGenerator", "inlineCallbacks",
           "returnValue",
           "DeferredLock", "DeferredSemaphore", "DeferredQueue",
           "DeferredFilesystemLock", "AlreadyTryingToLockError",
          ]
