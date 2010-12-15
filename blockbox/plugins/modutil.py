# blockBox is Copyright 2009-2010 of the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.
from lib.twisted.internet import reactor

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from blockbox.persistence import PersistenceEngine as Persist

maxundos = 3000

class ModUtilPlugin(ProtocolPlugin):
	"Commands for moderations."

	commands = {
		"ban": "commandBan",
		"ban": "commandSay",
		"banb": "commandBanBoth",
		"ipban": "commandIpban",
		"ipreason": "commandIpreason",
		"ipspecreason": "commandIpSpecReason",
		"kick": "commandKick",
		"banreason": "commandReason",
		"unban": "commandUnban",
		"unipban": "commandUnipban",
		"freeze": "commandFreeze",
		"stop": "commandFreeze",
		"unfreeze": "commandUnFreeze",
		"defreeze": "commandUnFreeze",
		"unstop": "commandUnFreeze",
		"ipshun": "commandIpSpec",
		"unipshun": "commandUnipSpec",
		"ipspec": "commandIpSpec",
		"unipspec": "commandUnIpSpec",
		"banish": "commandBanish",
		"worldkick": "commandBanish",
		"worldban": "commandWorldBan",
		"unworldban": "commandUnWorldBan",
		"deworldban": "commandUnWorldBan",
		"spec": "commandSpec",
		"unspec": "commandDeSpec",
		"undo": "commandUndo",
		"redo": "commandRedo",

		"silence": "commandSilence",
		"desilence": "commandDesilence",
		"unsilence": "commandDesilence",
		"hide": "commandHide",
		"cloak": "commandHide",
		"overload": "commandOverload",
		#"send": "commandSend",
		"blazer": "commandBlazer",
	}
	hooks = {
		"blockchange": "blockChanged",
		"newworld": "newWorld",		"playerpos": "playerMoved",	}	def gotClient(self):
		self.client.var_undolist = []
		self.client.var_redolist = []		self.hidden = False
	def blockChanged(self, x, y, z, block, selected_block, fromloc):
		"Hook trigger for block changes."
		world = self.client.world
		originalblock = world.blockstore.raw_blocks[world.blockstore.get_offset(x, y, z)]
		block = chr(block)
		if len(self.client.var_undolist) < maxundos:
			self.client.var_undolist.insert(0,((x,y,z),block,originalblock))
		else:
			del self.client.var_undolist[-1]
			self.client.var_undolist.insert(0,((x,y,z),block,originalblock))

	def newWorld(self, world):
		"Hook to reset undolist in new worlds."
		self.client.var_undolist = []

	def playerMoved(self, x, y, z, h, p):
		"Stops transmission of player positions if hide is on."
		if self.hidden:
			return False

	@player_list
	@mod_only
	def commandKick(self, parts, fromloc, overriderank):
		"/kick username [reason] - Mod\nKicks the Player off the server."
		user = parts[1]
		if len(parts) > 1:
			user.sendError("Kicked: %s" % " ".join(parts[2:]))
		else:
			user.sendError("You got kicked.")
		self.client.sendServerMessage("User %s has been kicked." % user)
	@player_list
	@admin_only
	def commandBanBoth(self, parts, fromloc, overriderank):
		"/banb username reason - Admin\nName and IP ban a Player from this server."
		username = parts[1]
		if len(parts) <= 1:
			self.client.sendServerMessage("Please give a reason.")
			return
		else:
			if username in self.client.factory.usernames:
				self.commandIpban(parts, "command", overriderank)
			else:
				# Nope, the user's not online. Let's do it ourselves. Query the IP
				with Persist(username) as p:
					ip = p.string("misc", "ip")
				# User's ip cannot be found (means that user never came on the server). Return error
				if ip == "":
					self.client.sendServerMessage("Warning: %s has never come on the server, therefore no IP record of that user.")
			if self.client.factory.isIpBanned(ip):
				self.client.sendServerMessage("%s is already IPBanned." % username)
			else:
				self.client.factory.addIpBan(ip, " ".join(params))
			if username in self.client.factory.usernames:
				self.client.factory.usernames[username].sendError("You got banned: %s" % "".join(params))
			self.commandBan(parts, "command", overriderank)
	@player_list
	@admin_only
	def commandBan(self, parts, fromloc, overriderank):
		"/ban username reason - Admin\nBans the Player from this server."
		username = parts[1]
		if len(parts) <= 1:
			self.client.sendServerMessage("Please specify a reason.")
			return
		if self.client.factory.isBanned(username):
			self.client.sendServerMessage("%s is already banned." % username)
			return
		else:
			self.client.factory.addBan(username, " ".join(parts[2:]))
			if username in self.client.factory.usernames:
				self.client.factory.usernames[username].sendError("You got banned: %s" % parts[2:])
			self.client.sendServerMessage("%s has been banned." % username)

	@player_list
	@director_only
	def commandIpban(self, parts, fromloc, overriderank):
		"/ipban username reason - Director\nBan a Player's IP from this server."
		username = parts[1]
		if len(parts) <= 1:
			self.client.sendServerMessage("Please specify a reason.")
			return
		if username in self.client.factory.usernames:
			ip = self.client.factory.usernames[username].transport.getPeer().host
		else:
			with Persist(username) as p:
				ip = p.string("misc", "ip")
				if ip == "":
					self.client.sendServerMessage("%s has never come on the server, therefore no IP record of that user." % username)
		if self.client.factory.isIpBanned(ip):
			self.client.sendServerMessage("%s is already IPBanned." % ip)
		else:
			self.client.factory.addIpBan(ip, " ".join(parts[2:]))
		if username in self.client.factory.usernames:
			self.client.factory.usernames[username].sendError("You got banned: %s" % "".join(parts[2:]))
		self.client.sendServerMessage("IP %s has been IPBanned." % ip)

	@player_list
	@admin_only
	@only_username_command
	def commandUnban(self, username, fromloc, overriderank):
		"/unban username - Admin\nRemoves the Ban on the Player."
		if not self.client.factory.isBanned(username):
			self.client.sendServerMessage("%s is not banned." % username)
		else:
			self.client.factory.removeBan(username)
			self.client.sendServerMessage("%s has been unbanned." % username)

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
			self.client.sendServerMessage("%s was not specced." % username)
		self.client.sendServerMessage("%s is no longer a spec." % username)
		if username in self.client.factory.usernames:
			self.client.factory.usernames[username].sendSpectatorUpdate()
	@player_list
	@director_only
	@only_string_command("IP")
	def commandUnipban(self, ip, fromloc, overriderank):
		"/unipban ip - Director\nRemoves the Ban on the IP."
		if not self.client.factory.isIpBanned(ip):
			self.client.sendServerMessage("IP %s is not banned." % ip)
		else:
			self.client.factory.removeIpBan(ip)
			self.client.sendServerMessage("IP %s has been unbanned." % ip)

	@player_list
	@admin_only
	@only_username_command
	def commandReason(self, username, fromloc, overriderank):
		"/banreason username - Admin\nGives the reason a Player was Banned."
		if not self.client.factory.isBanned(username):
			self.client.sendServerMessage("%s is not banned." % username)
		else:
			self.client.sendServerMessage("Reason: %s" % self.client.factory.banReason(username))

	@player_list
	@director_only
	@only_string_command("IP")
	def commandIpreason(self, ip, fromloc, overriderank):
		"/ipreason username - Director\nGives the reason an IP was Banned."
		if not self.client.factory.isIpBanned(ip):
			self.client.sendServerMessage("IP %s is not banned." % ip)
		else:
			self.client.sendServerMessage("Reason: %s" % self.client.factory.ipBanReason(ip))

	@player_list
	@director_only
	@only_string_command("IP")
	def commandIpSpecReason(self, ip, fromloc, overriderank):
		"/ipspecreason username - Director\nGives the reason an IP was Banned."
		if not self.client.factory.isIpSpecced(ip):
			self.client.sendServerMessage("IP %s is not specced." % ip)
		else:
			self.client.sendServerMessage("Reason: %s" % self.client.factory.ipSpecReason(ip))

	@player_list
	@mod_only
	def commandUnFreeze(self, parts, fromloc, overriderank):
		"/unfreeze username - Mod\nAliases: defreeze, unstop\nUnfreezes the player, allowing them to move again."
		username = parts[1]
		if username == "":
			self.client.sendServerMessage("Please specify a username.")
			return
		if username not in self.client.factory.usernames:
			self.client.sendServerMessage("User %s is not online." % username)
			return
		else:
			user = self.client.factory.usernames[username]
			user.frozen = False
			user.sendNormalMessage("&4You have been unfrozen by %s!" % self.client.username)

	@player_list
	@mod_only
	def commandFreeze(self, parts, fromloc, overriderank):
		"/freeze username - Mod\nAliases: stop\nFreezes the player, preventing them from moving."
		username = parts[1]
		if username == "":
			self.client.sendServerMessage("Please specify a username.")
			return
		if username not in self.client.factory.usernames:
			self.client.sendServerMessage("User %s is not online." % username)
			return
		else:
			user = self.client.factory.usernames[username]
			user.frozen = True
			user.sendNormalMessage("&4You have been frozen by %s!" % self.client.username)

	@player_list
	@mod_only
	def commandIpSpec(self, username, fromloc, overriderank):
		"/ipspec username reason - Mod\nAliases: ipshun\nIPSpec a Player's IP in this server."
		username = parts[1]
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a reason.")
			return
		if username in factory.mods:
			self.client.sendServerMessage("You cannot spec a staff!")
			return
		if username in self.client.factory.usernames:
			ip = self.client.factory.usernames[username].transport.getPeer().host
		else:
			with Persist(username) as p:
				ip = p.string("misc", "ip")
				if ip == "":
					self.client.sendServerMessage("Warning: %s has never come on the server, therefore no IP record of that user." % username)
		if self.client.factory.isIpSpecced(ip):
			self.client.sendServerMessage("%s is already IPSpecced." % ip)
			return
		else:
			self.client.factory.addIpSpec(ip, reason)
			if username in self.client.factory.usernames:
				self.client.factory.usernames[username].sendSpectatorUpdate()
				self.client.factory.usernames[username].sendServerMessage("You got IPSpecced!")
			self.client.sendServerMessage("%s has been IPSpecced." % ip)

	@player_list
	@mod_only
	@only_string_command("IP")
	def commandUnIpSpec(self, ip, fromloc, overriderank):
		"/unipspec ip - Mod\nAliases: unipshun\nRemoves the IPSpec on the IP."
		if not self.client.factory.isIpSpecced(ip):
			self.client.sendServerMessage("%s is not IPSpecced." % ip)
		else:
			self.client.factory.removeIpSpec(ip)
			self.client.sendServerMessage("%s has been unIPspecced." % ip)
	@mod_only	def commandSay(self, parts, byuser, overriderank):		"/say message - Mod\nAliases: msg\nPrints out message in the server color."		if len(parts) == 1:			self.client.sendServerMessage("Please type a message.")		else:			self.client.factory.queue.put((self.client, TASK_SERVERMESSAGE, ("[MSG] "+(" ".join(parts[1:])))))

	def chatmsg(self, message):
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
	@only_username_command
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
	def commandUnWorldBan(self, username, fromloc, overriderank):
		"/unworldban username - Op\nAliases: deworldban\nRemoves the WorldBan on the Player."
		if not self.client.world.isWorldBanned(username):
			self.client.sendServerMessage("%s is not WorldBanned." % username)
		else:
			self.client.world.delete_worldban(username)
			self.client.sendServerMessage("%s was UnWorldBanned." % username)
	@build_list
	def commandUndo(self, parts, fromloc, overriderank):
		"/undo numchanges [username] - Guest\nUndoes yours or other people's changes (If Mod+)"
		world = self.client.world
		if len(parts) == 3:
			if not self.client.isMod():
				self.client.sendServerMessage("You are not a Mod+")
				return
			try:
				username = parts[2].lower()
				user = self.client.factory.usernames[username]
			except:
				self.client.sendServerMessage("%s is not online." % parts[2])
				return
			var_sublist = user.var_undolist[:]
			undolistlength = len(user.var_undolist)
			if parts[1] == "all":
				def generate_changes():
					try:
						user = self.client.factory.usernames[username]
						for index in range(undolistlength):
							originalblock = user.var_undolist[index][2]
							block = user.var_undolist[index][1]
							i,j,k = user.var_undolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You do not have permission to build here.")
								return
							del var_sublist[var_sublist.index(((i,j,k),block,originalblock))]
							user.var_redolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds undo error.")
								return
							user.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							user.sendBlock(i, j, k, originalblock)
							yield
						user.var_undolist = var_sublist
					except:
						self.client.sendSplitServerMessage("The user seems to have logged off before the undo could finish.")
						return
			else:
				try:
					num = int(parts[1])
				except:
					self.client.sendServerMessage("The numchanges must be a number or 'all'.")
					return
				if num > undolistlength:
					self.client.sendServerMessage("They have not made that many changes.")
					return
				def generate_changes():
					try:
						for index in range(num):
							originalblock = user.var_undolist[index][2]
							block = user.var_undolist[index][1]
							i,j,k = user.var_undolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You do not have permission to build here.")
								return
							del var_sublist[var_sublist.index(((i,j,k),block,originalblock))]
							user.var_redolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds undo error.")
								return
							user.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							user.sendBlock(i, j, k, originalblock)
							yield
						user.var_undolist = var_sublist
					except:
						self.client.sendSplitServerMessage("The user seems to have logged off before the undo could finish.")
						return
		else:
			self.client.sublist = self.client.var_undolist[:]
			undolistlength = len(self.client.var_undolist)
			if len(parts) == 1:
				self.client.sendSplitServerMessage("Please specify a number of changes to undo or 'all' (and if you are Mod+ you can specify a username)")
				return
			else:
				if parts[1] == "all":
					def generate_changes():
						for index in range(undolistlength):
							originalblock = self.client.var_undolist[index][2]
							block = self.client.var_undolist[index][1]
							i,j,k = self.client.var_undolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You no longer have permission to build here.")
								return
							del self.client.sublist[self.client.sublist.index(((i,j,k),block,originalblock))]
							self.client.var_redolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds undo error.")
								return
							self.client.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							self.client.sendBlock(i, j, k, originalblock)
							yield
						self.client.var_undolist = self.client.sublist
				else:
					try:
						num = int(parts[1])
					except:
						self.client.sendServerMessage("The numchanges must be a number or 'all'.")
						return
					if num > undolistlength:
						self.client.sendServerMessage("You have not made that many changes.")
						return
					def generate_changes():
						for index in range(num):
							originalblock = self.client.var_undolist[index][2]
							block = self.client.var_undolist[index][1]
							i,j,k = self.client.var_undolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You no longer have permission to build here.")
								return
							del self.client.sublist[self.client.sublist.index(((i,j,k),block,originalblock))]
							self.client.var_redolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds undo error.")
								return
							self.client.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							self.client.sendBlock(i, j, k, originalblock)
							self.client.total += 1
							yield
						self.client.var_undolist = self.client.sublist
		# Now, set up a loop delayed by the reactor
		block_iter = iter(generate_changes())
		def do_step():
			# Do 10 blocks
			try:
				for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
					block_iter.next()
				reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
			except StopIteration:
				if fromloc == 'user':
					self.client.finalizeMassCMD('undo', self.client.total)
					self.client.total = 0
				pass
		do_step()

	@build_list
	def commandRedo(self, parts, fromloc, overriderank):
		"/redo numchanges [username] - Guest\nRedoes yours or other people's changes (If Mod+)"
		world = self.client.world
		if len(parts) == 3:
			if not self.client.isMod():
				self.client.sendServerMessage("You are not a Mod+")
				return
			try:
				username = parts[2].lower()
				user = self.client.factory.usernames[username]
			except:
				self.client.sendServerMessage("%s is not online." % parts[2])
				return
			var_sublist = user.var_redolist[:]
			redolistlength = len(user.var_redolist)
			if parts[1] == "all":
				def generate_changes():
					try:
						user = self.client.factory.usernames[username]
						for index in range(redolistlength):
							originalblock = user.var_redolist[index][2]
							block = user.var_redolist[index][1]
							i,j,k = user.var_redolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You do not have permission to build here.")
								return
							del var_sublist[var_sublist.index(((i,j,k),block,originalblock))]
							user.var_undolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds redo error.")
								return
							user.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							user.sendBlock(i, j, k, originalblock)
							self.client.total += 1 # This is how you increase a number in python.... - Stacy
							yield
						user.var_redolist = var_sublist
					except:
						self.client.sendSplitServerMessage("The user seems to have logged off before the redo could finish.")
						return
			else:
				try:
					num = int(parts[1])
				except:
					self.client.sendServerMessage("The numchanges must be a number or 'all'.")
					return
				if num > redolistlength:
					self.client.sendServerMessage("They have not made that many undos.")
					return
				def generate_changes():
					try:
						for index in range(num):
							originalblock = user.var_redolist[index][2]
							block = user.var_redolist[index][1]
							i,j,k = user.var_redolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You do not have permission to build here.")
								return
							del var_sublist[var_sublist.index(((i,j,k),block,originalblock))]
							user.var_undolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds redo error.")
								return
							user.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							user.sendBlock(i, j, k, originalblock)
							self.client.total += 1 # This is how you increase a number in python.... - Stacy
							yield
						user.var_redolist = var_sublist
					except:
						self.client.sendSplitServerMessage("The user seems to have logged off before the redo could finish.")
						return
		else:
			self.client.sublist = self.client.var_redolist[:]
			redolistlength = len(self.client.var_redolist)
			if len(parts) == 1:
				self.client.sendSplitServerMessage("Please specify a number of changes to redo or 'all' (and if you are Mod+ you can specify a username)")
				return
			else:
				if parts[1] == "all":
					def generate_changes():
						for index in range(redolistlength):
							originalblock = self.client.var_redolist[index][2]
							block = self.client.var_redolist[index][1]
							i,j,k = self.client.var_redolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You no longer have permission to build here.")
								return
							del self.client.sublist[self.client.sublist.index(((i,j,k),block,originalblock))]
							self.client.var_undolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds redo error.")
								return
							self.client.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							self.client.sendBlock(i, j, k, originalblock)
							self.client.total += 1 # This is how you increase a number in python.... - Stacy
							yield
						self.client.var_redolist = self.client.sublist
				else:
					try:
						num = int(parts[1])
					except:
						self.client.sendServerMessage("The numchanges must be a number or 'all'.")
						return
					if num > redolistlength:
						self.client.sendServerMessage("You have not made that many undos.")
						return
					def generate_changes():
						for index in range(num):
							originalblock = self.client.var_redolist[index][2]
							block = self.client.var_redolist[index][1]
							i,j,k = self.client.var_redolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You no longer have permission to build here.")
								return
							del self.client.sublist[self.client.sublist.index(((i,j,k),block,originalblock))]
							self.client.var_undolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds redo error.")
								return
							self.client.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							self.client.sendBlock(i, j, k, originalblock)
							self.client.total += 1 # This is how you increase a number in python.... - Stacy
							yield
						self.client.var_redolist = self.client.sublist
		# Now, set up a loop delayed by the reactor
		block_iter = iter(generate_changes())
		def do_step():
			# Do 10 blocks
			try:
				for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
					block_iter.next()
				reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
			except StopIteration:
				if fromloc == 'user':
					self.client.finalizeMassCMD('redo', self.client.total)
					self.client.total = 0
				pass
		do_step()
	@player_list
	@mod_only
	@only_username_command
	def commandSilence(self, username, fromloc, overriderank):
		"/silence username - Mod\nDisallows the Player to talk."
		if self.client.factory.usernames[username].isMod():
			self.client.sendServerMessage("You cannot silence staff!")
			return
		self.client.factory.silenced.add(username)
		self.client.sendServerMessage("%s is now Silenced." % username)

	@player_list
	@mod_only
	@only_username_command
	def commandDesilence(self, username, fromloc, overriderank):
		"/desilence username - Mod\nAliases: unsilence\nAllows the Player to talk."
		if self.client.factory.isSilenced(username):
			self.client.factory.silenced.remove(username)
			self.client.sendServerMessage("%s is no longer Silenced." % username.lower())
		else:
			self.client.sendServerMessage("User specified is not silenced.")

	@player_list
	@op_only
	def commandHide(self, params, fromloc, overriderank):
		"/hide - Op\nAliases: cloak\nHides you so no other players can see you. Toggle."
		if not self.hidden:
			self.client.sendServerMessage("You have vanished.")
			self.hidden = True
			# Send the "player has disconnected" command to people
			self.client.queueTask(TASK_PLAYERLEAVE, [self.client.id])
		else:
			self.client.sendServerMessage("That was Magic!")
			self.hidden = False
			#Imagine that! They've mysteriously appeared.
			self.client.queueTask(TASK_NEWPLAYER, [self.client.id, self.client.username, self.client.x, self.client.y, self.client.z, self.client.h, self.client.p])
			#self.client.queueTask(TASK_PLAYERCONNECT, [self.client.id, self.client.username, self.client.x, self.client.y, self.client.z, self.client.h, self.client.p])

	@mod_only
	def commandBlazer(self, parts, fromloc, overriderank):
		"/blazer - Mod\nBlazer!"
		for i in range(10):
			self.client.sendServerMessage("SPAM!")

	@player_list
	@admin_only
	@only_username_command
	def commandOverload(self, client, fromloc, overriderank):
		"/overload username - Admin\nSends the players client a massive fake map."
		client.sendOverload()
		self.client.sendServerMessage("Overload sent to %s" % client.username)

	#@player_list
	#@mod_only
	#@only_username_command
	#def commandSend(self, client, fromloc, overriderank):
		#"/send username [world] - Mod\nSends the players client another world."
		#if user.isMod():
			#self.client.sendServerMessage("You cannot send Staff!")
		#if len(parts) == 2:
			#self.client.sendServerMessage("Please specify a world ID.")
		#else:
			#world_id = parts[2]
			#user.changeToWorld("%s" % world_id)
			#else:
				#user.sendServerMessage("You were sent to '%s'." % self.client.world.id)
				#user.changeToWorld("default")
				#self.client.sendServerMessage("Player %s was sent." % user.username)
		#else:
			#self.client.sendServerMessage("Your Player is in another world!")