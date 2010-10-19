# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.


from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class StatusPlugin(ProtocolPlugin):
	
	commands = {
		"status": "commandStatus",
		"mapinfo": "commandStatus",
		"setspawn": "commandSetspawn",
		"setowner": "commandSetOwner",
		"owner": "commandSetOwner",
		"worldowner": "commandSetOwner",
		"where": "commandWhere",
		"ops": "commandOps",
		"writers": "commandWriters",
		"builders": "commandWriters",
	}

	@player_list
	@mod_only
	def commandSetOwner(self, parts, fromloc, overriderank):
		"/setowner username - Mod\nAliases: owner, worldowner\nSets the world's owner string"
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify an World Owner.")
		else:
			self.client.world.owner = str(parts[1])
			#This was deleted in iCraft2.6.2 for some weird reasons
			#self.client.sendWorldOwnerUpdate()
			self.client.sendServerMessage("The World Owner has been set.")

	@info_list
	def commandOps(self, parts, fromloc, overriderank):
		"/ops - Guest\nLists this world's ops"
		if not self.client.world.ops:
			self.client.sendServerMessage("This world has no Ops.")
		else:
			self.client.sendServerList(["Ops for %s:" % self.client.world.id] + list(self.client.world.ops))

	@info_list
	def commandWriters(self, parts, fromloc, overriderank):
		"/writers - Guest\nAliases: builders\nLists this world's writers"
		if not self.client.world.writers:
			self.client.sendServerMessage("This world has no Builders.")
		else:
			self.client.sendServerList(["Builders for %s:" % self.client.world.id] + list(self.client.world.writers))
	
	@info_list
	def commandStatus(self, parts, fromloc, overriderank):
		"/status - Guest\nAliases: mapinfo\nReturns info about the current world"
		self.client.sendServerMessage("World: %s" % (self.client.world.id))
		self.client.sendServerMessage("Owner: %s" % self.client.world.owner)
		self.client.sendServerMessage("Size: %sx%sx%s" % (self.client.world.x, self.client.world.y, self.client.world.z))
		self.client.sendServerMessage("- " + \
			(self.client.world.all_write and "&4Unlocked" or "&2Locked") + "&e | " + \
			(self.client.world.zoned and "&2Zones" or "&4Zones") + "&e | " + \
			(self.client.world.private and "&2Private" or "&4Private") + "&e | " + \
			(self.client.world.global_chat and "&2GChat" or "&4GChat")
		)
		self.client.sendServerMessage("- " + \
			(self.client.world.highlight_ops and "&2Colors" or "&4Colors") + "&e | " + \
			(self.client.world.physics and "&2Physics" or "&4Physics") + "&e | " + \
			(self.client.world.finite_water and "&4FWater" or "&2FWater") + "&e | " + \
			(self.client.world.admin_blocks and "&2Solids" or "&4Solids")
		)
		if not self.client.world.ops:
			self.client.sendServerMessage("Ops: N/A")
		else:
			self.client.sendServerList(["Ops:"] + list(self.client.world.ops))
		if not self.client.world.writers:
			self.client.sendServerMessage("Builders: N/A")
		else:
			self.client.sendServerList(["Builders:"] + list(self.client.world.writers))
  
	@world_list
	@op_only
	def commandSetspawn(self, parts, fromloc, overriderank):
		"/setspawn - Op\nSets this world's spawn point to the current location."
		x = self.client.x >> 5
		y = self.client.y >> 5
		z = self.client.z >> 5
		h = int(self.client.h*(360/255.0))
		self.client.world.spawn = (x, y, z, h)
		self.client.sendServerMessage("Set spawn point to %s, %s, %s" % (x, y, z))
	
	@info_list
	def commandWhere(self, parts, fromloc, overriderank):
		"/where - Guest\nReturns your current coordinates"
		x = self.client.x >> 5
		y = self.client.y >> 5
		z = self.client.z >> 5
		h = self.client.h
		p = self.client.p
		self.client.sendServerMessage("You are at %s, %s, %s [h%s, p%s]" % (x, y, z, h, p))
