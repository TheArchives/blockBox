# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class BlockInfoPlugin(ProtocolPlugin):
	"Commands which tells players more about that block."

	hooks = {
		"preblockchange": "blockChanged",
	}

	commands = {
		"info": "commandInfo",
		"binfo": "commandInfo",
		"bget": "commandInfo",
		"rget": "commandInfo",
		"pget": "commandInfo",
		"blockindex": "commandBlockindex",
		"bindex": "commandBlockindex",
	}

	def gotClient(self):
		self.binfo = False

	def blockChanged(self, x, y, z, block, selected_block, fromloc):
		if self.binfo == 1:
			check_offset = self.client.world.blockstore.get_offset(x, y, z)
			block2 = ord(self.client.world.blockstore.raw_blocks[check_offset])
			if block2 == 0:
				self.client.sendServerMessage("Block Info: %s (%s)" % (BlockList[block], block))
				self.client.sendServerMessage("x: %s y: %s z: %s" % (x, y, z))
				return block2
			else:
				self.client.sendServerMessage("Block Info: %s (%s)" % (BlockList[block2], block2))
				self.client.sendServerMessage("x: %s y: %s z: %s" % (x, y, z))
				return block2

	@config("category", "build")
	def commandInfo(self, parts, fromloc, overriderank):
		"/info - Guest\nAliases: bget, binfo, pget, rget\nClick on a block, returns block info."
		if self.binfo:
			self.binfo = False
			self.client.sendServerMessage("You are no longer getting information about blocks.")
		else:
			self.binfo = True
			self.client.sendServerMessage("You are now getting info about blocks.")

	@config("category", "build")
	def commandBlockindex(self, parts, fromloc, overriderank):
		"/blockindex blockname - Guest\nAliases: bindex\nGives you the index of the block."
		if len(parts) != 2:
			self.client.sendServerMessage("Please enter a block to check the index of.")
		else:
			try:
				block = globals()['BLOCK_%s' % parts[1].upper()]
			except KeyError:
				self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
				return
			self.client.sendServerMessage("%s is now being represented by %s." % (parts[1], block))