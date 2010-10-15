# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from blockbox.globals import *
from blockbox.world import World

class RankPlugin(ProtocolPlugin):
	
	commands = {
		"rank": "commandRank",
		"setrank": "commandRank",
		"derank": "commandDeRank",
		"colors": "commandColors",
		"showops": "commandColors",
		"spec": "commandSpec",
		"unspec": "commandDeSpec",
		"specced": "commandSpecced",
		#"writer": "commandOldRanks",
		#"builder": "commandOldRanks",
		#"advbuilder": "commandOldRanks",
		#"op": "commandOldRanks",
		#"mod": "commandOldRanks",
		#"admin": "commandOldRanks",
		#"director": "commandOldRanks",
		#"dewriter": "commandOldDeRanks",
		#"debuilder": "commandOldDeRanks",
		#"deadvbuilder": "commandOldDeRanks",
		#"deop": "commandOldDeRanks",
		#"demod": "commandOldDeRanks",
		#"deadmin": "commandOldDeRanks",
		#"dedirector": "commandOldDeRanks",
	}

	@player_list
	@mod_only
	def commandSpecced(self, user, fromloc, overriderank):
		"/specced - Mod\nShows who is Specced."
		if len(self.client.factory.spectators):
			self.client.sendServerList(["Specced:"] + list(self.client.factory.spectators))
		else:
			self.client.sendServerList(["Specced: No one."])

	@player_list
	@op_only
	def commandRank(self, parts, fromloc, overriderank):
		"/rank rankname username - Op\nAliases: setrank\nMakes username the rank of rankname."
		if len(parts) < 3:
			self.client.sendServerMessage("You must specify a rank and username.")
		else:
			self.client.sendServerMessage(Rank(self, parts, fromloc, overriderank))

	@player_list
	@op_only
	def commandDeRank(self, parts, fromloc, overriderank):
		"/derank rankname username - Op\nMakes playername lose the rank of rankname."
		if len(parts) < 3:
			self.client.sendServerMessage("You must specify a rank and username.")
		else:
			self.client.sendServerMessage(DeRank(self, parts, fromloc, overriderank))

	@player_list
	@op_only
	def commandOldRanks(self, parts, fromloc, overriderank):
		"/rankname username [world] - Op\nAliases: writer, builder, op, mod, admin, director\nThis is here for Myne users."
		if len(parts) < 2:
			self.client.sendServerMessage("You must specify a rank and username.")
		else:
			if parts[0] == "/writer":
				parts[0] = "/builder"
			parts = ["/rank", parts[0][1:]] + parts[1:]
			self.client.sendServerMessage(Rank(self, parts, fromloc, overriderank))

	@player_list
	@op_only
	def commandOldDeRanks(self, parts, fromloc, overriderank):
		"/derankname username [world] - Op\nAliases: dewriter, debuilder, deop, demod, deadmin, dedirector\nThis is here for Myne users."
		if len(parts) < 2:
			self.client.sendServerMessage("You must specify a rank and username.")
		else:
			if parts[0] == "/dewriter":
				parts[0] = "/debuilder"
			parts = ["/derank", parts[0][1:]] + parts[1:]
			self.client.sendServerMessage(DeRank(self, parts, fromloc, overriderank))
				
	@player_list
	@op_only
	@on_off_command
	def commandColors(self, onoff, fromloc, overriderank):
		"/colors on|off - Op\nAliases: showops\nEnables or disables colors in this world."
		if onoff == "on":
			self.client.world.highlight_ops = True
			self.client.sendServerMessage("%s now has staff highlighting." % self.client.world.id)
		else:
			self.client.world.highlight_ops = False
			self.client.sendServerMessage("%s no longer has staff highlighting." % self.client.world.id)

	@player_list
	@mod_only
	@only_username_command
	def commandSpec(self, username, fromloc, overriderank):
		"/spec username - Mod\nMakes the player as a spec."
		self.client.sendServerMessage(Spec(self, username, fromloc, overriderank))
	
	@player_list
	@mod_only
	@only_username_command
	def commandDeSpec(self, username, fromloc, overriderank):
		"/unspec username - Mod\nRemoves the player as a spec."
		try:
			self.client.factory.spectators.remove(username)
		except:
			self.client.sendServerMessage("%s was never a spec." % username)
		self.client.sendServerMessage("%s is no longer a spec." % username)
		if username in self.client.factory.usernames:
			self.client.factory.usernames[username].sendSpectatorUpdate()
