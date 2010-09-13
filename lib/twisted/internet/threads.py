# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import Queue
from lib.twisted.python import failure
from lib.twisted.internet import defer

def deferToThreadPool(reactor, threadpool, f, *args, **kwargs):
    d = defer.Deferred()

    def onResult(success, result):
        if success:
            reactor.callFromThread(d.callback, result)
        else:
            reactor.callFromThread(d.errback, result)

    threadpool.callInThreadWithCallback(onResult, f, *args, **kwargs)
    return d

def deferToThread(f, *args, **kwargs):
    from lib.twisted.internet import reactor
    return deferToThreadPool(reactor, reactor.getThreadPool(),
                             f, *args, **kwargs)

def _runMultiple(tupleList):
    for f, args, kwargs in tupleList:
        f(*args, **kwargs)

def callMultipleInThread(tupleList):
    from lib.twisted.internet import reactor
    reactor.callInThread(_runMultiple, tupleList)

def blockingCallFromThread(reactor, f, *a, **kw):
    queue = Queue.Queue()
    def _callFromThread():
        result = defer.maybeDeferred(f, *a, **kw)
        result.addBoth(queue.put)
    reactor.callFromThread(_callFromThread)
    result = queue.get()
    if isinstance(result, failure.Failure):
        result.raiseException()
    return result

__all__ = ["deferToThread", "deferToThreadPool", "callMultipleInThread",
           "blockingCallFromThread"]
