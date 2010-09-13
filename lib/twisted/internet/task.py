# -*- test-case-name: lib.twisted.test.test_task,lib.twisted.test.test_cooperator -*-
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.

__metaclass__ = type

import time

from lib.zope.interface import implements

from lib.twisted.python import reflect
from lib.twisted.python.failure import Failure

from lib.twisted.internet import base, defer
from lib.twisted.internet.interfaces import IReactorTime

class LoopingCall:

    call = None
    running = False
    deferred = None
    interval = None
    _expectNextCallAt = 0.0
    _runAtStart = False
    starttime = None

    def __init__(self, f, *a, **kw):
        self.f = f
        self.a = a
        self.kw = kw
        from lib.twisted.internet import reactor
        self.clock = reactor

    def withCount(cls, countCallable):
        def counter():
            now = self.clock.seconds()
            lastTime = self._realLastTime
            if lastTime is None:
                lastTime = self.starttime
                if self._runAtStart:
                    lastTime -= self.interval
            self._realLastTime = now
            lastInterval = self._intervalOf(lastTime)
            thisInterval = self._intervalOf(now)
            count = thisInterval - lastInterval
            return countCallable(count)

        self = cls(counter)

        self._realLastTime = None

        return self

    withCount = classmethod(withCount)

    def _intervalOf(self, t):
        elapsedTime = t - self.starttime
        intervalNum = int(elapsedTime / self.interval)
        return intervalNum

    def start(self, interval, now=True):
        assert not self.running, ("Tried to start an already running "
                                  "LoopingCall.")
        if interval < 0:
            raise ValueError, "interval must be >= 0"
        self.running = True
        d = self.deferred = defer.Deferred()
        self.starttime = self.clock.seconds()
        self._expectNextCallAt = self.starttime
        self.interval = interval
        self._runAtStart = now
        if now:
            self()
        else:
            self._reschedule()
        return d

    def stop(self):
        assert self.running, ("Tried to stop a LoopingCall that was "
                              "not running.")
        self.running = False
        if self.call is not None:
            self.call.cancel()
            self.call = None
            d, self.deferred = self.deferred, None
            d.callback(self)

    def __call__(self):
        def cb(result):
            if self.running:
                self._reschedule()
            else:
                d, self.deferred = self.deferred, None
                d.callback(self)

        def eb(failure):
            self.running = False
            d, self.deferred = self.deferred, None
            d.errback(failure)

        self.call = None
        d = defer.maybeDeferred(self.f, *self.a, **self.kw)
        d.addCallback(cb)
        d.addErrback(eb)

    def _reschedule(self):
        if self.interval == 0:
            self.call = self.clock.callLater(0, self)
            return

        currentTime = self.clock.seconds()
        untilNextTime = (self._expectNextCallAt - currentTime) % self.interval
        nextTime = max(
            self._expectNextCallAt + self.interval, currentTime + untilNextTime)
        if nextTime == currentTime:
            nextTime += self.interval
        self._expectNextCallAt = nextTime
        self.call = self.clock.callLater(nextTime - currentTime, self)

    def __repr__(self):
        if hasattr(self.f, 'func_name'):
            func = self.f.func_name
            if hasattr(self.f, 'im_class'):
                func = self.f.im_class.__name__ + '.' + func
        else:
            func = reflect.safe_repr(self.f)

        return 'LoopingCall<%r>(%s, *%s, **%s)' % (
            self.interval, func, reflect.safe_repr(self.a),
            reflect.safe_repr(self.kw))

class SchedulerError(Exception):

class SchedulerStopped(SchedulerError):

class TaskFinished(SchedulerError):

class TaskDone(TaskFinished):

class TaskStopped(TaskFinished):

class TaskFailed(TaskFinished):

class NotPaused(SchedulerError):

class _Timer(object):
    MAX_SLICE = 0.01
    def __init__(self):
        self.end = time.time() + self.MAX_SLICE

    def __call__(self):
        return time.time() >= self.end

_EPSILON = 0.00000001
def _defaultScheduler(x):
    from lib.twisted.internet import reactor
    return reactor.callLater(_EPSILON, x)

class CooperativeTask(object):
    def __init__(self, iterator, cooperator):
        self._iterator = iterator
        self._cooperator = cooperator
        self._deferreds = []
        self._pauseCount = 0
        self._completionState = None
        self._completionResult = None
        cooperator._addTask(self)

    def whenDone(self):
        d = defer.Deferred()
        if self._completionState is None:
            self._deferreds.append(d)
        else:
            d.callback(self._completionResult)
        return d

    def pause(self):
        self._checkFinish()
        self._pauseCount += 1
        if self._pauseCount == 1:
            self._cooperator._removeTask(self)

    def resume(self):
        if self._pauseCount == 0:
            raise NotPaused()
        self._pauseCount -= 1
        if self._pauseCount == 0 and self._completionState is None:
            self._cooperator._addTask(self)

    def _completeWith(self, completionState, deferredResult):
        self._completionState = completionState
        self._completionResult = deferredResult
        if not self._pauseCount:
            self._cooperator._removeTask(self)
        for d in self._deferreds:
            d.callback(deferredResult)

    def stop(self):
        self._checkFinish()
        self._completeWith(TaskStopped(), Failure(TaskStopped()))

    def _checkFinish(self):
        if self._completionState is not None:
            raise self._completionState

    def _oneWorkUnit(self):
        try:
            result = self._iterator.next()
        except StopIteration:
            self._completeWith(TaskDone(), self._iterator)
        except:
            self._completeWith(TaskFailed(), Failure())
        else:
            if isinstance(result, defer.Deferred):
                self.pause()
                def failLater(f):
                    self._completeWith(TaskFailed(), f)
                result.addCallbacks(lambda result: self.resume(),
                                    failLater)

class Cooperator(object):
    def __init__(self,
                 terminationPredicateFactory=_Timer,
                 scheduler=_defaultScheduler,
                 started=True):
        self._tasks = []
        self._metarator = iter(())
        self._terminationPredicateFactory = terminationPredicateFactory
        self._scheduler = scheduler
        self._delayedCall = None
        self._stopped = False
        self._started = started

    def coiterate(self, iterator, doneDeferred=None):
        if doneDeferred is None:
            doneDeferred = defer.Deferred()
        CooperativeTask(iterator, self).whenDone().chainDeferred(doneDeferred)
        return doneDeferred

    def cooperate(self, iterator):
        return CooperativeTask(iterator, self)

    def _addTask(self, task):
        if self._stopped:
            self._tasks.append(task)
            task._completeWith(SchedulerStopped(), Failure(SchedulerStopped()))
        else:
            self._tasks.append(task)
            self._reschedule()

    def _removeTask(self, task):
        self._tasks.remove(task)

    def _tasksWhileNotStopped(self):
        terminator = self._terminationPredicateFactory()
        while self._tasks:
            for t in self._metarator:
                yield t
                if terminator():
                    return
            self._metarator = iter(self._tasks)

    def _tick(self):
        self._delayedCall = None
        for taskObj in self._tasksWhileNotStopped():
            taskObj._oneWorkUnit()
        self._reschedule()

    _mustScheduleOnStart = False
    def _reschedule(self):
        if not self._started:
            self._mustScheduleOnStart = True
            return
        if self._delayedCall is None and self._tasks:
            self._delayedCall = self._scheduler(self._tick)

    def start(self):
        self._stopped = False
        self._started = True
        if self._mustScheduleOnStart:
            del self._mustScheduleOnStart
            self._reschedule()

    def stop(self):
        self._stopped = True
        for taskObj in self._tasks:
            taskObj._completeWith(SchedulerStopped(),
                                  Failure(SchedulerStopped()))
        self._tasks = []
        if self._delayedCall is not None:
            self._delayedCall.cancel()
            self._delayedCall = None

_theCooperator = Cooperator()

def coiterate(iterator):
    return _theCooperator.coiterate(iterator)

def cooperate(iterator):
    return _theCooperator.cooperate(iterator)

class Clock:
    implements(IReactorTime)

    rightNow = 0.0

    def __init__(self):
        self.calls = []

    def seconds(self):
        return self.rightNow

    def callLater(self, when, what, *a, **kw):
        dc = base.DelayedCall(self.seconds() + when,
                               what, a, kw,
                               self.calls.remove,
                               lambda c: None,
                               self.seconds)
        self.calls.append(dc)
        self.calls.sort(lambda a, b: cmp(a.getTime(), b.getTime()))
        return dc

    def getDelayedCalls(self):
        return self.calls

    def advance(self, amount):
        self.rightNow += amount
        while self.calls and self.calls[0].getTime() <= self.seconds():
            call = self.calls.pop(0)
            call.called = 1
            call.func(*call.args, **call.kw)

    def pump(self, timings):
        for amount in timings:
            self.advance(amount)

def deferLater(clock, delay, callable, *args, **kw):
    def deferLaterCancel(deferred):
        delayedCall.cancel()
    d = defer.Deferred(deferLaterCancel)
    d.addCallback(lambda ignored: callable(*args, **kw))
    delayedCall = clock.callLater(delay, d.callback, None)
    return d

__all__ = [
    'LoopingCall',
    'Clock',
    'SchedulerStopped', 'Cooperator', 'coiterate',
    'deferLater',
    ]
