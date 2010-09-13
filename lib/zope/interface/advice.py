##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from types import FunctionType
try:
    from types import ClassType
    __python3 = False
except ImportError:
    __python3 = True
    
import sys

def getFrameInfo(frame):

    f_locals = frame.f_locals
    f_globals = frame.f_globals

    sameNamespace = f_locals is f_globals
    hasModule = '__module__' in f_locals
    hasName = '__name__' in f_globals

    sameName = hasModule and hasName
    sameName = sameName and f_globals['__name__']==f_locals['__module__']

    module = hasName and sys.modules.get(f_globals['__name__']) or None

    namespaceIsModule = module and module.__dict__ is f_globals

    if not namespaceIsModule:
        # some kind of funky exec
        kind = "exec"
    elif sameNamespace and not hasModule:
        kind = "module"
    elif sameName and not sameNamespace:
        kind = "class"
    elif not sameNamespace:
        kind = "function call"
    else:
        # How can you have f_locals is f_globals, and have '__module__' set?
        # This is probably module-level code, but with a '__module__' variable.
        kind = "unknown"
    return kind, module, f_locals, f_globals


def addClassAdvisor(callback, depth=2):

    previousMetaclass = caller_locals.get('__metaclass__')
    if __python3:
        defaultMetaclass  = caller_globals.get('__metaclass__', type)
    else:
        defaultMetaclass  = caller_globals.get('__metaclass__', ClassType)


    def advise(name, bases, cdict):

        if '__metaclass__' in cdict:
            del cdict['__metaclass__']

        if previousMetaclass is None:
            if bases:
                # find best metaclass or use global __metaclass__ if no bases
                meta = determineMetaclass(bases)
            else:
                meta = defaultMetaclass

        elif isClassAdvisor(previousMetaclass):
            meta = previousMetaclass

        else:
            meta = determineMetaclass(bases, previousMetaclass)

        newClass = meta(name,bases,cdict)

        # this lets the callback replace the class completely, if it wants to
        return callback(newClass)

    # introspection data only, not used by inner function
    advise.previousMetaclass = previousMetaclass
    advise.callback = callback

    # install the advisor
    caller_locals['__metaclass__'] = advise


def isClassAdvisor(ob):
    """True if 'ob' is a class advisor function"""
    return isinstance(ob,FunctionType) and hasattr(ob,'previousMetaclass')


def determineMetaclass(bases, explicit_mc=None):
    """Determine metaclass from 1+ bases and optional explicit __metaclass__"""

    meta = [getattr(b,'__class__',type(b)) for b in bases]

    if explicit_mc is not None:
        # The explicit metaclass needs to be verified for compatibility
        # as well, and allowed to resolve the incompatible bases, if any
        meta.append(explicit_mc)

    if len(meta)==1:
        # easy case
        return meta[0]

    candidates = minimalBases(meta) # minimal set of metaclasses

    if not candidates:
        # they're all "classic" classes
        assert(not __python3) # This should not happen under Python 3
        return ClassType

    elif len(candidates)>1:
        # We could auto-combine, but for now we won't...
        raise TypeError("Incompatible metatypes",bases)

    # Just one, return it
    return candidates[0]


def minimalBases(classes):
    """Reduce a list of base classes to its ordered minimum equivalent"""

    if not __python3:
        classes = [c for c in classes if c is not ClassType]
    candidates = []

    for m in classes:
        for n in classes:
            if issubclass(n,m) and m is not n:
                break
        else:
            # m has no subclasses in 'classes'
            if m in candidates:
                candidates.remove(m)    # ensure that we're later in the list
            candidates.append(m)

    return candidates

