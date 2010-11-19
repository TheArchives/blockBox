# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *

class FetchPlugin(ProtocolPlugin):

	commands = {
		"fetch": "commandFetch",
		"bring": "commandFetch",
		"invite": "commandInvite",
	}

	hooks = {
		"chatmsg": "message"
	}

	def gotClient(self):
		self.client.var_fetchrequest = False
		self.client.var_fetchdata = ()

	def message(self, message):
		if self.client.var_fetchrequest:
			self.client.var_fetchrequest = False
			if message in ["y"]:
				sender,world,rx,ry,rz = self.client.var_fetchdata
				if self.client.world == world:
					self.client.teleportTo(rx, ry, rz)
				else:
					self.client.changeToWorld(world.id, position=(rx, ry, rz))
				sender.sendServerMessage("%s has accepted your fetch request." % self.client.username)
			else:
				sender = self.client.var_fetchdata[0]
				sender.sendServerMessage("%s did not accept your request." % self.client.username)
			self.client.var_fetchdata
			return True

	@player_list
	@op_only
	@username_command
	def commandFetch(self, user, fromloc, overriderank):
		"/fetch username - Op\nAliases: bring\nTeleports a player to be where you are"
		# Shift the locations right to make them into block coords
		rx = self.client.x >> 5
		ry = self.client.y >> 5
		rz = self.client.z >> 5
		if user.world == self.client.world:
			user.teleportTo(rx, ry, rz)
		else:
			if self.client.isAdmin():
				user.changeToWorld(self.client.world.id, position=(rx, ry, rz))
			elif self.client.isMod():
				user.changeToWorld(self.client.world.id, position=(rx, ry, rz))
			else:
				self.client.sendServerMessage("%s cannot be fetched from '%s'" % (self.client.username, user.world.id))
				return
		user.sendServerMessage("You have been fetched by %s" % self.client.username)

	@player_list
	@username_command
	def commandInvite(self, user, fromloc, overriderank):
		rx = self.client.x >> 5
		ry = self.client.y >> 5
		rz = self.client.z >> 5
		user.sendServerMessage("%s would like to fetch you." % self.client.username)
		user.sendServerMessage("Do you wish to accept? [y]es/[n]o")
		user.var_fetchrequest = True
		user.var_fetchdata = (self.client,self.client.world,rx,ry,rz)
		self.client.sendServerMessage("The fetch request has been sent.")
