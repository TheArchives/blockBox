# -*- test-case-name: lib.twisted.test.test_plugin -*-
# Copyright (c) 2005 Divmod, Inc.
# Copyright (c) 2007-2010 Twisted Matrix Laboratories.
# See LICENSE for details.
import os
import sys
from lib.zope.interface import Interface, providedBy
def _determinePickleModule():
    try:
        import cPickle
        return cPickle
    except ImportError:
        import pickle
        return pickle

pickle = _determinePickleModule()
from lib.twisted.python.components import getAdapterFactory
from lib.twisted.python.reflect import namedAny
from lib.twisted.python import log
from lib.twisted.python.modules import getModule

class IPlugin(Interface):

class CachedPlugin(object):
    def __init__(self, dropin, name, description, provided):
        self.dropin = dropin
        self.name = name
        self.description = description
        self.provided = provided
        self.dropin.plugins.append(self)

    def __repr__(self):
        return '<CachedPlugin %r/%r (provides %r)>' % (
            self.name, self.dropin.moduleName,
            ', '.join([i.__name__ for i in self.provided]))

    def load(self):
        return namedAny(self.dropin.moduleName + '.' + self.name)

    def __conform__(self, interface, registry=None, default=None):
        for providedInterface in self.provided:
            if providedInterface.isOrExtends(interface):
                return self.load()
            if getAdapterFactory(providedInterface, interface, None) is not None:
                return interface(self.load(), default)
        return default

    getComponent = __conform__

class CachedDropin(object):
    def __init__(self, moduleName, description):
        self.moduleName = moduleName
        self.description = description
        self.plugins = []

def _generateCacheEntry(provider):
    dropin = CachedDropin(provider.__name__,
                          provider.__doc__)
    for k, v in provider.__dict__.iteritems():
        plugin = IPlugin(v, None)
        if plugin is not None:
            cachedPlugin = CachedPlugin(dropin, k, v.__doc__, list(providedBy(plugin)))
    return dropin

try:
    fromkeys = dict.fromkeys
except AttributeError:
    def fromkeys(keys, value=None):
        d = {}
        for k in keys:
            d[k] = value
        return d

def getCache(module):
    allCachesCombined = {}
    mod = getModule(module.__name__)
    buckets = {}
    for plugmod in mod.iterModules():
        fpp = plugmod.filePath.parent()
        if fpp not in buckets:
            buckets[fpp] = []
        bucket = buckets[fpp]
        bucket.append(plugmod)
    for pseudoPackagePath, bucket in buckets.iteritems():
        dropinPath = pseudoPackagePath.child('dropin.cache')
        try:
            lastCached = dropinPath.getModificationTime()
            dropinDotCache = pickle.load(dropinPath.open('r'))
        except:
            dropinDotCache = {}
            lastCached = 0

        needsWrite = False
        existingKeys = {}
        for pluginModule in bucket:
            pluginKey = pluginModule.name.split('.')[-1]
            existingKeys[pluginKey] = True
            if ((pluginKey not in dropinDotCache) or
                (pluginModule.filePath.getModificationTime() >= lastCached)):
                needsWrite = True
                try:
                    provider = pluginModule.load()
                except:
                    log.err()
                else:
                    entry = _generateCacheEntry(provider)
                    dropinDotCache[pluginKey] = entry
        for pluginKey in dropinDotCache.keys():
            if pluginKey not in existingKeys:
                del dropinDotCache[pluginKey]
                needsWrite = True
        if needsWrite:
            try:
                dropinPath.setContent(pickle.dumps(dropinDotCache))
            except:
                log.err()
        allCachesCombined.update(dropinDotCache)
    return allCachesCombined

def getPlugins(interface, package=None):
    if package is None:
        import lib.twisted.plugins as package
    allDropins = getCache(package)
    for dropin in allDropins.itervalues():
        for plugin in dropin.plugins:
            try:
                adapted = interface(plugin, None)
            except:
                log.err()
            else:
                if adapted is not None:
                    yield adapted

getPlugIns = getPlugins

def pluginPackagePaths(name):
    package = name.split('.')
    return [
        os.path.abspath(os.path.join(x, *package))
        for x
        in sys.path
        if
        not os.path.exists(os.path.join(x, *package + ['__init__.py']))]

__all__ = ['getPlugins', 'pluginPackagePaths']
