# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from blockbox.globals import *
class ModsPlugin(ProtocolPlugin):
	
	commands = {
		"staff": "commandStaff",
		"advbuilders": "commandAdvBuilders",
		"directors": "commandDirectors",
		"admins": "commandAdmins",
		"mods": "commandMods",
	}

	@info_list
	def commandStaff(self, parts, byuser, overriderank):
		"/staff - Guest\nLists all server staff."
		self.client.sendServerMessage("The Server Staff - Owner: "+self.client.factory.owner)
		list = Staff(self)
		for each in list:
			self.client.sendServerList(each)

	@info_list
	def commandAdvBuilders(self, parts, byuser, overriderank):
		"/advbuilders - Guest\nLists all Advanced Builders."
		if len(self.client.factory.advbuilders):
			self.client.sendServerList(["Advanced Builders:"] + list(self.client.factory.members))

	@info_list
	def commandDirectors(self, parts, byuser, overriderank):
		"/direcors - Guest\nLists all Directors."
		if len(self.client.factory.directors):
			self.client.sendServerList(["Directors:"] + list(self.client.factory.directors))

	@info_list
	def commandAdmins(self, parts, byuser, overriderank):
		"/admins - Guest\nLists all Admins."
		if len(self.client.factory.admins):
			self.client.sendServerList(["Admins:"] + list(self.client.factory.admins))

	@info_list
	def commandMods(self, parts, byuser, overriderank):
		"/mods - Guest\nLists all Mods."
		if len(self.client.factory.mods):
			self.client.sendServerList(["Mods:"] + list(self.client.factory.mods))
