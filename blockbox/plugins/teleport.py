# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *

class TeleportPlugin(ProtocolPlugin):
	
	commands = {
		"goto": "commandGoto",
		"tp": "commandTeleport",
		"teleport": "commandTeleport",
	}

	@world_list
	def commandGoto(self, parts, fromloc, overriderank):
		"/goto x y z - Guest\nTeleports you to coords. NOTE: y is up."
		try:
			x = int(parts[1])
			y = int(parts[2])
			z = int(parts[3])
			self.client.teleportTo(x, y, z)
		except (IndexError, ValueError):
			self.client.sendServerMessage("Usage: /goto x y z")
	
	@player_list
	@username_command
	def commandTeleport(self, user, fromloc, overriderank):
		"/tp username - Guest\nAliases: teleport\nTeleports you to the players location."
		x = user.x >> 5
		y = user.y >> 5
		z = user.z >> 5
		if user.world == self.client.world:
			self.client.teleportTo(x, y, z)
		else:
			if self.client.canEnter(user.world):
				self.client.changeToWorld(user.world.id, position=(x, y, z))
			else:
				self.client.sendServerMessage("Sorry, that world is private.")
