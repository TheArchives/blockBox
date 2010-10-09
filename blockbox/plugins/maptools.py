# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class PrivatePlugin(ProtocolPlugin):
	
	commands = {
		"private": "commandPrivate",
		"lock": "commandLock",
		"gchat": "commandGChat"
		#"ponly": "commandPOnly"
	}
	
	@world_list
	@op_only
	@on_off_command
	def commandPrivate(self, onoff, fromloc, overriderank):
		"/private on|off - Op\nEnables or disables the private status for this world."
		if onoff == "on":
			self.client.world.private = True
			self.client.sendWorldMessage("This world is now private.")
			self.client.sendServerMessage("%s is now private." % self.client.world.id)
		else:
			self.client.world.private = False
			self.client.sendWorldMessage("This world is now public.")
			self.client.sendServerMessage("%s is now public." % self.client.world.id)

	@world_list
	@op_only
	@on_off_command
	def commandLock(self, onoff, fromloc, overriderank):
		"/lock on|off - Op\nEnables or disables the world lock."
		if onoff == "on":
			self.client.world.all_write = False
			self.client.sendWorldMessage("This world is now locked.")
			self.client.sendServerMessage("Locked %s" % self.client.world.id)
		else:
			self.client.world.all_write = True
			self.client.sendWorldMessage("This world is now unlocked.")
			self.client.sendServerMessage("Unlocked %s" % self.client.world.id)

	@world_list
	@mod_only
	@on_off_command
	def commandGChat(self, onoff, fromloc, rankoverride):
		"/gchat on|off - Mod\nTurns Global Chat on or off in this world.\nWorldChat is used instead if off."
		self.client.world.global_chat = onoff == "on"
		self.client.sendServerMessage("Global chat is now %s for this world." %onoff)

	#@op_only
	#@on_off_command
	#def commandPOnly(self, onoff, fromloc, rankoverride):
		#"/ponly on/off - Makes the world only accessable by portals."
		#if onoff == "on":
			#self.client.world.portal_only = True
			#self.client.sendWorldMessage("This world is now portal only.")
			#self.client.sendServerMessage("%s is now only accessable through portals." % self.client.world.id)
		#else:
			#self.client.world.portal_only = False
			#elf.client.sendWorldMessage("This world is now accesable through commands.")
			#self.client.sendServerMessage("%s is now accessable through commands." % self.client.world.id)
