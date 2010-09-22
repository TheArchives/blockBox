# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *

class SpectatePlugin(ProtocolPlugin):
	
	commands = {
		"spectate": "commandSpectate",
		"follow": "commandSpectate",
		"watch": "commandSpectate",
	}
	
	hooks = {
		"poschange": "posChanged",
	}
	
	def gotClient(self):
		self.flying = False
		self.last_flying_block = None
	
	def posChanged(self, x, y, z, h, p):
		"Hook trigger for when the player moves"

		spectators = set()

		for uid in self.client.factory.clients:
			user = self.client.factory.clients[uid]

			try:
				if user.spectating == self.client.id:
					if user.x != x and user.y != y and user.z != z:
						user.teleportTo(x >> 5, y >> 5, z >> 5, h, p)
			except AttributeError:
				pass
   
	@player_list
	@op_only
	@username_command
	def commandSpectate(self, user, byuser, overriderank):
		"/spectate username - Guest\nAliases: follow, watch\nFollows specified player around"

		nospec_check = True

		try:
			self.client.spectating
		except AttributeError:
			nospec_check = False

		if not nospec_check or self.client.spectating != user.id:
			self.client.sendServerMessage("You are now spectating %s" % user.username)
			self.client.spectating = user.id
		else:
			self.client.sendServerMessage("You are no longer spectating %s" % user.username)
			self.client.spectating = False
