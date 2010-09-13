# -*- test-case-name: lib.twisted.test.test_persisted -*-
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import types
import copy_reg
import copy
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from lib.twisted.python import log
try:
    from new import instancemethod
except:
    from org.python.core import PyMethod
    instancemethod = PyMethod
oldModules = {}

def pickleMethod(method):
    return unpickleMethod, (method.im_func.__name__,
                             method.im_self,
                             method.im_class)

def unpickleMethod(im_name,
                    im_self,
                    im_class):
    try:
        unbound = getattr(im_class,im_name)
        if im_self is None:
            return unbound
        bound=instancemethod(unbound.im_func,
                                 im_self,
                                 im_class)
        return bound
    except AttributeError:
        log.msg("Method",im_name,"not on class",im_class)
        assert im_self is not None,"No recourse: no instance to guess from."
        unbound = getattr(im_self.__class__,im_name)
        log.msg("Attempting fixup with",unbound)
        if im_self is None:
            return unbound
        bound=instancemethod(unbound.im_func,
                                 im_self,
                                 im_self.__class__)
        return bound

copy_reg.pickle(types.MethodType,
                pickleMethod,
                unpickleMethod)

def pickleModule(module):
    return unpickleModule, (module.__name__,)

def unpickleModule(name):
    if oldModules.has_key(name):
        log.msg("Module has moved: %s" % name)
        name = oldModules[name]
        log.msg(name)
    return __import__(name,{},{},'x')

copy_reg.pickle(types.ModuleType,
                pickleModule,
                unpickleModule)

def pickleStringO(stringo):
    return unpickleStringO, (stringo.getvalue(), stringo.tell())

def unpickleStringO(val, sek):
    x = StringIO.StringIO()
    x.write(val)
    x.seek(sek)
    return x

if hasattr(StringIO, 'OutputType'):
    copy_reg.pickle(StringIO.OutputType,
                    pickleStringO,
                    unpickleStringO)

def pickleStringI(stringi):
    return unpickleStringI, (stringi.getvalue(), stringi.tell())

def unpickleStringI(val, sek):
    x = StringIO.StringIO(val)
    x.seek(sek)
    return x

if hasattr(StringIO, 'InputType'):
    copy_reg.pickle(StringIO.InputType,
                pickleStringI,
                unpickleStringI)

class Ephemeral:
    def __getstate__(self):
        log.msg( "WARNING: serializing ephemeral %s" % self )
        import gc
        if getattr(gc, 'get_referrers', None):
            for r in gc.get_referrers(self):
                log.msg( " referred to by %s" % (r,))
        return None

    def __setstate__(self, state):
        log.msg( "WARNING: unserializing ephemeral %s" % self.__class__ )
        self.__class__ = Ephemeral

versionedsToUpgrade = {}
upgraded = {}

def doUpgrade():
    global versionedsToUpgrade, upgraded
    for versioned in versionedsToUpgrade.values():
        requireUpgrade(versioned)
    versionedsToUpgrade = {}
    upgraded = {}

def requireUpgrade(obj):
    objID = id(obj)
    if objID in versionedsToUpgrade and objID not in upgraded:
        upgraded[objID] = 1
        obj.versionUpgrade()
        return obj

from lib.twisted.python import reflect

def _aybabtu(c):
    l = []
    for b in reflect.allYourBase(c, Versioned):
        if b not in l and b is not Versioned:
            l.append(b)
    return l

class Versioned:
    persistenceVersion = 0
    persistenceForgets = ()

    def __setstate__(self, state):
        versionedsToUpgrade[id(self)] = self
        self.__dict__ = state

    def __getstate__(self, dict=None):
        dct = copy.copy(dict or self.__dict__)
        bases = _aybabtu(self.__class__)
        bases.reverse()
        bases.append(self.__class__) # don't forget me!!
        for base in bases:
            if base.__dict__.has_key('persistenceForgets'):
                for slot in base.persistenceForgets:
                    if dct.has_key(slot):
                        del dct[slot]
            if base.__dict__.has_key('persistenceVersion'):
                dct['%s.persistenceVersion' % reflect.qual(base)] = base.persistenceVersion
        return dct

    def versionUpgrade(self):
        bases = _aybabtu(self.__class__)
        bases.reverse()
        bases.append(self.__class__) # don't forget me!!
        if self.__dict__.has_key("persistenceVersion"):
            pver = self.__dict__['persistenceVersion']
            del self.__dict__['persistenceVersion']
            highestVersion = 0
            highestBase = None
            for base in bases:
                if not base.__dict__.has_key('persistenceVersion'):
                    continue
                if base.persistenceVersion > highestVersion:
                    highestBase = base
                    highestVersion = base.persistenceVersion
            if highestBase:
                self.__dict__['%s.persistenceVersion' % reflect.qual(highestBase)] = pver
        for base in bases:
            if (Versioned not in base.__bases__ and
                not base.__dict__.has_key('persistenceVersion')):
                continue
            currentVers = base.persistenceVersion
            pverName = '%s.persistenceVersion' % reflect.qual(base)
            persistVers = (self.__dict__.get(pverName) or 0)
            if persistVers:
                del self.__dict__[pverName]
            assert persistVers <=  currentVers, "Sorry, can't go backwards in time."
            while persistVers < currentVers:
                persistVers = persistVers + 1
                method = base.__dict__.get('upgradeToVersion%s' % persistVers, None)
                if method:
                    log.msg( "Upgrading %s (of %s @ %s) to version %s" % (reflect.qual(base), reflect.qual(self.__class__), id(self), persistVers) )
                    method(self)
                else:
                    log.msg( 'Warning: cannot upgrade %s to version %s' % (base, persistVers) )
