# Copyright (c) 2001-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import warnings, os
from lib.zope.interface import implements
from lib.twisted.internet.interfaces import IAddress

class IPv4Address(object):
    implements(IAddress)

    def __init__(self, type, host, port, _bwHack = None):
        assert type in ('TCP', 'UDP')
        self.type = type
        self.host = host
        self.port = port
        self._bwHack = _bwHack

    def __getitem__(self, index):
        warnings.warn("IPv4Address.__getitem__ is deprecated.  Use attributes instead.",
                      category=DeprecationWarning, stacklevel=2)
        return (self._bwHack or self.type, self.host, self.port).__getitem__(index)

    def __getslice__(self, start, stop):
        warnings.warn("IPv4Address.__getitem__ is deprecated.  Use attributes instead.",
                      category=DeprecationWarning, stacklevel=2)
        return (self._bwHack or self.type, self.host, self.port)[start:stop]

    def __eq__(self, other):
        if isinstance(other, tuple):
            return tuple(self) == other
        elif isinstance(other, IPv4Address):
            a = (self.type, self.host, self.port)
            b = (other.type, other.host, other.port)
            return a == b
        return False

    def __repr__(self):
        return 'IPv4Address(%s, %r, %d)' % (self.type, self.host, self.port)

class UNIXAddress(object):
    implements(IAddress)

    def __init__(self, name, _bwHack='UNIX'):
        self.name = name
        self._bwHack = _bwHack

    def __getitem__(self, index):
        warnings.warn("UNIXAddress.__getitem__ is deprecated.  Use attributes instead.",
                      category=DeprecationWarning, stacklevel=2)
        return (self._bwHack, self.name).__getitem__(index)

    def __getslice__(self, start, stop):
        warnings.warn("UNIXAddress.__getitem__ is deprecated.  Use attributes instead.",
                      category=DeprecationWarning, stacklevel=2)
        return (self._bwHack, self.name)[start:stop]

    def __eq__(self, other):
        if isinstance(other, tuple):
            return tuple(self) == other
        elif isinstance(other, UNIXAddress):
            if self.name == other.name:
                return True
            else:
                try:
                    return os.path.samefile(self.name, other.name)
                except OSError:
                    pass
        return False

    def __repr__(self):
        return 'UNIXAddress(%r)' % (self.name,)

class _ServerFactoryIPv4Address(IPv4Address):
    def __eq__(self, other):
        if isinstance(other, tuple):
            warnings.warn("IPv4Address.__getitem__ is deprecated.  Use attributes instead.",
                          category=DeprecationWarning, stacklevel=2)
            return (self.host, self.port) == other
        elif isinstance(other, IPv4Address):
            a = (self.type, self.host, self.port)
            b = (other.type, other.host, other.port)
            return a == b
        return False
