# -*- test-case-name: lib.twisted.test.test_persisted -*-

# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import types, new, string, copy_reg, tokenize, re
from lib.twisted.python import reflect, log
from lib.twisted.persisted import crefutil

class Named:
    def __init__(self, name):
        self.name = name

class Class(Named):
    def getSource(self):
        return "Class(%r)" % self.name

class Function(Named):
    def getSource(self):
        return "Function(%r)" % self.name

class Module(Named):
    def getSource(self):
        return "Module(%r)" % self.name

class InstanceMethod:
    def __init__(self, name, klass, inst):
        if not (isinstance(inst, Ref) or isinstance(inst, Instance) or isinstance(inst, Deref)):
            raise TypeError("%s isn't an Instance, Ref, or Deref!" % inst)
        self.name = name
        self.klass = klass
        self.instance = inst

    def getSource(self):
        return "InstanceMethod(%r, %r, \n\0%s)" % (self.name, self.klass, prettify(self.instance))

class _NoStateObj:
    pass
NoStateObj = _NoStateObj()

_SIMPLE_BUILTINS = [
    types.StringType, types.UnicodeType, types.IntType, types.FloatType,
    types.ComplexType, types.LongType, types.NoneType, types.SliceType,
    types.EllipsisType]

try:
    _SIMPLE_BUILTINS.append(types.BooleanType)
except AttributeError:
    pass

class Instance:
    def __init__(self, className, __stateObj__=NoStateObj, **state):
        if not isinstance(className, types.StringType):
            raise TypeError("%s isn't a string!" % className)
        self.klass = className
        if __stateObj__ is not NoStateObj:
            self.state = __stateObj__
            self.stateIsDict = 0
        else:
            self.state = state
            self.stateIsDict = 1

    def getSource(self):
        if self.stateIsDict:
            stateDict = self.state
        elif isinstance(self.state, Ref) and isinstance(self.state.obj, types.DictType):
            stateDict = self.state.obj
        else:
            stateDict = None
        if stateDict is not None:
            try:
                return "Instance(%r, %s)" % (self.klass, dictToKW(stateDict))
            except NonFormattableDict:
                return "Instance(%r, %s)" % (self.klass, prettify(stateDict))
        return "Instance(%r, %s)" % (self.klass, prettify(self.state))

class Ref:
    def __init__(self, *args):
        #blargh, lame.
        if len(args) == 2:
            self.refnum = args[0]
            self.obj = args[1]
        elif not args:
            self.refnum = None
            self.obj = None

    def setRef(self, num):
        if self.refnum:
            raise ValueError("Error setting id %s, I already have %s" % (num, self.refnum))
        self.refnum = num

    def setObj(self, obj):
        if self.obj:
            raise ValueError("Error setting obj %s, I already have %s" % (obj, self.obj))
        self.obj = obj

    def getSource(self):
        if self.obj is None:
            raise RuntimeError("Don't try to display me before setting an object on me!")
        if self.refnum:
            return "Ref(%d, \n\0%s)" % (self.refnum, prettify(self.obj))
        return prettify(self.obj)

class Deref:
    def __init__(self, num):
        self.refnum = num

    def getSource(self):
        return "Deref(%d)" % self.refnum
    __repr__ = getSource

class Copyreg:
    def __init__(self, loadfunc, state):
        self.loadfunc = loadfunc
        self.state = state

    def getSource(self):
        return "Copyreg(%r, %s)" % (self.loadfunc, prettify(self.state))

def getSource(ao):
    return indentify("app = " + prettify(ao))

class NonFormattableDict(Exception):

r = re.compile('[a-zA-Z_][a-zA-Z0-9_]*$')

def dictToKW(d):
    out = []
    items = d.items()
    items.sort()
    for k,v in items:
        if not isinstance(k, types.StringType):
            raise NonFormattableDict("%r ain't a string" % k)
        if not r.match(k):
            raise NonFormattableDict("%r ain't an identifier" % k)
        out.append(
            "\n\0%s=%s," % (k, prettify(v))
            )
    return string.join(out, '')

def prettify(obj):
    if hasattr(obj, 'getSource'):
        return obj.getSource()
    else:
        t = type(obj)
        if t in _SIMPLE_BUILTINS:
            return repr(obj)
        elif t is types.DictType:
            out = ['{']
            for k,v in obj.items():
                out.append('\n\0%s: %s,' % (prettify(k), prettify(v)))
            out.append(len(obj) and '\n\0}' or '}')
            return string.join(out, '')
        elif t is types.ListType:
            out = ["["]
            for x in obj:
                out.append('\n\0%s,' % prettify(x))
            out.append(len(obj) and '\n\0]' or ']')
            return string.join(out, '')
        elif t is types.TupleType:
            out = ["("]
            for x in obj:
                out.append('\n\0%s,' % prettify(x))
            out.append(len(obj) and '\n\0)' or ')')
            return string.join(out, '')
        else:
            raise TypeError("Unsupported type %s when trying to prettify %s." % (t, obj))

def indentify(s):
    out = []
    stack = []
    def eater(type, val, r, c, l, out=out, stack=stack):
        if val in ['[', '(', '{']:
            stack.append(val)
        elif val in [']', ')', '}']:
            stack.pop()
        if val == '\0':
            out.append('  '*len(stack))
        else:
            out.append(val)
    l = ['', s]
    tokenize.tokenize(l.pop, eater)
    return string.join(out, '')

def unjellyFromAOT(aot):
    return AOTUnjellier().unjelly(aot)

def unjellyFromSource(stringOrFile):
    ns = {"Instance": Instance,
          "InstanceMethod": InstanceMethod,
          "Class": Class,
          "Function": Function,
          "Module": Module,
          "Ref": Ref,
          "Deref": Deref,
          "Copyreg": Copyreg,
          }

    if hasattr(stringOrFile, "read"):
        exec stringOrFile.read() in ns
    else:
        exec stringOrFile in ns

    if ns.has_key('app'):
        return unjellyFromAOT(ns['app'])
    else:
        raise ValueError("%s needs to define an 'app', it didn't!" % stringOrFile)

class AOTUnjellier:
    def __init__(self):
        self.references = {}
        self.stack = []
        self.afterUnjelly = []

    def unjellyLater(self, node):
        d = crefutil._Defer()
        self.unjellyInto(d, 0, node)
        return d

    def unjellyInto(self, obj, loc, ao):
        o = self.unjellyAO(ao)
        obj[loc] = o
        if isinstance(o, crefutil.NotKnown):
            o.addDependant(obj, loc)
        return o

    def callAfter(self, callable, result):
        if isinstance(result, crefutil.NotKnown):
            l = [None]
            result.addDependant(l, 1)
        else:
            l = [result]
        self.afterUnjelly.append((callable, l))

    def unjellyAttribute(self, instance, attrName, ao):
        self.unjellyInto(instance.__dict__, attrName, ao)

    def unjellyAO(self, ao):
        self.stack.append(ao)
        t = type(ao)
        if t is types.InstanceType:
            c = ao.__class__
            if c is Module:
                return reflect.namedModule(ao.name)

            elif c in [Class, Function] or issubclass(c, type):
                return reflect.namedObject(ao.name)

            elif c is InstanceMethod:
                im_name = ao.name
                im_class = reflect.namedObject(ao.klass)
                im_self = self.unjellyAO(ao.instance)
                if im_name in im_class.__dict__:
                    if im_self is None:
                        return getattr(im_class, im_name)
                    elif isinstance(im_self, crefutil.NotKnown):
                        return crefutil._InstanceMethod(im_name, im_self, im_class)
                    else:
                        return new.instancemethod(im_class.__dict__[im_name],
                                                  im_self,
                                                  im_class)
                else:
                    raise TypeError("instance method changed")

            elif c is Instance:
                klass = reflect.namedObject(ao.klass)
                state = self.unjellyAO(ao.state)
                if hasattr(klass, "__setstate__"):
                    inst = new.instance(klass, {})
                    self.callAfter(inst.__setstate__, state)
                else:
                    inst = new.instance(klass, state)
                return inst

            elif c is Ref:
                o = self.unjellyAO(ao.obj) #THIS IS CHANGING THE REF OMG
                refkey = ao.refnum
                ref = self.references.get(refkey)
                if ref is None:
                    self.references[refkey] = o
                elif isinstance(ref, crefutil.NotKnown):
                    ref.resolveDependants(o)
                    self.references[refkey] = o
                elif refkey is None:
                    pass
                else:
                    raise ValueError("Multiple references with the same ID: %s, %s, %s!" % (ref, refkey, ao))
                return o

            elif c is Deref:
                num = ao.refnum
                ref = self.references.get(num)
                if ref is None:
                    der = crefutil._Dereference(num)
                    self.references[num] = der
                    return der
                return ref

            elif c is Copyreg:
                loadfunc = reflect.namedObject(ao.loadfunc)
                d = self.unjellyLater(ao.state).addCallback(
                    lambda result, _l: apply(_l, result), loadfunc)
                return d
        elif t in _SIMPLE_BUILTINS:
            return ao
            
        elif t is types.ListType:
            l = []
            for x in ao:
                l.append(None)
                self.unjellyInto(l, len(l)-1, x)
            return l
        
        elif t is types.TupleType:
            l = []
            tuple_ = tuple
            for x in ao:
                l.append(None)
                if isinstance(self.unjellyInto(l, len(l)-1, x), crefutil.NotKnown):
                    tuple_ = crefutil._Tuple
            return tuple_(l)

        elif t is types.DictType:
            d = {}
            for k,v in ao.items():
                kvd = crefutil._DictKeyAndValue(d)
                self.unjellyInto(kvd, 0, k)
                self.unjellyInto(kvd, 1, v)
            return d

        else:
            raise TypeError("Unsupported AOT type: %s" % t)

        del self.stack[-1]
        
    def unjelly(self, ao):
        try:
            l = [None]
            self.unjellyInto(l, 0, ao)
            for callable, v in self.afterUnjelly:
                callable(v[0])
            return l[0]
        except:
            log.msg("Error jellying object! Stacktrace follows::")
            log.msg(string.join(map(repr, self.stack), "\n"))
            raise

def jellyToAOT(obj):
    return AOTJellier().jelly(obj)

def jellyToSource(obj, file=None):
    aot = jellyToAOT(obj)
    if file:
        file.write(getSource(aot))
    else:
        return getSource(aot)
        

class AOTJellier:
    def __init__(self):
        self.prepared = {}
        self._ref_id = 0
        self.stack = []

    def prepareForRef(self, aoref, object):
        self.prepared[id(object)] = aoref

    def jellyToAO(self, obj):
        objType = type(obj)
        self.stack.append(repr(obj))

        if objType in _SIMPLE_BUILTINS:
            retval = obj
            
        elif objType is types.MethodType:
            retval = InstanceMethod(obj.im_func.__name__, reflect.qual(obj.im_class),
                                    self.jellyToAO(obj.im_self))
            
        elif objType is types.ModuleType:
            retval = Module(obj.__name__)
            
        elif objType is types.ClassType:
            retval = Class(reflect.qual(obj))

        elif issubclass(objType, type):
            retval = Class(reflect.qual(obj))
            
        elif objType is types.FunctionType:
            retval = Function(reflect.fullFuncName(obj))
            
        else:
            if self.prepared.has_key(id(obj)):
                oldRef = self.prepared[id(obj)]
                if oldRef.refnum:
                    key = oldRef.refnum
                else:
                    self._ref_id = self._ref_id + 1
                    key = self._ref_id
                    oldRef.setRef(key)
                return Deref(key)

            retval = Ref()
            self.prepareForRef(retval, obj)
            
            if objType is types.ListType:
                retval.setObj(map(self.jellyToAO, obj)) #hah!
                
            elif objType is types.TupleType:
                retval.setObj(tuple(map(self.jellyToAO, obj)))

            elif objType is types.DictionaryType:
                d = {}
                for k,v in obj.items():
                    d[self.jellyToAO(k)] = self.jellyToAO(v)
                retval.setObj(d)

            elif objType is types.InstanceType:
                if hasattr(obj, "__getstate__"):
                    state = self.jellyToAO(obj.__getstate__())
                else:
                    state = self.jellyToAO(obj.__dict__)
                retval.setObj(Instance(reflect.qual(obj.__class__), state))

            elif copy_reg.dispatch_table.has_key(objType):
                unpickleFunc, state = copy_reg.dispatch_table[objType](obj)
                
                retval.setObj(Copyreg( reflect.fullFuncName(unpickleFunc),
                                       self.jellyToAO(state)))
                
            else:
                raise TypeError("Unsupported type: %s" % objType.__name__)

        del self.stack[-1]
        return retval

    def jelly(self, obj):
        try:
            ao = self.jellyToAO(obj)
            return ao
        except:
            log.msg("Error jellying object! Stacktrace follows::")
            log.msg(string.join(self.stack, '\n'))
            raise
