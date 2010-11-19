# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *

class KickBanPlugin(ProtocolPlugin):

	commands = {
		"ban": "commandBan",
		"banb": "commandBanBoth",
		"ipban": "commandIpban",
		"ipreason": "commandIpreason",
		"kick": "commandKick",
		"banreason": "commandReason",
		"unban": "commandUnban",
		"unipban": "commandUnipban",
		"banned": "commandBanned",
		"freeze": "commandFreeze",
		"stop": "commandFreeze",
		"unfreeze": "commandUnFreeze",
		"defreeze": "commandUnFreeze",
		"unstop": "commandUnFreeze",
		#"ipshun": "commandIpshun",
		#"unipshun": "commandUnipshun",
		#"ipspec": "commandIpshun",
		#"unipspec": "commandUnipshun",
	}

	@player_list
	@admin_only
	def commandBanned(self, user, fromloc, overriderank):
		"/banned - Admin\nShows who is Banned."
		done = ""
		for element in self.client.factory.banned.keys():
			done = done + " " + element
		if len(done):
			self.client.sendServerList(["Banned:"] + done.split(' '))
		else:
			self.client.sendServerList(["Banned: No one."])

	@player_list
	@mod_only
	@username_command
	def commandKick(self, user, fromloc, overriderank, params=[]):
		"/kick username [reason] - Mod\nKicks the Player off the server."
		if params:
			user.sendError("Kicked: %s" % " ".join(params))
			self.client.sendServerMessage("They were just kicked.")
		else:
			user.sendError("You got Kicked.")
			self.client.sendServerMessage("They were just kicked.")

	@player_list
	@admin_only
	@only_username_command
	def commandBanBoth(self, username, fromloc, overriderank, params=[]):
		"/banb username reason - Admin\nName and IP ban a Player from this server."
		if not params:
			self.client.sendServerMessage("Please give a reason.")
		else:
			if username in self.client.factory.usernames:
				self.commandIpban(["/banb",username] + params, fromloc, overriderank)
			self.commandBan(["/banb",username] + params, fromloc, overriderank)

	@player_list
	@admin_only
	@only_username_command
	def commandBan(self, username, fromloc, overriderank, params=[]):
		"/ban username reason - Admin\nBans the Player from this server."
		if self.client.factory.isBanned(username):
			self.client.sendServerMessage("%s is already Banned." % username)
		else:
			if not params:
				self.client.sendServerMessage("Please give a reason.")
			else:
				self.client.factory.addBan(username, " ".join(params))
				if username in self.client.factory.usernames:
					self.client.factory.usernames[username].sendError("You got Banned!")
				self.client.sendServerMessage("%s has been Banned." % username)

	@player_list
	@director_only
	@only_username_command
	def commandIpban(self, username, fromloc, overriderank, params=[]):
		"/ipban username reason - Director\nBan a Player's IP from this server."
		ip = self.client.factory.usernames[username].transport.getPeer().host
		if self.client.factory.isIpBanned(ip):
			self.client.sendServerMessage("%s is already IPBanned." % ip)
		else:
			if not params:
				self.client.sendServerMessage("Please give a reason.")
			else:
				self.client.factory.addIpBan(ip, " ".join(params))
				if username in self.client.factory.usernames:
					self.client.factory.usernames[username].sendError("You got Banned!")
				self.client.sendServerMessage("%s has been IPBanned." % ip)

	@player_list
	@admin_only
	@only_username_command
	def commandUnban(self, username, fromloc, overriderank):
		"/unban username - Admin\nRemoves the Ban on the Player."
		if not self.client.factory.isBanned(username):
			self.client.sendServerMessage("%s is not Banned." % username)
		else:
			self.client.factory.removeBan(username)
			self.client.sendServerMessage("%s was UnBanned." % username)

	@player_list
	@director_only
	@only_string_command("IP")
	def commandUnipban(self, ip, fromloc, overriderank):
		"/unipban ip - Director\nRemoves the Ban on the IP."
		if not self.client.factory.isIpBanned(ip):
			self.client.sendServerMessage("%s is not Banned." % ip)
		else:
			self.client.factory.removeIpBan(ip)
			self.client.sendServerMessage("%s UnBanned." % ip)

	@player_list
	@admin_only	
	@only_username_command
	def commandReason(self, username, fromloc, overriderank):
		"/banreason username - Admin\nGives the reason a Player was Banned."
		if not self.client.factory.isBanned(username):
			self.client.sendServerMessage("%s is not Banned." % username)
		else:
			self.client.sendServerMessage("Reason: %s" % self.client.factory.banReason(username))

	@player_list
	@director_only
	@only_string_command("IP")
	def commandIpreason(self, ip, fromloc, overriderank):
		"/ipreason username - Director\nGives the reason an IP was Banned."
		if not self.client.factory.isIpBanned(ip):
			self.client.sendServerMessage("%s is not Banned." % ip)
		else:
			self.client.sendServerMessage("Reason: %s" % self.client.factory.ipBanReason(ip))

	@player_list
	@mod_only
	def commandUnFreeze(self, parts, fromloc, overriderank):
		"/unfreeze playername - Mod\nAliases: defreeze, unstop\nUnfreezes the player, allowing them to move again."
		try:
			username = parts[1]
		except:
			self.client.sendServerMessage("No player name given.")
			return
		try:
			user = self.client.factory.usernames[username]
		except:
			self.client.sendServerMessage("Player is not online.")
			return
		user.frozen = False
		user.sendNormalMessage("&4You have been unfrozen by %s!" % self.client.username)

	@player_list
	@mod_only
	def commandFreeze(self, parts, fromloc, overriderank):
		"/freeze playername - Mod\nAliases: stop\nFreezes the player, preventing them from moving."
		try:
			username = parts[1]
		except:
			self.client.sendServerMessage("No player name given.")
			return
		try:
			user = self.client.factory.usernames[username]
		except:
			self.client.sendServerMessage("Player is not online.")
			return
		user.frozen = True
		user.sendNormalMessage("&4You have been frozen by %s!" % self.client.username)

	#@player_list
	#@mod_only
	#@only_username_command
	#def commandIpshun(self, username, fromloc, overriderank):
	#	"/ipspec playername - Mod\nAliases: ipshun\nIPSpec a Player's IP in this server."
	#	ip = self.client.factory.usernames[username].transport.getPeer().host
	#	if self.client.factory.isIpShunned(ip):
	#		self.client.sendServerMessage("%s is already IPSpecced." % ip)
	#	else:
	#		self.client.factory.addIpShun(ip)
	#		if username in self.client.factory.usernames:
	#			self.client.factory.usernames[username].sendServerMessage("You got IPSpecced!")
	#		self.client.sendServerMessage("%s has been IPSpecced." % ip)
	#		logging.log(logging.INFO,self.client.username + ' IPSpecced ' + username + ip)

	#@player_list
	#@mod_only
	#@only_string_command("IP")
	#def commandUnipshun(self, ip, fromloc, overriderank):
	#	"/unipspec ip - Mod\nAliases: unipshun\nRemoves the IPSpec on the IP."
	#	if not self.client.factory.isIpShunned(ip):
	#		self.client.sendServerMessage("%s is not IPSpecced." % ip)
	#	else:
	#		self.client.factory.removeIpShun(ip)
	#		self.client.sendServerMessage("%s UnIPSpecced." % ip)
	#		logging.log(logging.INFO,self.client.username + ' UnIPSpecced ' + ip)
