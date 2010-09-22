
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class FetchPlugin(ProtocolPlugin):
	
	commands = {
		"respawn": "commandRespawn",
	}
	
	@player_list
	@mod_only
	@only_username_command
	def commandRespawn(self, username, byuser, rankoverride):
		   "/respawn username - Respawns player."
		   if username in self.client.factory.usernames:
			   self.client.factory.usernames[username].respawn()
		   else:
				self.client.sendServerMessage("%s is not on the server" % username)
				return
		   self.client.factory.usernames[username].sendServerMessage("You have been respawned by %s" % self.client.username)
		   self.client.sendServerMessage("%s respawned." % username)
