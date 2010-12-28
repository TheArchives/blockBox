# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class BlockInfoPlugin(ProtocolPlugin):
	"Commands which tells players more about that block."
	BlockList = []
	while len(BlockList) != 50:
		BlockList.append('')
	BlockList[0]="air"
	BlockList[1]="rock"
	BlockList[2]="grass"
	BlockList[3]="dirt"
	BlockList[4]="stone"
	BlockList[5]="wood"
	BlockList[6]="plant"
	BlockList[7]="adminblock"
	BlockList[8]="water"
	BlockList[9]="still_water"
	BlockList[10]="lava"
	BlockList[11]="still_lava"
	BlockList[12]="sand"
	BlockList[13]="gravel"
	BlockList[14]="goldore"
	BlockList[15]="ironore"
	BlockList[16]="coal"
	BlockList[17]="log"
	BlockList[18]="leaves"
	BlockList[19]="sponge"
	BlockList[20]="glass"
	BlockList[21]="red"
	BlockList[22]="orange"
	BlockList[23]="yellow"
	BlockList[24]="lime"
	BlockList[25]="green"
	BlockList[26]="turquoise"
	BlockList[27]="cyan"
	BlockList[28]="blue"
	BlockList[29]="indigo"
	BlockList[30]="violet"
	BlockList[31]="purple"
	BlockList[32]="magenta"
	BlockList[33]="pink"
	BlockList[34]="black"
	BlockList[35]="grey"
	BlockList[36]="white"
	BlockList[37]="yellow_flower"
	BlockList[38]="red_flower"
	BlockList[39]="brown_mushroom"
	BlockList[40]="red_mushroom"
	BlockList[41]="gold"
	BlockList[42]="iron"
	BlockList[43]="step"
	BlockList[44]="doublestep"
	BlockList[45]="brick"
	BlockList[46]="tnt"
	BlockList[47]="bookcase"
	BlockList[48]="moss"
	BlockList[49]="obsidian"

	hooks = {
		"preblockchange": "blockChanged",
	}

	commands = {
		"info": "commandInfo",
		"binfo": "commandInfo",
		"bget": "commandInfo",
		"rget": "commandInfo",
		"pget": "commandInfo",
		"binfoend": "commandInfoEnd",
		"infoend": "commandInfoEnd",
		"blockindex": "commandBlockindex",
		"bindex": "commandBlockindex",
	}
	def gotClient(self):
		self.binfo = 0
	def blockChanged(self, x, y, z, block, selected_block, fromloc):
		if self.binfo == 1:
			check_offset = self.client.world.blockstore.get_offset(x, y, z)
			block2 = ord(self.client.world.blockstore.raw_blocks[check_offset])
			if block2 == 0:
				self.client.sendServerMessage("Block Info: %s (%s)" % (self.BlockList[block], block))
				self.client.sendServerMessage("x: %s y: %s z: %s" % (x, y, z))
				return block2
			else:
				self.client.sendServerMessage("Block Info: %s (%s)" % (self.BlockList[block2], block2))
				self.client.sendServerMessage("x: %s y: %s z: %s" % (x, y, z))
				return block2
	@build_list
	def commandInfo(self,parts,fromloc,overriderank):
			self.binfo = 1
			self.client.sendServerMessage("You are now getting info about blocks.")
			self.client.sendServerMessage("Use '/infoend' to stop.")

	@build_list
	def commandInfoEnd(self,parts,fromloc,overriderank):
			self.binfo = 0
			self.client.sendServerMessage("You are no longer getting info about blocks.")

	@build_list
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
			self.client.sendServerMessage("%s is represented by %s" % (parts[1],block))