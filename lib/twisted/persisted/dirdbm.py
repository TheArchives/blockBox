# -*- test-case-name: lib.twisted.test.test_dirdbm -*-
#
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import os
import types
import base64
import glob
try:
    import cPickle as pickle
except ImportError:
    import pickle
try:
    _open
except NameError:
    _open = open

class DirDBM:
   
    def __init__(self, name):
        """
        @type name: str
        @param name: Base path to use for the directory storage.
        """
        self.dname = os.path.abspath(name)
        if not os.path.isdir(self.dname):
            os.mkdir(self.dname)
        else:
            for f in glob.glob(os.path.join(self.dname, "*.new")):
                os.remove(f)
            replacements = glob.glob(os.path.join(self.dname, "*.rpl"))
            for f in replacements:
                old = f[:-4]
                if os.path.exists(old):
                    os.remove(f)
                else:
                    os.rename(f, old)
    
    def _encode(self, k):
        return base64.encodestring(k).replace('\n', '_').replace("/", "-")
    
    def _decode(self, k):
        return base64.decodestring(k.replace('_', '\n').replace("-", "/"))
    
    def _readFile(self, path):
        f = _open(path, "rb")
        s = f.read()
        f.close()
        return s
    
    def _writeFile(self, path, data):
        f = _open(path, "wb")
        f.write(data)
        f.flush()
        f.close()
    
    def __len__(self):
        return len(os.listdir(self.dname))

    def __setitem__(self, k, v):
        assert type(k) == types.StringType, "DirDBM key must be a string"
        assert type(v) == types.StringType, "DirDBM value must be a string"
        k = self._encode(k)
        old = os.path.join(self.dname, k)
        if os.path.exists(old):
            new = old + ".rpl" # replacement entry
        else:
            new = old + ".new" # new entry
        try:
            self._writeFile(new, v)
        except:
            os.remove(new)
            raise
        else:
            if os.path.exists(old): os.remove(old)
            os.rename(new, old)

    def __getitem__(self, k):
        assert type(k) == types.StringType, "DirDBM key must be a string"
        path = os.path.join(self.dname, self._encode(k))
        try:
            return self._readFile(path)
        except:
            raise KeyError, k

    def __delitem__(self, k):
        assert type(k) == types.StringType, "DirDBM key must be a string"
        k = self._encode(k)
        try:    os.remove(os.path.join(self.dname, k))
        except (OSError, IOError): raise KeyError(self._decode(k))

    def keys(self):
        return map(self._decode, os.listdir(self.dname))

    def values(self):
        vals = []
        keys = self.keys()
        for key in keys:
            vals.append(self[key])
        return vals

    def items(self):
        items = []
        keys = self.keys()
        for key in keys:
            items.append((key, self[key]))
        return items

    def has_key(self, key):
        assert type(key) == types.StringType, "DirDBM key must be a string"
        key = self._encode(key)
        return os.path.isfile(os.path.join(self.dname, key))

    def setdefault(self, key, value):
        if not self.has_key(key):
            self[key] = value
            return value
        return self[key]

    def get(self, key, default = None):
        if self.has_key(key):
            return self[key]
        else:
            return default

    def __contains__(self, key):
        assert type(key) == types.StringType, "DirDBM key must be a string"
        key = self._encode(key)
        return os.path.isfile(os.path.join(self.dname, key))

    def update(self, dict):
        for key, val in dict.items():
            self[key]=val
            
    def copyTo(self, path):
        path = os.path.abspath(path)
        assert path != self.dname
        
        d = self.__class__(path)
        d.clear()
        for k in self.keys():
            d[k] = self[k]
        return d

    def clear(self):
        for k in self.keys():
            del self[k]

    def close(self):

    def getModificationTime(self, key):
        assert type(key) == types.StringType, "DirDBM key must be a string"
        path = os.path.join(self.dname, self._encode(key))
        if os.path.isfile(path):
            return os.path.getmtime(path)
        else:
            raise KeyError, key

class Shelf(DirDBM):
    def __setitem__(self, k, v):
        v = pickle.dumps(v)
        DirDBM.__setitem__(self, k, v)

    def __getitem__(self, k):
        return pickle.loads(DirDBM.__getitem__(self, k))


def open(file, flag = None, mode = None):
    return DirDBM(file)

__all__ = ["open", "DirDBM", "Shelf"]
