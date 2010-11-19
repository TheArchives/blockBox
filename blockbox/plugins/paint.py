# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class PaintPlugin(ProtocolPlugin):

	commands = {
		"paint": "commandPaint",
	}

	hooks = {
		"preblockchange": "blockChanged",
	}

	def gotClient(self):
		self.painting = False

	def blockChanged(self, x, y, z, block, selected_block, fromloc):
		"Hook trigger for block changes."
		if block is BLOCK_AIR and self.painting:
			return selected_block

	@build_list
	def commandPaint(self, parts, fromloc, overriderank):
		"/paint - Guest\nLets you break-and-build in one move. Toggle."
		if self.painting:
			self.painting = False
			self.client.sendServerMessage("Painting mode is now off.")
		else:
			self.painting = True
			self.client.sendServerMessage("Painting mode is now on.")
