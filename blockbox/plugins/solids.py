# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class AdminBlocksPlugin(ProtocolPlugin):
	"Commands for toggling admincrete options on-off."

	commands = {
		"solid": "commandSolid",
	}

	hooks = {
		"blockchange": "blockChanged",
	}

	def gotClient(self):
		self.building_solid = False

	def blockChanged(self, x, y, z, block, selected_block, fromloc):
		"Hook trigger for block changes."
		# Admincrete hack check
		if not self.client.canBreakAdminBlocks():
			def check_block(block):
				if ord(block) == BLOCK_GROUND_ROCK:
					self.client.sendError("You are not allowed to build Admincrete.")
					self.client.world[x, y, z] = chr(BLOCK_AIR)
			self.client.world[x, y, z].addCallback(check_block)
		# See if they are in solid-building mode
		if self.building_solid and block == BLOCK_ROCK:
			return BLOCK_GROUND_ROCK

	@config("category", "build")
	@config("rank", "op")
	def commandSolid(self, parts, fromloc, overriderank):
		"/solid - Op\nToggles admincrete creation."
		if self.building_solid:
			self.client.sendServerMessage("You are now placing normal rock.")
		else:
			self.client.sendServerMessage("You are now placing admin rock.")
		self.building_solid = not self.building_solid