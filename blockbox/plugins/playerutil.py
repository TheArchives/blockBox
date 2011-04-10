# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from __future__ import with_statement

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.globals import *
from blockbox.persistence import PersistenceEngine as Persist
from blockbox.plugins import ProtocolPlugin

class PlayerUtilPlugin(ProtocolPlugin):
	"Commands for player handling, etc."

	commands = {
		"staff": "commandStaff",
		"advbuilders": "commandAdvBuilders",
		"directors": "commandDirectors",
		"admins": "commandAdmins",
		"mods": "commandMods",
		"banned": "commandBanned",
		"worldbanned": "commandWorldBanned",
		"ops": "commandOps",
		"builders": "commandBuilders",
		"specced": "commandSpecced",

		"respawn": "commandRespawn",

		"fetch": "commandFetch",
		"bring": "commandFetch",
		"invite": "commandInvite",

		"title": "commandSetTitle",
		"settitle": "commandSetTitle",

		"coord": "commandCoord",
		"tp": "commandTeleport",
		"teleport": "commandTeleport",

		"where": "commandWhere",
		"locate": "commandLocate",
		"find": "commandLocate",

		"quitmsg": "commandQuitMsg",

		"quit": "commandQuit",

		"who": "commandWho",
		"whois": "commandWho",
		"players": "commandWho",
		"pinfo": "commandWho",
		"lastseen": "commandLastseen",

		"b": "commandLastCommand",
		"lastcmd": "commandLastCommand",
		"lastcommand": "commandLastCommand",

		"rank": "commandRank",
		"setrank": "commandRank",
		"derank": "commandDeRank",
		"colors": "commandColors",
		"showops": "commandColors",

		"builder": "commandOldRanks",
		"advbuilder": "commandOldRanks",
		"op": "commandOldRanks",
		"mod": "commandOldRanks",
		"admin": "commandOldRanks",
		"director": "commandOldRanks",
		"debuilder": "commandOldDeRanks",
		"deadvbuilder": "commandOldDeRanks",
		"deop": "commandOldDeRanks",
		"demod": "commandOldDeRanks",
		"deadmin": "commandOldDeRanks",
		"dedirector": "commandOldDeRanks",

		"mute": "commandMute",
		"unmute": "commandUnmute",
		"muted": "commandMuted",

		"fly": "commandFly",
	}

	hooks = {
		"chatmsg": "chatmsg",
		"recvmessage": "messageReceived",
		"poschange": "posChanged",
		"newworld": "newWorld",
	}

	def gotClient(self):
		self.client.var_fetchrequest = False
		self.client.var_fetchdata = ()
		self.lastcommand = None
		self.savedcommands = list({})
		self.muted = set()
		self.flying = False
		self.last_flying_block = None

	def chatmsg(self, message):
		if message.startswith("/") and not message.split()[0].lower() == "/b":
			self.lastcommand = message
		elif self.client.var_fetchrequest:
			self.client.var_fetchrequest = False
			if message in ["y", "yes"]:
				sender, world, rx, ry, rz = self.client.var_fetchdata
				if self.client.world == world:
					self.client.teleportTo(rx, ry, rz)
				else:
					self.client.changeToWorld(world.id, position=(rx, ry, rz))
				self.client.sendServerMessage("You have accepted the fetch request.")
				sender.sendServerMessage("%s has accepted your fetch request." % self.client.username)
			elif message in ["n", "no"]:
				sender = self.client.var_fetchdata[0]
				self.client.sendServerMessage("You did not accept the fetch request.")
				sender.sendServerMessage("%s did not accept your request." % self.client.username)
			else:
				sender = self.client.var_fetchdata[0]
				self.client.sendServerMessage("You have ignored the fetch request.")
				sender.sendServerMessage("%s has ignored your request." % self.client.username)
				return
			return True

	def messageReceived(self, colour, username, text, fromloc):
		"Stop viewing a message if we've muted them."
		if username.lower() in self.muted:
			return False

	def posChanged(self, x, y, z, h, p):
		"Hook trigger for when the player moves"
		# Are we fake-flying them?
		if self.flying:
			fly_block_loc = ((x>>5),((y-48)>>5)-1,(z>>5))
			if not self.last_flying_block:
				# OK, send the first flying blocks
				self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
				self.setCsBlock(fly_block_loc[0], fly_block_loc[1] - 1, fly_block_loc[2], BLOCK_GLASS)
				self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
				self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
				self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
				self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
				self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
				self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
				self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
				self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
			else:
				# Have we moved at all?
				if fly_block_loc != self.last_flying_block:
					self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1] - 1, self.last_flying_block[2], BLOCK_AIR)
					self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
					self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
					self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
					self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
					self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
					self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
					self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
					self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
					self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
					self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
					self.setCsBlock(fly_block_loc[0], fly_block_loc[1] - 1, fly_block_loc[2], BLOCK_GLASS)
					self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
					self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
					self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
					self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
					self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
					self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
					self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
					self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
			self.last_flying_block = fly_block_loc
		else:
			if self.last_flying_block:
				self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
				self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1] - 1, self.last_flying_block[2], BLOCK_AIR)
				self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
				self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
				self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
				self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
				self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
				self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
				self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
				self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
				self.last_flying_block = None

	def newWorld(self, world):
		"Hook to reset flying abilities in new worlds if not op."
		if self.client.isSpectator():
			self.flying = False

	def setCsBlock(self, x, y, z, type):
		if y > -1 and x > -1 and z > -1:
			if y < self.client.world.y and x < self.client.world.x and z < self.client.world.z:
				if ord(self.client.world.blockstore.raw_blocks[self.client.world.blockstore.get_offset(x, y, z)]) is 0:
					self.client.sendPacked(TYPE_BLOCKSET, x, y, z, type)

	@config("category", "info")
	def commandStaff(self, parts, fromloc, overriderank):
		"/staff - Guest\nLists all server staff."
		self.client.sendServerMessage("The Server Staff - Owner: "+self.client.factory.owner)
		list = Staff(self)
		for each in list:
			self.client.sendServerList(each)

	@config("category", "info")
	def commandAdvBuilders(self, parts, fromloc, overriderank):
		"/advbuilders - Guest\nLists all Advanced Builders."
		if len(self.client.factory.advbuilders):
			self.client.sendServerList(["Advanced Builders:"] + list(self.client.factory.advbuilders))
		else:
			self.client.sendServerMessage("Advanced Builders: No one.")

	@config("category", "info")
	def commandDirectors(self, parts, fromloc, overriderank):
		"/directors - Guest\nLists all Directors."
		if len(self.client.factory.directors):
			self.client.sendServerList(["Directors:"] + list(self.client.factory.directors))
		else:
			self.client.sendServerMessage("Directors: No one.")

	@config("category", "info")
	def commandAdmins(self, parts, fromloc, overriderank):
		"/admins - Guest\nLists all Admins."
		if len(self.client.factory.admins):
			self.client.sendServerList(["Admins:"] + list(self.client.factory.admins))
		else:
			self.client.sendServerMessage("Admins: No one.")

	@config("category", "info")
	def commandMods(self, parts, fromloc, overriderank):
		"/mods - Guest\nLists all Mods."
		if len(self.client.factory.mods):
			self.client.sendServerList(["Mods:"] + list(self.client.factory.mods))
		else:
			self.client.sendServerMessage("Mods: No one.")

	@config("category", "player")
	@config("rank", "admin")
	def commandBanned(self, user, fromloc, overriderank):
		"/banned - Admin\nShows who is Banned."
		done = ""
		for element in self.client.factory.banned.keys():
			done = done + " " + element
		if len(done):
			self.client.sendServerList(["Banned:"] + done.split(' '))
		else:
			self.client.sendServerList(["Banned: No one."])

	@config("category", "player")
	@config("rank", "op")
	def commandWorldBanned(self, user, fromloc, overriderank):
		"/worldbanned - Op\nShows who is WorldBanned."
		done = ""
		for element in self.client.world.worldbans.keys():
			done = done + " " + element
		if len(done):
			self.client.sendServerList(["WorldBanned:"] + done.split(' '))
		else:
			self.client.sendServerList(["WorldBanned: No one."])

	@config("category", "player")
	@username_command
	def commandRespawn(self, username, fromloc, overriderank):
		"/respawn [username] - Guest\n Respawns player, specify username if you would like to respawn another player (Mod+ only)"
		if len(username) == 1 and self.client.isMod():
			if username in self.client.factory.usernames:
				self.client.factory.usernames[username].respawn()
			else:
				self.client.sendServerMessage("%s is not on the server." % username)
				return
			self.client.factory.usernames[username].sendServerMessage("You have been respawned by %s." % self.client.username)
			self.client.world.logger.debug("%s respawned." % username)
		else:
			self.client.respawn()

	@config("category", "player")
	@config("rank", "op")
	@username_command
	def commandFetch(self, user, fromloc, overriderank):
		"/fetch username - Op\nAliases: bring\nTeleports a player to be where you are."
		# Shift the locations right to make them into block coords
		rx = self.client.x >> 5
		ry = self.client.y >> 5
		rz = self.client.z >> 5
		if user.world == self.client.world:
			user.teleportTo(rx, ry, rz)
		else:
			if self.client.isMod():
				user.changeToWorld(self.client.world.id, position=(rx, ry, rz))
			else:
				self.client.sendServerMessage("%s cannot be fetched from '%s'" % (self.client.username, user.world.id))
				return
		user.sendServerMessage("You have been fetched by %s." % self.client.username)

	@config("category", "player")
	@username_command
	def commandInvite(self, user, fromloc, overriderank):
		"/invite username - Guest\nInvites a player to teleport to you."
		rx = self.client.x >> 5
		ry = self.client.y >> 5
		rz = self.client.z >> 5
		user.sendServerMessage("%s would like you to teleport to him." % self.client.username)
		user.sendServerMessage("Do you wish to accept? [y]es/[n]o")
		user.var_fetchrequest = True
		user.var_fetchdata = (self.client,self.client.world, rx, ry, rz)
		self.client.sendServerMessage("The fetch request has been sent.")

	@config("category", "player")
	@config("rank", "director")
	def commandSetTitle(self, parts, fromloc, overriderank):
		"/title username [title] - Director\nAliases: settitle\nGives or removes a title to username."
		with Persist(parts[1]) as p:
			if len(parts) == 3:
				if len(parts[2]) < 6:
					p.set("misc", "title", parts[2])
					self.client.sendServerMessage("Added title.")
				else:
					self.client.sendServerMessage("A title must be 5 character or less")
			elif len(parts) == 2:
				if p.string("misc", "title") is None:
					self.client.sendServerMessage("Syntax: /title username title")
					return False
				else:
					p.set("misc", "title", "")
					self.client.sendServerMessage("Removed title.")
			elif len(parts)>3:
				self.client.sendServerMessage("You may only set one word as a title.")

	@config("category", "info")
	def commandOps(self, parts, fromloc, overriderank):
		"/ops - Guest\nLists this world's ops."
		if not self.client.world.ops:
			self.client.sendServerMessage("This world has no Ops.")
		else:
			self.client.sendServerList(["Ops for %s:" % self.client.world.id] + list(self.client.world.ops))

	@config("category", "info")
	def commandBuilders(self, parts, fromloc, overriderank):
		"/builders - Guest\nLists this world's builders."
		if not self.client.world.builders:
			self.client.sendServerMessage("This world has no builders.")
		else:
			self.client.sendServerList(["Builders for %s:" % self.client.world.id] + list(self.client.world.writers))

	@config("category", "info")
	def commandWhere(self, parts, fromloc, overriderank):
		"/where - Guest\nReturns your current coordinates"
		x = self.client.x >> 5
		y = self.client.y >> 5
		z = self.client.z >> 5
		h = self.client.h
		p = self.client.p
		self.client.sendServerMessage("You are at %s, %s, %s [h%s, p%s]" % (x, y, z, h, p))

	@config("category", "player")
	def commandWho(self, parts, fromloc, overriderank):
		"/who [username] - Guest\nAliases: pinfo, players, whois\nOnline players, or player lookup."
		if len(parts) < 2:
			self.client.sendServerMessage("Do '/who username' for more info.")
			userlist = set()
			for user in self.client.factory.usernames:
				if user is None:
					pass # To avoid NoneType error
				else:
					if user in self.client.factory.spectators:
						user = COLOUR_BLACK + user
					elif user in self.client.factory.owner:
						user = COLOUR_DARKGREEN + user
					elif user in self.client.factory.directors:
						user = COLOUR_GREEN + user
					elif user in self.client.factory.admins:
						user = COLOUR_RED + user
					elif user in self.client.factory.mods:
						user = COLOUR_BLUE + user
					elif user in self.client.world.owner:
						user = COLOUR_DARKPURPLE + user
					elif user in self.client.world.ops:
						user = COLOUR_DARKCYAN + user
					elif user in self.client.factory.advbuilders:
						user = COLOUR_GREY + user
					elif user in self.client.world.builders:
						user = COLOUR_CYAN + user
					else:
						user = COLOUR_WHITE + user
				userlist.add(user)
			self.client.sendServerList(["Players:"] + list(userlist))
		else:
			user = parts[1].lower()
			with Persist(user) as p:
				if parts[1].lower() in self.client.factory.usernames:
					# Parts is an array, always, so we get the first item.
					username = self.client.factory.usernames[user]
					if username.isOwner():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKGREEN+"Owner")
					elif username.isDirector():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREEN+"Director")
					elif username.isAdmin():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_RED+"Admin")
					elif username.isMod():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLUE+"Mod")
					elif username.isWorldOwner():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKPURPLE+"World Owner")
					elif username.isOp():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKCYAN+"Operator")
					elif username.isAdvBuilder():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREY+"Advanced Builder")
					elif username.isBuilder():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_CYAN+"Builder")
					elif username.isSpectator():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLACK+"Spec")
					else:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_WHITE+"Player")
					if self.client.isAdmin():
						self.client.sendServerMessage("IP: "+str(username.transport.getPeer().host))
					if username.gone == 1:
						self.client.sendServerMessage("Status: "+COLOUR_DARKPURPLE+"Away")
					elif username.gone == 0:
						self.client.sendServerMessage("Status: "+COLOUR_DARKGREEN+"Online")
					else:
						self.client.sendServerMessage("Status: "+COLOUR_DARKGREEN+"Online")
					self.client.sendServerMessage("World: %s" % (username.world.id))
					if p.int("bank", "balance", -1) is not -1:
						self.client.sendServerMessage("Balance: C%d." %(p.int("bank", "balance", 0)))
					else:
						self.client.sendServerMessage("Balance: N/A")
				else:
					# Parts is an array, always, so we get the first item.
					username = parts[1].lower()
					if username in self.client.factory.spectators:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLACK+"Spec")
					elif username in self.client.factory.owner:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKGREEN+"Owner")
					elif username in self.client.factory.directors:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREEN+"Director")
					elif username in self.client.factory.admins:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_RED+"Admin")
					elif username in self.client.factory.mods:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLUE+"Mod")
					elif username in self.client.world.owner:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKPURPLE+"World Owner")
					elif username in self.client.world.ops:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKCYAN+"Operator")
					elif username in self.client.factory.advbuilders:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREY+"Advanced Builder")
					elif username in self.client.world.builders:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_CYAN+"Builder")
					else:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_WHITE+"Guest")
					if self.client.isAdmin():
						self.client.sendServerMessage("IP: "+p.string("main", "ip", "None recorded."))
					self.client.sendServerMessage("Status: "+COLOUR_DARKRED+"Offline")
					if username not in self.client.factory.lastseen:
						self.client.sendServerMessage("Last Seen: N/A")
					else:
						t = time.time() - self.client.factory.lastseen[username]
						days = t // 86400
						hours = (t % 86400) // 3600
						mins = (t % 3600) // 60
						desc = "%id, %ih, %im" % (days, hours, mins)
						self.client.sendServerMessage("Last Seen: %s ago." % (desc))
						#self.commandLastseen(parts, fromloc, overriderank)
					if p.int("bank", "balance", -1) is not -1:
						self.client.sendServerMessage("Balance: C%d." %(p.int("bank", "balance", 0)))
					else:
						self.client.sendServerMessage("Balance: N/A")

	@config("category", "player")
	def commandQuitMsg(self, parts, fromloc, overriderank):
		"/quitmsg - Guest\nSets your quit message."
		self.client.persist.set("main", "quitmsg", " ".join(parts[1:]))
		self.client.quitmsg = " ".join(parts[1:])
		self.client.sendServerMessage("Your quit message is now: %s" % " ".join(parts[1:]))

	@config("category", "player")
	def commandQuit(self, parts, fromloc, overriderank):
		"/quit [message] - Guest\nExits the server."
		if not len(parts) > 1:
			self.client.sendError("Quit: %s" % self.client.quitmsg)
		else:
			self.client.quitmsg = " ".join(parts[1:])
			self.client.sendError("Quit: %s" % " ".join(parts[1:]))

	@only_username_command
	def commandLastseen(self, username, fromloc, overriderank):
		"/lastseen username - Guest\nTells you when 'username' was last seen."
		if self.persist.string("main", "lastseen", -1):
			self.client.sendServerMessage("There are no records of %s." % username)
		else:
			t = time.time() - self.persist.string("main", "lastseen", -1)
			days = t // 86400
			hours = (t % 86400) // 3600
			mins = (t % 3600) // 60
			desc = "%id, %ih, %im" % (days, hours, mins)
			self.client.sendServerMessage("%s was last seen %s ago." % (username, desc))

	@username_command
	def commandLocate(self, user, fromloc, overriderank):
		"/locate username - Guest\nAliases: find\nTells you what world a user is in."
		self.client.sendServerMessage("%s is in world %s." % (user.username, user.world.id))

	@config("category", "info")
	def commandLastCommand(self, parts, fromloc, rankoverride):
		"/b - Guest\nAliases: lastcmd, lastcommand\nRedos the last command you entered."
		message = self.lastcommand
		parts = [x.strip() for x in message.split() if x.strip()]
		command = parts[0].strip("/")
		# See if we can handle it internally
		try:
			func = getattr(self.client, "command%s" % command.title())
		except AttributeError:
			# Can we find it from a plugin?
			try:
				try:
					func = self.commands[command.lower()]
				except KeyError:
					self.client.sendServerMessage("Unknown command '%s'" % command)
					return
			except AttributeError:
				self.client.logger.error("Cannot find command code for %s, please report to blockBox team." % func)
				self.client.sendSplitServerMessage("Command code not found, please report to server staff or blockBox team.")
				return
		if func.config["disabled"]:
			self.sendServerMessage("Command %s has been disabled by the server owner." % command)
			return
		if self.client.isSpectator() and func.config["rank"]:
			self.client.sendServerMessage("'%s' is not available to spectators." % command)
			return
		if func.config["rank"] == "owner" and not self.isOwner():
			self.client.sendServerMessage("'%s' is an Owner-only command!" % command)
			return
		if func.config["rank"] == "director" and not self.isDirector():
			self.client.sendServerMessage("'%s' is a Director-only command!" % command)
			return
		if func.config["rank"] == "admin" and not self.isAdmin():
			self.client.sendServerMessage("'%s' is an Admin-only command!" % command)
			return
		if func.config["rank"] == "mod" and not self.isMod():
			self.client.sendServerMessage("'%s' is a Mod-only command!" % command)
			return
		if func.config["rank"] == "worldowner" and not self.isWorldOwner():
			self.client.sendServerMessage("'%s' is an WorldOwner-only command!" % command)
			return
		if func.config["rank"] == "op" and not self.isRank("op"):
			self.client.sendServerMessage("'%s' is an Op-only command!" % command)
			return
		if func.config["rank"] == "advbuilder" and not self.isRank("advbuilder"):
			self.client.sendServerMessage("'%s' is an Advanced Builder-only command!" % command)
			return
		if func.config["rank"] == "builder" and not self.isRank("builder"):
			self.client.sendServerMessage("'%s' is a Builder-only command!" % command)
			return
		# Using custom message?
		if func.config["custom_cmdlog_msg"]:
			self.logger.info("%s %s" % (self.username, func.config["custom_cmdlog_msg"]))
		else:
			self.logger.info("%s just used: %s" % (self.username, " ".join(parts)))
		try:
			func(parts, 'user', False) # fromloc is user, overriderank is false
		except Exception, e:
			self.client.sendServerMessage("Internal server error.")
			self.client.logger.error(traceback.format_exc())

	@config("category", "player")
	@config("rank", "mod")
	def commandSpecced(self, user, fromloc, overriderank):
		"/specced - Mod\nShows who is specced."
		if len(self.client.factory.spectators):
			self.client.sendServerList(["Specced:"] + list(self.client.factory.spectators))
		else:
			self.client.sendServerList(["Specced: No one."])

	@config("category", "player")
	@config("rank", "op")
	def commandRank(self, parts, fromloc, overriderank):
		"/rank username rankname - Op\nAliases: setrank\nMakes username the rank of rankname."
		if len(parts) < 3:
			self.client.sendServerMessage("You must specify a rank and username.")
		else:
			self.client.sendServerMessage(Rank(self, parts, fromloc, overriderank))

	@config("category", "player")
	@config("rank", "op")
	def commandDeRank(self, parts, fromloc, overriderank):
		"/derank rankname username - Op\nMakes playername lose the rank of rankname."
		if len(parts) < 3:
			self.client.sendServerMessage("You must specify a rank and username.")
		else:
			self.client.sendServerMessage(DeRank(self, parts, fromloc, overriderank))

	@config("category", "player")
	@config("rank", "op")
	def commandOldRanks(self, parts, fromloc, overriderank):
		"/rankname username [world] - Op\nAliases: spec, builder, op, mod, admin, director\nThis is here for Myne users."
		if len(parts) < 2:
			self.client.sendServerMessage("You must specify a rank and username.")
		else:
			parts = ["/rank", parts[0][1:]] + parts[1:]
			self.client.sendServerMessage(Rank(self, parts, fromloc, overriderank))

	@config("category", "player")
	@config("rank", "op")
	def commandOldDeRanks(self, parts, fromloc, overriderank):
		"/derankname username [world] - Op\nAliases: despec, unspec, debuilder, deop, demod, deadmin, dedirector\nThis is here for Myne users."
		if len(parts) < 2:
			self.client.sendServerMessage("You must specify a rank and username.")
		else:
			parts = ["/derank", parts[0][1:]] + parts[1:]
			self.client.sendServerMessage(DeRank(self, parts, fromloc, overriderank))

	@config("category", "player")
	@config("rank", "op")
	@on_off_command
	def commandColors(self, onoff, fromloc, overriderank):
		"/colors on|off - Op\nAliases: showops\nEnables or disables colors in this world."
		if onoff == "on":
			self.client.world.highlight_ops = True
			self.client.sendServerMessage("World %s now has staff highlighting." % self.client.world.id)
		else:
			self.client.world.highlight_ops = False
			self.client.sendServerMessage("World %s no longer has staff highlighting." % self.client.world.id)

	@config("category", "player")
	@only_username_command
	def commandMute(self, username, fromloc, overriderank):
		"/mute username - Guest\nStops you hearing messages from 'username'."
		self.muted.add(username)
		self.client.sendServerMessage("%s is now muted." % username)

	@config("category", "player")
	@only_username_command
	def commandUnmute(self, username, fromloc, overriderank):
		"/unmute username - Guest\nLets you hear messages from this player again"
		if username in self.muted:
			self.muted.remove(username)
			self.client.sendServerMessage("%s has been unmuted." % username)
		else:
			self.client.sendServerMessage("%s was not muted." % username)

	@config("category", "player")
	def commandMuted(self, username, fromloc, overriderank):
		"/muted - Guest\nLists people you have muted."
		if self.muted:
			self.client.sendServerList(["Muted:"] + list(self.muted))
		else:
			self.client.sendServerMessage("You haven't muted anyone.")

	@config("category", "player")
	@on_off_command
	def commandFly(self, onoff, fromloc, overriderank):
		"/fly on|off - Guest\nEnables or disables server-side flying."
		if onoff == "on":
			self.flying = True
			self.client.sendServerMessage("You are now flying.")
		else:
			self.flying = False
			self.client.sendServerMessage("You are no longer flying.")

	@config("category", "player")
	@username_command
	def commandTeleport(self, user, fromloc, overriderank):
		"/tp username - Guest\nAliases: teleport\nTeleports you to the players location."
		x = user.x >> 5
		y = user.y >> 5
		z = user.z >> 5
		if user.world == self.client.world:
			self.client.teleportTo(x, y, z)
		else:
			if self.client.canEnter(user.world):
				self.client.changeToWorld(user.world.id, position=(x, y, z))
			else:
				self.client.sendServerMessage("Sorry, that world is private.")

	@config("category", "world")
	def commandCoord(self, parts, fromloc, overriderank):
		"/coord x y z - Guest\nTeleports you to coords. NOTE: y is up."
		try:
			x = int(parts[1])
			y = int(parts[2])
			z = int(parts[3])
			self.client.teleportTo(x, y, z)
		except (IndexError, ValueError):
			self.client.sendServerMessage("Usage: /coord x y z")