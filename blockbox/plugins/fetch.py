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
#				   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#				   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#				   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#				   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#				   <James Kirslis> james@helplarge.com AKA "iKJames"
#				   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#				   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
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
	def commandFetch(self, user, byuser, overriderank):
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
	def commandInvite(self, user, byuser, overriderank):
		rx = self.client.x >> 5
		ry = self.client.y >> 5
		rz = self.client.z >> 5
		user.sendServerMessage("%s would like to fetch you." % self.client.username)
		user.sendServerMessage("Do you wish to accept? [y]es/[n]o")
		user.var_fetchrequest = True
		user.var_fetchdata = (self.client,self.client.world,rx,ry,rz)
		self.client.sendServerMessage("The fetch request has been sent.")
