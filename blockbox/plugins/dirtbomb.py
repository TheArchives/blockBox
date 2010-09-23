# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from lib.twisted.internet import reactor

class DirtBombPlugin(ProtocolPlugin):
	
	commands = {
		"dirtbomb": "commanddirtbomb",
	}
	
	hooks = {
		"blockchange": "blockChanged",
		"newworld": "newWorld",
	}
	
	def gotClient(self):
		self.build_tnt = False
		self.explosion_radius = 7
		self.delay = 2
	
	def newWorld(self, world):
		"Hook to reset bomb abilities in new worlds if not op."
		if not self.client.isOp():
			self.build_tnt = False
	
	def blockChanged(self, x, y, z, block, selected_block, byuser):
		"Hook trigger for block changes."
		tobuild = []
		# Randomise the variables
		fanout = self.explosion_radius
		if self.build_tnt and block == BLOCK_DIRT:
			def explode():
				# Clear the explosion radius
				for i in range(-fanout, fanout+1):
					for j in range(-fanout, fanout+1):
						for k in range(-fanout, fanout+1):
								tobuild.append((i, j, k, BLOCK_DIRT))
				# OK, send the build changes
				for dx, dy, dz, block in tobuild:
					try:
						self.client.world[x+dx, y+dy, z+dz] = chr(block)
						self.client.sendBlock(x+dx, y+dy, z+dz, block)
						self.client.factory.queue.put((self.client, TASK_BLOCKSET, (x+dx, y+dy, z+dz, block)))
					except AssertionError: # OOB
						pass
			# Explode in 2 seconds
			reactor.callLater(self.delay, explode)

	@build_list
	@op_only
	@on_off_command
	def commanddirtbomb(self, onoff, byuser, overriderank):
		"/dirtbomb on|off - Builder\nThis is some kind of bomb involving dirt."
		if onoff == "on":
			self.build_tnt = True
			self.client.sendServerMessage("You are now making dirtbombs in place of dirt.")
		else:
			self.build_tnt = False
			self.client.sendServerMessage("You are no longer building dirtbombs.")
