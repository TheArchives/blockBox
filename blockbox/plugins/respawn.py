# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class RespawnPlugin(ProtocolPlugin):
	commands = {
		"respawn": "commandRespawn",
	}
	@player_list
	@mod_only
	@only_username_command
	def commandRespawn(self, username, fromloc, rankoverride):
			"/respawn username - Respawns player."
			if username in self.client.factory.usernames:
				self.client.factory.usernames[username].respawn()
			else:
				self.client.sendServerMessage("%s is not on the server" % username)
				return
			self.client.factory.usernames[username].sendServerMessage("You have been respawned by %s" % self.client.username)
			self.client.sendServerMessage("%s respawned." % username)
