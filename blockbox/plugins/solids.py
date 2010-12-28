# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted.
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
		"rankchange": "sendAdminBlockUpdate",
		"canbreakadmin": "canBreakAdminBlocks",
	}

	def gotClient(self):
		self.building_solid = False

	def sendAdminBlockUpdate(self):
		"Sends a packet that updates the client's admin-building ability"
		self.client.sendPacked(TYPE_INITIAL, 6, "Admincrete Update", "Reloading the server...", self.canBreakAdminBlocks() and 100 or 0)

	def blockChanged(self, x, y, z, block, selected_block, fromloc):
		"Hook trigger for block changes."
		# Admincrete hack check
		if not self.canBreakAdminBlocks():
			def check_block(block):
				if ord(block) == BLOCK_GROUND_ROCK:
					self.client.sendError("Don't build admincrete!")
					self.client.world[x, y, z] = chr(BLOCK_AIR)
			self.client.world[x,y,z].addCallback(check_block)
		# See if they are in solid-building mode
		if self.building_solid and block == BLOCK_ROCK:
			return BLOCK_GROUND_ROCK

	def canBreakAdminBlocks(self):
		"Shortcut for checking permissions."
		if hasattr(self.client, "world"):
			return (not self.client.world.admin_blocks) or self.client.isOp()
		else:
			return False

	@build_list
	@op_only
	def commandSolid(self, parts, fromloc, overriderank):
		"/solid - Op\nToggles admincrete creation."
		if self.building_solid:
			self.client.sendServerMessage("You are now placing normal rock.")
		else:
			self.client.sendServerMessage("You are now placing admin rock.")
		self.building_solid = not self.building_solid