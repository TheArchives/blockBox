# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
import Tkinter, tkSimpleDialog, tkMessageBox
from lib.twisted.python import log
from lib.twisted.internet import task
_task = None

def install(widget, ms=10, reactor=None):
    installTkFunctions()
    global _task
    _task = task.LoopingCall(widget.update)
    _task.start(ms / 1000.0, False)

def uninstall():
    global _task
    _task.stop()
    _task = None

def installTkFunctions():
    import lib.twisted.python.util
    lib.twisted.python.util.getPassword = getPassword

def getPassword(prompt = '', confirm = 0):
    while 1:
        try1 = tkSimpleDialog.askstring('Password Dialog', prompt, show='*')
        if not confirm:
            return try1
        try2 = tkSimpleDialog.askstring('Password Dialog', 'Confirm Password', show='*')
        if try1 == try2:
            return try1
        else:
            tkMessageBox.showerror('Password Mismatch', 'Passwords did not match, starting over')

__all__ = ["install", "uninstall"]
