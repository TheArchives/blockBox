# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class MutePlugin(ProtocolPlugin):
	
	commands = {
		"mute": "commandMute",
		"unmute": "commandUnmute",
		"muted": "commandMuted",
		"silence": "commandSilence",
		"desilence": "commandDesilence",
		"unsilence": "commandDesilence",
	}
	
	hooks = {
		"recvmessage": "messageReceived",
	}
	
	def gotClient(self):
		self.muted = set()
	
	def messageReceived(self, colour, username, text, action):
		"Stop viewing a message if we've muted them."
		if username.lower() in self.muted:
			return False
	
	@player_list
	@only_username_command
	def commandMute(self, username, byuser, overriderank):
		"/mute username - Guest\nStops you hearing messages from 'username'."
		self.muted.add(username)
		self.client.sendServerMessage("%s muted." % username)
	
	@player_list
	@only_username_command
	def commandUnmute(self, username, byuser, overriderank):
		"/unmute username - Guest\nLets you hear messages from this player again"
		if username in self.muted:
			self.muted.remove(username)
			self.client.sendServerMessage("%s unmuted." % username)
		else:
			self.client.sendServerMessage("%s wasn't muted to start with" % username)
	
	@player_list
	def commandMuted(self, username, byuser, overriderank):
		"/muted - Guest\nLists people you have muted."
		if self.muted:
			self.client.sendServerList(["Muted:"] + list(self.muted))
		else:
			self.client.sendServerMessage("You haven't muted anyone.")
	
	@player_list
	@mod_only
	@only_username_command
	def commandSilence(self, username, byuser, overriderank):
		"/silence username - Mod\nDisallows the Player to talk."
		if self.client.factory.usernames[username].isMod():
			self.client.sendServerMessage("You cannot silence staff!")
			return
		self.client.factory.silenced.add(username)
		self.client.sendServerMessage("%s is now Silenced." % username)

	@player_list
	@mod_only
	@only_username_command
	def commandDesilence(self, username, byuser, overriderank):
		"/desilence username - Mod\nAliases: unsilence\nAllows the Player to talk."
		if self.client.factory.isSilenced(username):
			self.client.factory.silenced.remove(username)
			self.client.sendServerMessage("%s is no longer Silenced." % username.lower())
		else:
			self.client.sendServerMessage("They aren't silenced.")
