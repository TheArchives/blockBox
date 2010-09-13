##############################################################################
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
__docformat__ = 'restructuredtext'

import sys
import weakref
from lib.zope.interface.interface import InterfaceClass, Specification
from lib.zope.interface.interface import SpecificationBase
from types import ModuleType, MethodType, FunctionType
from lib.zope.interface.advice import addClassAdvisor

# Registry of class-implementation specifications
BuiltinImplementationSpecifications = {}

class Declaration(Specification):
    """Interface declarations"""

    def __init__(self, *interfaces):
        Specification.__init__(self, _normalizeargs(interfaces))

    def changed(self, originally_changed):
        Specification.changed(self, originally_changed)
        try:
            del self._v_attrs
        except AttributeError:
            pass

    def __contains__(self, interface):
        return self.extends(interface) and interface in self.interfaces()

    def __iter__(self):
        return self.interfaces()

    def flattened(self):
        return iter(self.__iro__)

    def __sub__(self, other):
        return Declaration(
            *[i for i in self.interfaces()
                if not [j for j in other.interfaces()
                        if i.extends(j, 0)]
                ]
                )

    def __add__(self, other):
        seen = {}
        result = []
        for i in self.interfaces():
            if i not in seen:
                seen[i] = 1
                result.append(i)
        for i in other.interfaces():
            if i not in seen:
                seen[i] = 1
                result.append(i)

        return Declaration(*result)

    __radd__ = __add__


class Implements(Declaration):

    # class whose specification should be used as additional base
    inherit = None

    # interfaces actually declared for a class
    declared = ()

    __name__ = '?'

    def __repr__(self):
        return '<implementedBy %s>' % (self.__name__)

    def __reduce__(self):
        return implementedBy, (self.inherit, )

def implementedByFallback(cls):
    try:
        spec = cls.__dict__.get('__implemented__')
    except AttributeError:
        spec = getattr(cls, '__implemented__', None)
        if spec is None:
            # There's no spec stred in the class. Maybe its a builtin:
            spec = BuiltinImplementationSpecifications.get(cls)
            if spec is not None:
                return spec
            return _empty

        if spec.__class__ == Implements:
            # we defaulted to _empty or there was a spec. Good enough.
            # Return it.
            return spec

        return Declaration(*_normalizeargs((spec, )))

    if isinstance(spec, Implements):
        return spec

    if spec is None:
        spec = BuiltinImplementationSpecifications.get(cls)
        if spec is not None:
            return spec

    # TODO: need old style __implements__ compatibility?
    if spec is not None:
        # old-style __implemented__ = foo declaration
        spec = (spec, ) # tuplefy, as it might be just an int
        spec = Implements(*_normalizeargs(spec))
        spec.inherit = None    # old-style implies no inherit
        del cls.__implemented__ # get rid of the old-style declaration
    else:
        try:
            bases = cls.__bases__
        except AttributeError:
            if not callable(cls):
                raise TypeError("ImplementedBy called for non-factory", cls)
            bases = ()

        spec = Implements(*[implementedBy(c) for c in bases])
        spec.inherit = cls

    spec.__name__ = (getattr(cls, '__module__', '?') or '?') + \
                    '.' + (getattr(cls, '__name__', '?') or '?')

    try:
        cls.__implemented__ = spec
        if not hasattr(cls, '__providedBy__'):
            cls.__providedBy__ = objectSpecificationDescriptor

        if (isinstance(cls, DescriptorAwareMetaClasses)
            and
            '__provides__' not in cls.__dict__):
            # Make sure we get a __provides__ descriptor
            cls.__provides__ = ClassProvides(
                cls,
                getattr(cls, '__class__', type(cls)),
                )

    except TypeError:
        if not isinstance(cls, type):
            raise TypeError("ImplementedBy called for non-type", cls)
        BuiltinImplementationSpecifications[cls] = spec

    return spec

implementedBy = implementedByFallback

def classImplementsOnly(cls, *interfaces):
    spec = implementedBy(cls)
    spec.declared = ()
    spec.inherit = None
    classImplements(cls, *interfaces)

def classImplements(cls, *interfaces):

    spec = implementedBy(cls)
    spec.declared += tuple(_normalizeargs(interfaces))

    # compute the bases
    bases = []
    seen = {}
    for b in spec.declared:
        if b not in seen:
            seen[b] = 1
            bases.append(b)

    if spec.inherit is not None:

        for c in spec.inherit.__bases__:
            b = implementedBy(c)
            if b not in seen:
                seen[b] = 1
                bases.append(b)            

    spec.__bases__ = tuple(bases)

def _implements_advice(cls):
    interfaces, classImplements = cls.__dict__['__implements_advice_data__']
    del cls.__implements_advice_data__
    classImplements(cls, *interfaces)
    return cls


class implementer:

    def __init__(self, *interfaces):
        self.interfaces = interfaces

    def __call__(self, ob):
        if isinstance(ob, DescriptorAwareMetaClasses):
            classImplements(ob, *self.interfaces)
            return ob            
        
        spec = Implements(*self.interfaces)
        try:
            ob.__implemented__ = spec
        except AttributeError:
            raise TypeError("Can't declare implements", ob)
        return ob

class implementer_only:

    def __init__(self, *interfaces):
        self.interfaces = interfaces

    def __call__(self, ob):
        if isinstance(ob, (FunctionType, MethodType)):
            raise ValueError('The implementor_only decorator is not '
                             'supported for methods or functions.')
        else:
            # Assume it's a class:
            classImplementsOnly(ob, *self.interfaces)
            return ob            
        
def _implements(name, interfaces, classImplements):
    frame = sys._getframe(2)
    locals = frame.f_locals

    if (locals is frame.f_globals) or (
        ('__module__' not in locals) and sys.version_info[:3] > (2, 2, 0)):
        raise TypeError(name+" can be used only from a class definition.")

    if '__implements_advice_data__' in locals:
        raise TypeError(name+" can be used only once in a class definition.")

    locals['__implements_advice_data__'] = interfaces, classImplements
    addClassAdvisor(_implements_advice, depth=3)

def implements(*interfaces):
    _implements("implements", interfaces, classImplements)

def implementsOnly(*interfaces):
    _implements("implementsOnly", interfaces, classImplementsOnly)

class Provides(Declaration):  # Really named ProvidesClass

    def __init__(self, cls, *interfaces):
        self.__args = (cls, ) + interfaces
        self._cls = cls
        Declaration.__init__(self, *(interfaces + (implementedBy(cls), )))

    def __reduce__(self):
        return Provides, self.__args

    __module__ = 'lib.zope.interface'

    def __get__(self, inst, cls):
        if inst is None and cls is self._cls:
            return self

        raise AttributeError('__provides__')

ProvidesClass = Provides

InstanceDeclarations = weakref.WeakValueDictionary()

def Provides(*interfaces):
    spec = InstanceDeclarations.get(interfaces)
    if spec is None:
        spec = ProvidesClass(*interfaces)
        InstanceDeclarations[interfaces] = spec

    return spec
Provides.__safe_for_unpickling__ = True

try:
    from types import ClassType
    DescriptorAwareMetaClasses = ClassType, type
except ImportError: # Python 3
    DescriptorAwareMetaClasses = (type,)
    
def directlyProvides(object, *interfaces):
    cls = getattr(object, '__class__', None)
    if cls is not None and getattr(cls,  '__class__', None) is cls:
        # It's a meta class (well, at least it it could be an extension class)
        if not isinstance(object, DescriptorAwareMetaClasses):
            raise TypeError("Attempt to make an interface declaration on a "
                            "non-descriptor-aware class")

    interfaces = _normalizeargs(interfaces)
    if cls is None:
        cls = type(object)

    issub = False
    for damc in DescriptorAwareMetaClasses:
        if issubclass(cls, damc):
            issub = True
            break
    if issub:
        # we have a class or type.  We'll use a special descriptor
        # that provides some extra caching
        object.__provides__ = ClassProvides(object, cls, *interfaces)
    else:
        object.__provides__ = Provides(cls, *interfaces)


def alsoProvides(object, *interfaces):
    directlyProvides(object, directlyProvidedBy(object), *interfaces)

def noLongerProvides(object, interface):
    directlyProvides(object, directlyProvidedBy(object)-interface)
    if interface.providedBy(object):
        raise ValueError("Can only remove directly provided interfaces.")

class ClassProvidesBasePy(object):

    def __get__(self, inst, cls):
        if cls is self._cls:
            # We only work if called on the class we were defined for

            if inst is None:
                # We were accessed through a class, so we are the class'
                # provides spec. Just return this object as is:
                return self

            return self._implements

        raise AttributeError('__provides__')

ClassProvidesBase = ClassProvidesBasePy

# Try to get C base:
try:
    import _zope_interface_coptimizations
except ImportError:
    pass
else:
    from _zope_interface_coptimizations import ClassProvidesBase


class ClassProvides(Declaration, ClassProvidesBase):

    def __init__(self, cls, metacls, *interfaces):
        self._cls = cls
        self._implements = implementedBy(cls)
        self.__args = (cls, metacls, ) + interfaces
        Declaration.__init__(self, *(interfaces + (implementedBy(metacls), )))

    def __reduce__(self):
        return self.__class__, self.__args

    # Copy base-class method for speed
    __get__ = ClassProvidesBase.__get__

def directlyProvidedBy(object):
    provides = getattr(object, "__provides__", None)
    if (provides is None # no spec
        or

        isinstance(provides, Implements)
        ):
        return _empty

    # Strip off the class part of the spec:
    return Declaration(provides.__bases__[:-1])

def classProvides(*interfaces):
    frame = sys._getframe(1)
    locals = frame.f_locals

    # Try to make sure we were called from a class def
    if (locals is frame.f_globals) or ('__module__' not in locals):
        raise TypeError("classProvides can be used only from a class definition.")

    if '__provides__' in locals:
        raise TypeError(
            "classProvides can only be used once in a class definition.")

    locals["__provides__"] = _normalizeargs(interfaces)

    addClassAdvisor(_classProvides_advice, depth=2)

def _classProvides_advice(cls):
    interfaces = cls.__dict__['__provides__']
    del cls.__provides__
    directlyProvides(cls, *interfaces)
    return cls

class provider:
    """Class decorator version of classProvides"""

    def __init__(self, *interfaces):
        self.interfaces = interfaces

    def __call__(self, ob):
        directlyProvides(ob, *self.interfaces)
        return ob            

def moduleProvides(*interfaces):
    frame = sys._getframe(1)
    locals = frame.f_locals

    # Try to make sure we were called from a class def
    if (locals is not frame.f_globals) or ('__name__' not in locals):
        raise TypeError(
            "moduleProvides can only be used from a module definition.")

    if '__provides__' in locals:
        raise TypeError(
            "moduleProvides can only be used once in a module definition.")

    locals["__provides__"] = Provides(ModuleType,
                                      *_normalizeargs(interfaces))

def ObjectSpecification(direct, cls):

    return Provides(cls, direct)

def getObjectSpecification(ob):

    provides = getattr(ob, '__provides__', None)
    if provides is not None:
        if isinstance(provides, SpecificationBase):
            return provides

    try:
        cls = ob.__class__
    except AttributeError:
        # We can't get the class, so just consider provides
        return _empty

    return implementedBy(cls)

def providedBy(ob):

    try:
        r = ob.__providedBy__
    except AttributeError:
        # Not set yet. Fall back to lower-level thing that computes it
        return getObjectSpecification(ob)

    try:
        r.extends

    except AttributeError:
        try:
            r = ob.__provides__
        except AttributeError:
            # No __provides__, so just fall back to implementedBy
            return implementedBy(ob.__class__)
        try:
            cp = ob.__class__.__provides__
        except AttributeError:
            return r

        if r is cp:
            return implementedBy(ob.__class__)

    return r

class ObjectSpecificationDescriptorPy(object):

    def __get__(self, inst, cls):
        if inst is None:
            return getObjectSpecification(cls)

        provides = getattr(inst, '__provides__', None)
        if provides is not None:
            return provides

        return implementedBy(cls)

ObjectSpecificationDescriptor = ObjectSpecificationDescriptorPy

def _normalizeargs(sequence, output = None):
    if output is None:
        output = []

    cls = sequence.__class__
    if InterfaceClass in cls.__mro__ or Implements in cls.__mro__:
        output.append(sequence)
    else:
        for v in sequence:
            _normalizeargs(v, output)

    return output

_empty = Declaration()

try:
    import _zope_interface_coptimizations
except ImportError:
    pass
else:
    from _zope_interface_coptimizations import implementedBy, providedBy
    from _zope_interface_coptimizations import getObjectSpecification
    from _zope_interface_coptimizations import ObjectSpecificationDescriptor

objectSpecificationDescriptor = ObjectSpecificationDescriptor()
