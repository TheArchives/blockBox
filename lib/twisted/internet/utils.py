# -*- test-case-name: lib.twisted.test.test_iutils -*-
# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.
import sys, warnings
from lib.twisted.internet import protocol, defer
from lib.twisted.python import failure, util as tputil
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

def _callProtocolWithDeferred(protocol, executable, args, env, path, reactor=None):
    if reactor is None:
        from lib.twisted.internet import reactor

    d = defer.Deferred()
    p = protocol(d)
    reactor.spawnProcess(p, executable, (executable,)+tuple(args), env, path)
    return d

class _UnexpectedErrorOutput(IOError):
    def __init__(self, text, processEnded):
        IOError.__init__(self, "got stderr: %r" % (text,))
        self.processEnded = processEnded

class _BackRelay(protocol.ProcessProtocol):
    def __init__(self, deferred, errortoo=0):
        self.deferred = deferred
        self.s = StringIO.StringIO()
        if errortoo:
            self.errReceived = self.errReceivedIsGood
        else:
            self.errReceived = self.errReceivedIsBad

    def errReceivedIsBad(self, text):
        if self.deferred is not None:
            self.onProcessEnded = defer.Deferred()
            err = _UnexpectedErrorOutput(text, self.onProcessEnded)
            self.deferred.errback(failure.Failure(err))
            self.deferred = None
            self.transport.loseConnection()

    def errReceivedIsGood(self, text):
        self.s.write(text)

    def outReceived(self, text):
        self.s.write(text)

    def processEnded(self, reason):
        if self.deferred is not None:
            self.deferred.callback(self.s.getvalue())
        elif self.onProcessEnded is not None:
            self.onProcessEnded.errback(reason)

def getProcessOutput(executable, args=(), env={}, path=None, reactor=None,
                     errortoo=0):
    return _callProtocolWithDeferred(lambda d:
                                        _BackRelay(d, errortoo=errortoo),
                                     executable, args, env, path,
                                     reactor)

class _ValueGetter(protocol.ProcessProtocol):
    def __init__(self, deferred):
        self.deferred = deferred

    def processEnded(self, reason):
        self.deferred.callback(reason.value.exitCode)

def getProcessValue(executable, args=(), env={}, path=None, reactor=None):
    """Spawn a process and return its exit code as a Deferred."""
    return _callProtocolWithDeferred(_ValueGetter, executable, args, env, path,
                                    reactor)

class _EverythingGetter(protocol.ProcessProtocol):
    def __init__(self, deferred):
        self.deferred = deferred
        self.outBuf = StringIO.StringIO()
        self.errBuf = StringIO.StringIO()
        self.outReceived = self.outBuf.write
        self.errReceived = self.errBuf.write

    def processEnded(self, reason):
        out = self.outBuf.getvalue()
        err = self.errBuf.getvalue()
        e = reason.value
        code = e.exitCode
        if e.signal:
            self.deferred.errback((out, err, e.signal))
        else:
            self.deferred.callback((out, err, code))

def getProcessOutputAndValue(executable, args=(), env={}, path=None,
                             reactor=None):
    return _callProtocolWithDeferred(_EverythingGetter, executable, args, env, path,
                                    reactor)

def _resetWarningFilters(passthrough, addedFilters):
    for f in addedFilters:
        try:
            warnings.filters.remove(f)
        except ValueError:
            pass
    return passthrough

def runWithWarningsSuppressed(suppressedWarnings, f, *a, **kw):
    for args, kwargs in suppressedWarnings:
        warnings.filterwarnings(*args, **kwargs)
    addedFilters = warnings.filters[:len(suppressedWarnings)]
    try:
        result = f(*a, **kw)
    except:
        exc_info = sys.exc_info()
        _resetWarningFilters(None, addedFilters)
        raise exc_info[0], exc_info[1], exc_info[2]
    else:
        if isinstance(result, defer.Deferred):
            result.addBoth(_resetWarningFilters, addedFilters)
        else:
            _resetWarningFilters(None, addedFilters)
        return result

def suppressWarnings(f, *suppressedWarnings):
    def warningSuppressingWrapper(*a, **kw):
        return runWithWarningsSuppressed(suppressedWarnings, f, *a, **kw)
    return tputil.mergeFunctionMetadata(f, warningSuppressingWrapper)

__all__ = [
    "runWithWarningsSuppressed", "suppressWarnings",

    "getProcessOutput", "getProcessValue", "getProcessOutputAndValue",
    ]
