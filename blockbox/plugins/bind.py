# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class BindPlugin(ProtocolPlugin):
	
	commands = {
		"bind": "commandBind",
		"build": "commandBind",
		"material": "commandBind",
		"air": "commandAir",
		"stand": "commandAir",
		"place": "commandAir",
	}
	
	hooks = {
		"blockchange": "blockChanged",
		"rankchange": "sendAdminBlockUpdate",
		"canbreakadmin": "canBreakAdminBlocks",
	}
	
	def gotClient(self):
		self.block_overrides = {}
	
	def blockChanged(self, x, y, z, block, selected_block, byuser):
		"Hook trigger for block changes."
		if block in self.block_overrides:
			return self.block_overrides[block]

	def canBreakAdminBlocks(self):
		"Shortcut for checking permissions."
		if hasattr(self.client, "world"):
			return (not self.client.world.admin_blocks) or self.client.isOp()
		else:
			return False
	
	def sendAdminBlockUpdate(self):
		"Sends a packet that updates the client's admin-building ability"
		self.client.sendPacked(TYPE_INITIAL, 6, "Admincrete Update", "Reloading the server...", self.canBreakAdminBlocks() and 100 or 0)

	@build_list
	def commandBind(self, parts, byuser, overriderank):
		"/bind blockA blockB - Guest\nAliases: build, material\nBinds blockB to blockA."
		if len(parts) == 1:
			if self.block_overrides:
				temp = tuple(self.block_overrides)
				for each in temp:
					del self.block_overrides[each]
				self.client.sendServerMessage("All blocks are back to normal")
				del temp
				return
			self.client.sendServerMessage("Please enter two block types.")
		elif len(parts) == 2:
			try:
				old = ord(self.client.GetBlockValue(parts[1]))
			except:
				return
			if old == None:
				return
			if old in self.block_overrides:
				del self.block_overrides[old]
				self.client.sendServerMessage("%s is back to normal." % parts[1])
			else:
				self.client.sendServerMessage("Please enter two block types.")
		else:
			old = self.client.GetBlockValue(parts[1])
			if old == None:
				return
			old = ord(old)
			new = self.client.GetBlockValue(parts[2])
			if new == None:
				return
			new = ord(new)
			name = parts[2].lower()
			old_name = parts[1].lower()
			self.block_overrides[old] = new
			self.client.sendServerMessage("%s will turn into %s." % (old_name, name))

	@build_list
	def commandAir(self, params, byuser, overriderank):
		"/air - Guest\nAliases: place, stand\nPuts a block under you for easier building in the air."
		self.client.sendPacked(TYPE_BLOCKSET, self.client.x>>5, (self.client.y>>5)-3, (self.client.z>>5), BLOCK_WHITE)
