# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *

class BanishPlugin(ProtocolPlugin):
	commands = {
		"banish": "commandBanish",
		"worldkick": "commandBanish",
		"worldban": "commandWorldBan",
		"unworldban": "commandUnWorldban",
		"deworldban": "commandUnWorldban",
		"worldbanned": "commandWorldBanned",
	}

	@player_list
	@op_only
	def commandWorldBanned(self, user, fromloc, overriderank):
		"/worldbanned - Op\nShows who is worldbanned."
		done = ""
		for element in self.client.world.worldbans.keys():
			done = done + " " + element
		if len(done):
			self.client.sendServerList(["WorldBanned:"] + done.split(' '))
		else:
			self.client.sendServerList(["WorldBanned: No one."])
	@player_list
	@op_only
	@username_command
	def commandBanish(self, user, fromloc, overriderank):
		"/worldkick username - Op\nAliases: banish\nBanishes the Player to the default world."
		if user.world == self.client.world:
			user.sendServerMessage("You were WorldKicked from '%s'." % self.client.world.id)
			user.changeToWorld("main")
			self.client.sendServerMessage("Player %s got WorldKicked." % user.username)
		else:
			self.client.sendServerMessage("Your Player is in another world!")

	@player_list
	@op_only
	@only_username_command
	def commandWorldBan(self, username, fromloc, overriderank):
		"/worldban username - Op\nWorldBan a Player from this Map."
		if self.client.world.isWorldBanned(username):
			self.client.sendServerMessage("%s is already WorldBanned." % username)
		else:
			self.client.world.add_worldban(username)
			if username in self.client.factory.usernames:
				if self.client.factory.usernames[username].world == self.client.world:
					self.client.factory.usernames[username].changeToWorld("main")
					self.client.factory.usernames[username].sendServerMessage("You got WorldBanned!")
			self.client.sendServerMessage("%s has been WorldBanned." % username)

	@player_list
	@op_only
	@only_username_command
	def commandUnWorldban(self, username, fromloc, overriderank):
		"/unworldban username - Op\nAliases: deworldban\nRemoves the WorldBan on the Player."
		if not self.client.world.isWorldBanned(username):
			self.client.sendServerMessage("%s is not WorldBanned." % username)
		else:
			self.client.world.delete_worldban(username)
			self.client.sendServerMessage("%s was UnWorldBanned." % username)