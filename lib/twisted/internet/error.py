# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

import socket
from lib.twisted.python import deprecate
from lib.twisted.python.versions import Version

class BindError(Exception):
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(self.args))
        s = '%s.' % s
        return s

class CannotListenError(BindError):
    def __init__(self, interface, port, socketError):
        BindError.__init__(self, interface, port, socketError)
        self.interface = interface
        self.port = port
        self.socketError = socketError

    def __str__(self):
        iface = self.interface or 'any'
        return "Couldn't listen on %s:%s: %s." % (iface, self.port,
                                                 self.socketError)


class MulticastJoinError(Exception):

class MessageLengthError(Exception):
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(self.args))
        s = '%s.' % s
        return s

class DNSLookupError(IOError):
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(self.args))
        s = '%s.' % s
        return s

class ConnectInProgressError(Exception):

class ConnectError(Exception):
    def __init__(self, osError=None, string=""):
        self.osError = osError
        Exception.__init__(self, string)

    def __str__(self):
        s = self.__doc__ or self.__class__.__name__
        if self.osError:
            s = '%s: %s' % (s, self.osError)
        if self[0]:
            s = '%s: %s' % (s, self[0])
        s = '%s.' % s
        return s

class ConnectBindError(ConnectError):

class UnknownHostError(ConnectError):

class NoRouteError(ConnectError):

class ConnectionRefusedError(ConnectError):

class TCPTimedOutError(ConnectError):

class BadFileError(ConnectError):

class ServiceNameUnknownError(ConnectError):

class UserError(ConnectError):

class TimeoutError(UserError):

class SSLError(ConnectError):

class VerifyError(Exception):

class PeerVerifyError(VerifyError):

class CertificateError(Exception):

try:
    import errno
    errnoMapping = {
        errno.ENETUNREACH: NoRouteError,
        errno.ECONNREFUSED: ConnectionRefusedError,
        errno.ETIMEDOUT: TCPTimedOutError,
    }
    if hasattr(errno, "WSAECONNREFUSED"):
        errnoMapping[errno.WSAECONNREFUSED] = ConnectionRefusedError
        errnoMapping[errno.WSAENETUNREACH] = NoRouteError
except ImportError:
    errnoMapping = {}

def getConnectError(e):
    try:
        number, string = e
    except ValueError:
        return ConnectError(string=e)

    if hasattr(socket, 'gaierror') and isinstance(e, socket.gaierror):
        klass = UnknownHostError
    else:
        klass = errnoMapping.get(number, ConnectError)
    return klass(number, string)

class ConnectionClosed(Exception):

class ConnectionLost(ConnectionClosed):
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(self.args))
        s = '%s.' % s
        return s

class ConnectionDone(ConnectionClosed):
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(self.args))
        s = '%s.' % s
        return s

class ConnectionFdescWentAway(ConnectionLost):

class AlreadyCalled(ValueError):
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(self.args))
        s = '%s.' % s
        return s

class AlreadyCancelled(ValueError):
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(self.args))
        s = '%s.' % s
        return s

class PotentialZombieWarning(Warning):
    MESSAGE = (
        "spawnProcess called, but the SIGCHLD handler is not "
        "installed. This probably means you have not yet "
        "called reactor.run, or called "
        "reactor.run(installSignalHandler=0). You will probably "
        "never see this process finish, and it may become a "
        "zombie process.")

deprecate.deprecatedModuleAttribute(
    Version("Twisted", 10, 0, 0),
    "There is no longer any potential for zombie process.",
    __name__,
    "PotentialZombieWarning")

class ProcessDone(ConnectionDone):
    def __init__(self, status):
        Exception.__init__(self, "process finished with exit code 0")
        self.exitCode = 0
        self.signal = None
        self.status = status

class ProcessTerminated(ConnectionLost):
    def __init__(self, exitCode=None, signal=None, status=None):
        self.exitCode = exitCode
        self.signal = signal
        self.status = status
        s = "process ended"
        if exitCode is not None: s = s + " with exit code %s" % exitCode
        if signal is not None: s = s + " by signal %s" % signal
        Exception.__init__(self, s)

class ProcessExitedAlready(Exception):

class NotConnectingError(RuntimeError):
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(self.args))
        s = '%s.' % s
        return s

class NotListeningError(RuntimeError):
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(self.args))
        s = '%s.' % s
        return s

class ReactorNotRunning(RuntimeError):

class ReactorAlreadyRunning(RuntimeError):

class ConnectingCancelledError(Exception):
    def __init__(self, address):
        """
        @param address: The L{IAddress} that is the destination of the
            L{IStreamClientEndpoint} that was cancelled.
        """
        Exception.__init__(self, address)
        self.address = address
