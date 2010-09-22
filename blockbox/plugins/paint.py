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
	
	def blockChanged(self, x, y, z, block, selected_block, byuser):
		"Hook trigger for block changes."
		if block is BLOCK_AIR and self.painting:
			return selected_block
	
	@build_list
	def commandPaint(self, parts, byuser, overriderank):
		"/paint - Guest\nLets you break-and-build in one move. Toggle."
		if self.painting:
			self.painting = False
			self.client.sendServerMessage("Painting mode is now off.")
		else:
			self.painting = True
			self.client.sendServerMessage("Painting mode is now on.")
