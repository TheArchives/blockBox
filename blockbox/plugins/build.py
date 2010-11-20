# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class BuildPlugin(ProtocolPlugin):
	commands = {
		"b": "commandBuild",
		"build": "commandBuild",
	}

	hooks = {
		"blockchange": "blockChanged",
	}

	def gotClient(self):
		self.block_overrides = {}

	def blockChanged(self, x, y, z, block, selected_block, fromloc):
		"Hook trigger for block changes."
		if block in self.block_overrides:
			return self.block_overrides[block]

	def commandBuild(self, parts, fromloc, overrriderank):
		"/build water|watervator|lava|stilllava|grass|doublestep - Guest\nAliases: b\nLets you build special blocks."
		if self.client.isOp():
			possibles = {
				"air": (BLOCK_AIR, BLOCK_GLASS, "Glass"),
				"water": (BLOCK_WATER, BLOCK_INDIGO_CLOTH, "Dark Blue cloth"),
				"watervator": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
				"stillwater": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
				"lava": (BLOCK_LAVA, BLOCK_ORANGE_CLOTH, "Orange cloth"),
				"stilllava": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
				"lavavator": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
				"grass": (BLOCK_GRASS, BLOCK_GREEN_CLOTH, "Green cloth"),
				"doublestep": (BLOCK_DOUBLE_STAIR, BLOCK_WOOD, "Wood")
			}
		else:
			possibles = {
				"air": (BLOCK_AIR, BLOCK_GLASS, "Glass"),
				"water": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
				"watervator": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
				"stillwater": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
				"lava": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
				"stilllava": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
				"lavavator": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
				"grass": (BLOCK_GRASS, BLOCK_GREEN_CLOTH, "Green cloth"),
				"doublestep": (BLOCK_DOUBLE_STAIR, BLOCK_WOOD, "Wood")
			}
		if len(parts) == 1:
			self.client.sendServerMessage("Specify a type to toggle.")
		else:
			name = parts[1].lower()
			try:
				new, old, old_name = possibles[name]
			except KeyError:
				self.client.sendServerMessage("'%s' is not a special block type." % name)
			else:
				if old in self.block_overrides:
					del self.block_overrides[old]
					self.client.sendServerMessage("%s is back to normal." % old_name)
				else:
					self.block_overrides[old] = new
					self.client.sendServerMessage("%s will turn into %s." % (old_name, name))