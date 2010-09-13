# -*- test-case-name: lib.twisted.test.test_persisted -*-

# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.twisted.python import log, reflect
try:
    from new import instancemethod
except:
    from org.python.core import PyMethod
    instancemethod = PyMethod

class NotKnown:
    def __init__(self):
        self.dependants = []
        self.resolved = 0

    def addDependant(self, mutableObject, key):
        assert not self.resolved
        self.dependants.append( (mutableObject, key) )

    resolvedObject = None

    def resolveDependants(self, newObject):
        self.resolved = 1
        self.resolvedObject = newObject
        for mut, key in self.dependants:
            mut[key] = newObject
            if isinstance(newObject, NotKnown):
                newObject.addDependant(mut, key)

    def __hash__(self):
        assert 0, "I am not to be used as a dictionary key."

class _Container(NotKnown):
    def __init__(self, l, containerType):
        NotKnown.__init__(self)
        self.containerType = containerType
        self.l = l
        self.locs = range(len(l))
        for idx in xrange(len(l)):
            if not isinstance(l[idx], NotKnown):
                self.locs.remove(idx)
            else:
                l[idx].addDependant(self, idx)
        if not self.locs:
            self.resolveDependants(self.containerType(self.l))

    def __setitem__(self, n, obj):
        self.l[n] = obj
        if not isinstance(obj, NotKnown):
            self.locs.remove(n)
            if not self.locs:
                self.resolveDependants(self.containerType(self.l))

class _Tuple(_Container):
    def __init__(self, l):
        """
        @param l: The list of object which may contain some not yet referenced
        objects.
        """
        _Container.__init__(self, l, tuple)

class _InstanceMethod(NotKnown):
    def __init__(self, im_name, im_self, im_class):
        NotKnown.__init__(self)
        self.my_class = im_class
        self.name = im_name
        im_self.addDependant(self, 0)

    def __call__(self, *args, **kw):
        import traceback
        log.msg('instance method %s.%s' % (reflect.qual(self.my_class), self.name))
        log.msg('being called with %r %r' % (args, kw))
        traceback.print_stack(file=log.logfile)
        assert 0

    def __setitem__(self, n, obj):
        assert n == 0, "only zero index allowed"
        if not isinstance(obj, NotKnown):
            self.resolveDependants(instancemethod(self.my_class.__dict__[self.name],
                                                  obj,
                                                  self.my_class))

class _DictKeyAndValue:
    def __init__(self, dict):
        self.dict = dict
    def __setitem__(self, n, obj):
        if n not in (1, 0):
            raise RuntimeError("DictKeyAndValue should only ever be called with 0 or 1")
        if n: # value
            self.value = obj
        else:
            self.key = obj
        if hasattr(self, "key") and hasattr(self, "value"):
            self.dict[self.key] = self.value

class _Dereference(NotKnown):
    def __init__(self, id):
        NotKnown.__init__(self)
        self.id = id

from lib.twisted.internet.defer import Deferred
class _Catcher:
    def catch(self, value):
        self.value = value

class _Defer(Deferred, NotKnown):
    def __init__(self):
        Deferred.__init__(self)
        NotKnown.__init__(self)
        self.pause()

    wasset = 0

    def __setitem__(self, n, obj):
        if self.wasset:
            raise RuntimeError('setitem should only be called once, setting %r to %r' % (n, obj))
        else:
            self.wasset = 1
        self.callback(obj)

    def addDependant(self, dep, key):
        NotKnown.addDependant(self,  dep, key)
        self.unpause()
        resovd = self.result
        self.resolveDependants(resovd)
