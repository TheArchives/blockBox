# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class OverloadPlugin(ProtocolPlugin):
	
	commands = {
		"overload": "commandOverload",
		#"send": "commandSend",
		"blazer": "commandBlazer",
	}
	
	@player_list
	@admin_only
	@username_command
	def commandOverload(self, client, byuser, overriderank):
		"/overload username - Admin\nSends the players client a massive fake map."
		client.sendOverload()
		self.client.sendServerMessage("Overload sent to %s" % client.username)

	#@player_list
	#@mod_only
	#@username_command
	#def commandSend(self, client, byuser, overriderank):
		#"/send username [world] - Mod\nSends the players client another world."
		#if user.isMod():
			#self.client.sendServerMessage("You cannot send Staff!")
		#if len(parts) == 2:
			#self.client.sendServerMessage("Please specify a world ID.")
		#else:
			#world_id = parts[2]
			#user.changeToWorld("%s" % world_id)
			#else:
				#user.sendServerMessage("You were sent to '%s'." % self.client.world.id)
				#user.changeToWorld("default")
				#self.client.sendServerMessage("Player %s was sent." % user.username)
		#else:
			#self.client.sendServerMessage("Your Player is in another world!")

	@mod_only
	def commandBlazer(self, parts, byuser, overriderank):
		"/blazer - Mod\nBlazer!"
		for i in range(10):
			self.client.sendServerMessage("SPAM!")
