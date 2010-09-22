# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from lib.twisted.internet import reactor
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
