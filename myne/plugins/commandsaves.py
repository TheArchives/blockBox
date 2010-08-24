#    iCraft is Copyright 2010 both
#
#    The Archives team:
#                   <Adam Guy> adam@adam-guy.com AKA "Adam01"
#                   <Andrew Godwin> andrew@aeracode.org AKA "Aera"
#                   <Dylan Lukes> lukes.dylan@gmail.com AKA "revenant"
#                   <Gareth Coles> colesgareth2@hotmail.com AKA "gdude2002"
#
#    And,
#
#    The iCraft team:
#                   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#                   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#                   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#                   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#                   <James Kirslis> james@helplarge.com AKA "iKJames"
#                   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#                   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
#                   <Nick Tolrud> ntolrud@yahoo.com AKA "ntfwc"
#                   <Noel Benzinger> ronnygmod@gmail.com AKA "Dwarfy"
#                   <Randy Lyne> qcksilverdragon@gmail.com AKA "goober"
#                   <Willem van der Ploeg> willempieeploeg@live.nl AKA "willempiee"
#
#    iCraft is licensed under the Creative Commons
#    Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
#    To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#    Or, send a letter to Creative Commons, 171 2nd Street,
#    Suite 300, San Francisco, California, 94105, USA.

from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *
from twisted.internet import reactor
import logging

class DynamitePlugin(ProtocolPlugin):
    
    commands = {
        "b": "commandBack",
    }
    
    hooks = {
        "chatmsg": "Message",
    }
    
    def gotClient(self):
        self.lastcommand = None
        self.savedcommands = list({})

    def Message(self, message):
        if message.startswith("/") and not message.split()[0] == "/b":
            self.lastcommand = message
    
    @info_list
    def commandBack(self, parts, byuser, rankoverride):
        message = self.lastcommand
        parts = [x.strip() for x in message.split() if x.strip()]
        command = parts[0].strip("/")
        self.client.log("%s just used: %s" % (self.client.username," ".join(parts)), level=logging.INFO)
        # See if we can handle it internally
        try:
            func = getattr(self.client, "command%s" % command.title())
        except AttributeError:
            # Can we find it from a plugin?
            try:
                func = self.client.commands[command.lower()]
            except KeyError:
                self.client.sendServerMessage("Unknown command '%s'" % command)
                return
        if (self.client.isSpectator() and (getattr(func, "admin_only", False) or getattr(func, "mod_only", False) or getattr(func, "op_only", False) or getattr(func, "worldowner_only", False) or getattr(func, "member_only", False) or getattr(func, "writer_only", False))):
            if byuser:
                self.client.sendServerMessage("'%s' is not available to specs." % command)
                return
        if getattr(func, "director_only", False) and not self.client.isDirector():
            if byuser:
                self.client.sendServerMessage("'%s' is a Director-only command!" % command)
                return
        if getattr(func, "admin_only", False) and not self.client.isAdmin():
            if byuser:
                self.client.sendServerMessage("'%s' is an Admin-only command!" % command)
                return
        if getattr(func, "mod_only", False) and not (self.client.isMod() or self.client.isAdmin()):
            if byuser:
                self.client.sendServerMessage("'%s' is a Mod-only command!" % command)
                return
        if getattr(func, "op_only", False) and not (self.client.isOp() or self.client.isWorldOwner() or self.client.isMod()):
            if byuser:
                self.client.sendServerMessage("'%s' is an Op-only command!" % command)
                return
        if getattr(func, "worldowner_only", False) and not (self.client.isWorldOwner() or self.client.isMod()):
            if byuser:
                self.client.sendServerMessage("'%s' is an WorldOwner-only command!" % command)
                return
        if getattr(func, "member_only", False) and not (self.client.isMember() or self.client.isOp() or self.client.isWorldOwner() or self.client.isMod()):
            if byuser:
                self.client.sendServerMessage("'%s' is a Member-only command!" % command)
                return
        if getattr(func, "writer_only", False) and not (self.client.isWriter() or self.client.isOp() or self.client.isWorldOwner() or self.client.isMod()):
            if byuser:
                self.client.sendServerMessage("'%s' is a Builder-only command!" % command)
                return
        try:
            func(parts, True, False) #byuser is true, overriderank is false
        except Exception, e:
            self.client.sendServerMessage("Internal server error.")
            self.client.log(traceback.format_exc(), level=logging.ERROR)
