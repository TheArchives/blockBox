# blockBox is Copyright 2009-2010 of the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class NickPlugin(ProtocolPlugin):	"Commands for nickname changes."
	commands = {
		"nick": "commandNick",
	}

	@player_list
	@director_only
	def commandNick(self, params, fromloc, overriderank):
		"/nick - Changes your username and skin. Use with great care."
		if len(params) < 1:
			self.client.sendServerMessage("Please enter a username.")
		else:
			username = params[1]
			if username in self.client.factory.usernames:
				self.client.sendServerMessage("Someone is using that username on this server.")
			else:
				old_username, self.client.username = self.client.username, username
				self.client.factory.usernames[username] = self.client.factory.usernames[old_username]
				del self.client.factory.usernames[old_username]
				self.client.respawn()
