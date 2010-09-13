# Copyright (c) 2008 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.zope.interface import Interface

class IReadHandle(Interface):
    def readFromHandle(bufflist, evt):

class IWriteHandle(Interface):
    def writeToHandle(buff, evt):

class IReadWriteHandle(IReadHandle, IWriteHandle):
    pass
