# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

# 
from __future__ import nested_scopes
from lib.twisted.internet import defer
import base
INSERT, DELETE, UPDATE = range(3)

class RowJournal(base.Journal):
    def __init__(self, log, journaledService, reflector):
        self.reflector = reflector
        self.commands = []
        self.syncing = 0
        base.Journal.__init__(self, log, journaledService)
    
    def updateRow(self, obj):
        self.commands.append((UPDATE, obj))

    def insertRow(self, obj):
        self.commands.append((INSERT, obj))

    def deleteRow(self, obj):
        self.commands.append((DELETE, obj))

    def loadObjectsFrom(self, tableName, parentRow=None, data=None, whereClause=None, forceChildren=0):
        d = self.sync()
        d.addCallback(lambda result: self.reflector.loadObjectsFrom(
            tableName, parentRow=parentRow, data=data, whereClause=whereClause,
            forceChildren=forceChildren))
        return d

    def sync(self):
        if self.syncing:
            raise ValueError, "sync already in progress"
        comandMap = {INSERT : self.reflector.insertRowSQL,
                     UPDATE : self.reflector.updateRowSQL,
                     DELETE : self.reflector.deleteRowSQL}
        sqlCommands = []
        for kind, obj in self.commands:
            sqlCommands.append(comandMap[kind](obj))
        self.commands = []
        if sqlCommands:
            self.syncing = 1
            d = self.reflector.dbpool.runInteraction(self._sync, self.latestIndex, sqlCommands)
            d.addCallback(self._syncDone)
            return d
        else:
            return defer.succeed(1)

    def _sync(self, txn, index, commands):
        for c in commands:
            txn.execute(c)
        txn.update("UPDATE journalinfo SET commandIndex = %d" % index)
    
    def _syncDone(self, result):
        self.syncing = 0
        return result
    
    def getLastSnapshot(self):
        conn = self.reflector.dbpool.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT commandIndex FROM journalinfo")
        return cursor.fetchall()[0][0]
