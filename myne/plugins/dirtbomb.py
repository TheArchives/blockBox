#	iCraft is Copyright 2010 both
#
#	The Archives team:
#				   <Adam Guy> adam@adam-guy.com AKA "Adam01"
#				   <Andrew Godwin> andrew@aeracode.org AKA "Aera"
#				   <Dylan Lukes> lukes.dylan@gmail.com AKA "revenant"
#				   <Gareth Coles> colesgareth2@hotmail.com AKA "gdude2002"
#
#	And,
#
#	The iCraft team:
#				   <Andrew Caluzzi> tehcid@gmail.com AKA "tehcid"
#				   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#				   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#				   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#				   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#				   <James Kirslis> james@helplarge.com AKA "iKJames"
#				   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#				   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
#				   <Nathan Coulombe> NathanCoulombe@hotmail.com AKA "Saanix"
#				   <Nick Tolrud> ntolrud@yahoo.com AKA "ntfwc"
#				   <Noel Benzinger> ronnygmod@gmail.com AKA "Dwarfy"
#				   <Randy Lyne> qcksilverdragon@gmail.com AKA "goober"
#				   <Willem van der Ploeg> willempieeploeg@live.nl AKA "willempiee"
#
#	iCraft is licensed under the Creative Commons
#	Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
#	To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#	Or, send a letter to Creative Commons, 171 2nd Street,
#	Suite 300, San Francisco, California, 94105, USA.

from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *
from twisted.internet import reactor

class tntPlugin(ProtocolPlugin):
	
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
