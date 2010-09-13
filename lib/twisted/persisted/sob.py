# -*- test-case-name: lib.twisted.test.test_sob -*-
# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.

#
import os, sys
try:
    import cPickle as pickle
except ImportError:
    import pickle
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from lib.twisted.python import log, runtime
from lib.twisted.python.hashlib import md5
from lib.twisted.persisted import styles
from lib.zope.interface import implements, Interface
def _encrypt(passphrase, data):
    from Crypto.Cipher import AES as cipher
    leftover = len(data) % cipher.block_size
    if leftover:
        data += ' '*(cipher.block_size - leftover)
    return cipher.new(md5(passphrase).digest()[:16]).encrypt(data)

def _decrypt(passphrase, data):
    from Crypto.Cipher import AES
    return AES.new(md5(passphrase).digest()[:16]).decrypt(data)

class IPersistable(Interface):
    def setStyle(style):

    def save(tag=None, filename=None, passphrase=None):

class Persistent:
    implements(IPersistable)
    style = "pickle"

    def __init__(self, original, name):
        self.original = original
        self.name = name

    def setStyle(self, style):
        self.style = style

    def _getFilename(self, filename, ext, tag):
        if filename:
            finalname = filename
            filename = finalname + "-2"
        elif tag:
            filename = "%s-%s-2.%s" % (self.name, tag, ext)
            finalname = "%s-%s.%s" % (self.name, tag, ext)
        else:
            filename = "%s-2.%s" % (self.name, ext)
            finalname = "%s.%s" % (self.name, ext)
        return finalname, filename

    def _saveTemp(self, filename, passphrase, dumpFunc):
        f = open(filename, 'wb')
        if passphrase is None:
            dumpFunc(self.original, f)
        else:
            s = StringIO.StringIO()
            dumpFunc(self.original, s)
            f.write(_encrypt(passphrase, s.getvalue()))
        f.close()

    def _getStyle(self):
        if self.style == "source":
            from lib.twisted.persisted.aot import jellyToSource as dumpFunc
            ext = "tas"
        else:
            def dumpFunc(obj, file):
                pickle.dump(obj, file, 2)
            ext = "tap"
        return ext, dumpFunc

    def save(self, tag=None, filename=None, passphrase=None):
        ext, dumpFunc = self._getStyle()
        if passphrase:
            ext = 'e' + ext
        finalname, filename = self._getFilename(filename, ext, tag)
        log.msg("Saving "+self.name+" application to "+finalname+"...")
        self._saveTemp(filename, passphrase, dumpFunc)
        if runtime.platformType == "win32" and os.path.isfile(finalname):
            os.remove(finalname)
        os.rename(filename, finalname)
        log.msg("Saved.")

Persistant = Persistent

class _EverythingEphemeral(styles.Ephemeral):

    initRun = 0

    def __init__(self, mainMod):
        self.mainMod = mainMod

    def __getattr__(self, key):
        try:
            return getattr(self.mainMod, key)
        except AttributeError:
            if self.initRun:
                raise
            else:
                log.msg("Warning!  Loading from __main__: %s" % key)
                return styles.Ephemeral()


def load(filename, style, passphrase=None):
    mode = 'r'
    if style=='source':
        from lib.twisted.persisted.aot import unjellyFromSource as _load
    else:
        _load, mode = pickle.load, 'rb'
    if passphrase:
        fp = StringIO.StringIO(_decrypt(passphrase,
                                        open(filename, 'rb').read()))
    else:
        fp = open(filename, mode)
    ee = _EverythingEphemeral(sys.modules['__main__'])
    sys.modules['__main__'] = ee
    ee.initRun = 1
    try:
        value = _load(fp)
    finally:
        sys.modules['__main__'] = ee.mainMod

    styles.doUpgrade()
    ee.initRun = 0
    persistable = IPersistable(value, None)
    if persistable is not None:
        persistable.setStyle(style)
    return value


def loadValueFromFile(filename, variable, passphrase=None):
    if passphrase:
        mode = 'rb'
    else:
        mode = 'r'
    fileObj = open(filename, mode)
    d = {'__file__': filename}
    if passphrase:
        data = fileObj.read()
        data = _decrypt(passphrase, data)
        exec data in d, d
    else:
        exec fileObj in d, d
    value = d[variable]
    return value

def guessType(filename):
    ext = os.path.splitext(filename)[1]
    return {
        '.tac':  'python',
        '.etac':  'python',
        '.py':  'python',
        '.tap': 'pickle',
        '.etap': 'pickle',
        '.tas': 'source',
        '.etas': 'source',
    }[ext]

__all__ = ['loadValueFromFile', 'load', 'Persistent', 'Persistant',
           'IPersistable', 'guessType']
