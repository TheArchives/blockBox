# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class PhysicsControlPlugin(ProtocolPlugin):

	commands = {
		"physics": "commandPhysics",
		#"physflush": "commandPhysflush",
		"unflood": "commandUnflood",
		"deflood": "commandUnflood",
		"fwater": "commandFwater",
		"asd":"commandASD",
	}

	@world_list
	@op_only
	def commandUnflood(self, parts, fromloc, overriderank):
		"/unflood worldname - Op\nAliases: deflood\nSlowly removes all water and lava from the map."
		self.client.world.start_unflooding()
		self.client.sendWorldMessage("Unflooding has been initiated.")

	@world_list
	@admin_only
	@on_off_command
	def commandPhysics(self, onoff, fromloc, overriderank):
		"/physics on|off - Admin\nEnables or disables physics in this world."
		if onoff == "on":
			if self.client.world.physics:
				self.client.sendWorldMessage("Physics is already on here.")
			else:
				if self.client.factory.numberWithPhysics() >= self.client.factory.physics_limit:
					self.client.sendWorldMessage("There are already %s worlds with physics on (the max)." % self.client.factory.physics_limit)
				else:
					self.client.world.physics = True
					self.client.sendWorldMessage("This world now has physics enabled.")
		else:
			if not self.client.world.physics:
				self.client.sendWorldMessage("Physics is already off here.")
			else:
				self.client.world.physics = False
				self.client.sendWorldMessage("This world now has physics disabled.")

	@world_list
	@op_only
	@on_off_command
	def commandFwater(self, onoff, fromloc, overriderank):
		"/fwater on|off - Op\nEnables or disables finite water in this world."
		if onoff == "on":
			self.client.world.finite_water = True
			self.client.sendWorldMessage("This world now has finite water enabled.")
		else:
			self.client.world.finite_water = False
			self.client.sendWorldMessage("This world now has finite water disabled.")

	@world_list
	@admin_only
	@on_off_command
	def commandASD(self, onoff, fromloc, overriderank):
		"/asd on|off - Admin\nEnables or disables whether the world shuts down if no one is on it."
		if onoff == "on":
			self.client.world.autoshutdown = True
			self.client.sendWorldMessage("This world now automaticaly shuts down.")
		else:
			self.client.world.autoshutdown = False
			self.client.sendWorldMessage("This world now shuts down manualy.")

	# Needs updating for new physics engine separation
	#@admin_only
	#def commandPhysflush(self, parts, fromloc, overriderank):
	#	"/physflush - Tells the physics engine to rescan the world."
	#	self.client.world.physics_engine.was_physics = False
	#	self.sendServerMessage("Physics flush running.")
