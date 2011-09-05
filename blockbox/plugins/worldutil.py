# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import os, shutil

from lib.twisted.internet import reactor

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin
from blockbox.world import World

class WorldUtilPlugin(ProtocolPlugin):
	"Commands that handle world creation/deletion, options, etc."

	commands = {
		"private": "commandPrivate",
		"lock": "commandLock",
		"gchat": "commandGChat",
		#"ponly": "commandPOnly"
		"asd":"commandASD",
		"setowner": "commandSetOwner",
		"owner": "commandSetOwner",
		"worldowner": "commandSetOwner",
		"setspawn": "commandSetspawn",

		"new": "commandNew",
		#"mapadd": "commandNew",
		"rename": "commandRename",
		#"maprename": "commandRename",
		"shutdown": "commandShutdown",
		"boot": "commandBoot",
		"reboot": "commandReboot",
		"create": "commandCreate",
		"delete": "commandDelete",
		#"mapdelete": "commandDelete",
		"undelete": "commandUnDelete",
		"deleted": "commandDeleted",

		"goto": "commandLoad",
		"l": "commandLoad",
		"load": "commandLoad",
		"join": "commandLoad",

		"worlds": "commandWorlds",
		"levels": "commandWorlds",
		"maps": "commandWorlds",
		"templates": "commandTemplates",

		"home": "commandHome",

		"physics": "commandPhysics",
		"physflush": "commandPhysflush",
		"unflood": "commandUnflood",
		"deflood": "commandUnflood",
		"fwater": "commandFwater",

		"backup": "commandBackup",
		"backups": "commandBackups",
		"restore": "commandRestore",
	}

	@config("category", "world")
	@config("rank", "op")
	@on_off_command
	def commandPrivate(self, onoff, fromloc, overriderank):
		"/private on|off - Op\nEnables or disables the private status for this world."
		if onoff == "on":
			self.client.world.private = True
			self.client.sendWorldMessage("This world is now private.")
			self.client.sendServerMessage("%s is now private." % self.client.world.id)
		else:
			self.client.world.private = False
			self.client.sendWorldMessage("This world is now public.")
			self.client.sendServerMessage("%s is now public." % self.client.world.id)

	@config("category", "world")
	@config("rank", "op")
	@on_off_command
	def commandLock(self, onoff, fromloc, overriderank):
		"/lock on|off - Op\nEnables or disables the world lock."
		if onoff == "on":
			self.client.world.all_write = False
			self.client.sendWorldMessage("This world is now locked.")
			self.client.sendServerMessage("Locked %s" % self.client.world.id)
		else:
			self.client.world.all_write = True
			self.client.sendWorldMessage("This world is now unlocked.")
			self.client.sendServerMessage("Unlocked %s" % self.client.world.id)

	@config("category", "world")
	@config("rank", "mod")
	@on_off_command
	def commandGChat(self, onoff, fromloc, rankoverride):
		"/gchat on|off - Mod\nTurns Global Chat on or off in this world.\nWorldChat is used instead if off."
		self.client.world.global_chat = onoff == "on"
		self.client.sendServerMessage("Global chat is now %s for this world." %onoff)

	#@config("rank", "op")
	#@on_off_command
	#def commandPOnly(self, onoff, fromloc, rankoverride):
		#"/ponly on/off - Makes the world only accessable by portals."
		#if onoff == "on":
			#self.client.world.portal_only = True
			#self.client.sendWorldMessage("This world is now portal only.")
			#self.client.sendServerMessage("%s is now only accessable through portals." % self.client.world.id)
		#else:
			#self.client.world.portal_only = False
			#elf.client.sendWorldMessage("This world is now accesable through commands.")
			#self.client.sendServerMessage("%s is now accessable through commands." % self.client.world.id)

	@config("category", "world")
	@config("rank", "admin")
	def commandNew(self, parts, fromloc, overriderank):
		"/new worldname templatename - Admin\nMakes a new world, and boots it."
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a new worldname.")
		elif self.client.factory.world_exists(parts[1]):
			self.client.sendServerMessage("Worldname in use")
		else:
			if len(parts) == 2:
				self.client.sendServerMessage("Sorry, but you need to specify a template.")
				return
			elif len(parts) == 3 or len(parts) == 4:
				template = parts[2]
			world_id = parts[1].lower()
			try:
				self.client.factory.newWorld(world_id, template)
			except TemplateDoesNotExist:
				self.client.sendServerMessage("That template does not exist.")
				return
			self.client.factory.loadWorld("mapdata/worlds/%s" % world_id, world_id)
			self.client.factory.worlds[world_id].all_write = False
			if len(parts) < 4:
				self.client.sendServerMessage("World '%s' made and booted." % world_id)

	@config("category", "world")
	@config("rank", "mod")
	def commandRename(self, parts, fromloc, overriderank):
		"/rename worldname newworldname - Mod\nRenames a shut down world."
		if len(parts) < 3:
			self.client.sendServerMessage("Please specify two worldnames.")
		else:
			old_worldid = parts[1]
			new_worldid = parts[2]
			if old_worldid in self.client.factory.worlds:
				self.client.sendServerMessage("World '%s' is booted, please shut it down before continuing." % old_worldid)
			elif not self.client.factory.world_exists(old_worldid):
				self.client.sendServerMessage("No such world %s." % old_worldid)
			elif self.client.factory.world_exists(new_worldid):
				self.client.sendServerMessage("World called %s already exists." % new_worldid)
			else:
				self.client.factory.renameWorld(old_worldid, new_worldid)
				self.client.sendServerMessage("World %s has been renamed to %s." % (old_worldid, new_worldid))

	@config("category", "world")
	@config("rank", "mod")
	def commandShutdown(self, parts, fromloc, overriderank):
		"/shutdown worldname - Mod\nTurns off the named world."
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a worldname.")
		else:
			if parts[1] in self.client.factory.worlds:
				self.client.factory.unloadWorld(parts[1])
				self.client.sendServerMessage("World %s unloaded." % parts[1])
			else:
				self.client.sendServerMessage("No such world %s." % parts[1])

	@config("category", "world")
	@config("rank", "mod")
	def commandReboot(self, parts, fromloc, overriderank):
		"/reboot worldname - Mod\nReboots a map"
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a worldname.")
		else:
			if parts[1] in self.client.factory.worlds:
				self.client.factory.rebootWorld(parts[1])
				self.client.sendServerMessage("World %s rebooted." % parts[1])
			else:
				self.client.sendServerMessage("World '%s' isn't booted." % parts[1])

	@config("category", "world")
	@config("rank", "mod")
	def commandBoot(self, parts, fromloc, overriderank):
		"/boot worldname - Mod\nStarts up a new world."
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a worldname.")
		else:
			if parts[1] in self.client.factory.worlds:
				self.client.sendServerMessage("World '%s' already exists!" % parts[1])
			else:
				try:
					self.client.factory.loadWorld("mapdata/worlds/%s" % parts[1], parts[1])
					self.client.sendServerMessage("World '%s' booted." % parts[1])
				except AssertionError:
					self.client.sendServerMessage("There is no world by that name.")

	@config("category", "world")
	@only_string_command("world name")
	def commandLoad(self, world_id, fromloc, overriderank, params=None):
		"/l worldname - Guest\nAliases: goto, join, load\nMoves you into world 'worldname'"
		if world_id not in self.client.factory.worlds:
			self.client.sendServerMessage("Attempting to boot and join '%s'" % world_id)
			try:
				self.client.factory.loadWorld("mapdata/worlds/%s" % world_id, world_id)
			except AssertionError:
				self.client.sendServerMessage("There is no world by that name.")
				return
		world = self.client.factory.worlds[world_id]
		if not self.client.canEnter(world):
			if world.private:
				self.client.sendServerMessage("'%s' is private; you're not allowed in." % world_id)
				return
			else:
				self.client.sendServerMessage("You're WorldBanned from '%s'; so you're not allowed in." % world_id)
				return
		self.client.changeToWorld(world_id)

	@config("category", "world")
	def commandWorlds(self, parts, fromloc, overriderank):
		"/worlds [letter|all] - Guest\nAliases: maps, levels\nLists available worlds - by letter, online, or all."
		if len(parts) != 2 and len(parts) != 3:
			self.client.sendServerMessage("Do /worlds all for all worlds or choose a letter.")
			self.client.sendServerList(["Online:"] + [id for id, world in self.client.factory.worlds.items() if self.client.canEnter(world)])
			return
		else:
			if parts[1] == 'all':
				self.client.sendServerList(["Worlds:"] + os.listdir("mapdata/worlds/"))
				return
			if len(parts[1]) != 1:
				self.client.sendServerMessage("Only specify one starting letter per entry, not multiple")
				return
			if len(parts) == 3:
				if len(parts[2]) != 1:
					self.client.sendServerMessage("Only specify one starting letter per entry, not multiple")
					return
			letter1 = ord(parts[1].lower())
			if len(parts) == 3:
				letter2 = ord(parts[2].lower())
			else:
				letter2 = letter1
			if letter1 > letter2:
				a = letter1
				letter1 = letter2
				letter2 = a
			worldlist = os.listdir("mapdata/worlds/")
			newlist = []
			for world in worldlist:
				if letter1 <= ord(world[0]) <= letter2 and not world.startswith("."):
					newlist.append(world)
			self.client.sendServerList(["Worlds:"] + newlist)

	@config("category", "world")
	def commandTemplates(self, parts, fromloc, overriderank):
		"/templates - Guest\nLists available templates"
		self.client.sendServerList(["Templates:"] + os.listdir("mapdata/templates/"))

	def commandHome(self, parts, fromloc, overriderank):
		"/home [worldname] - Guest\nGoes to and/or changes your home world."
		if not len(parts) > 1:
			self.client.changeToWorld(self.client.homeworld)
		else:
			self.client.homeworld = parts[1]
			self.client.persist.set("main", "homeworld", parts[1])
			self.client.sendServerMessage("Your home world is now %s!" % parts[1])

	@config("category", "world")
	@config("rank", "admin")
	def commandCreate(self, parts, fromloc, overriderank):
		"/create worldname width height length - Admin\nCreates a new world with specified dimensions."
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a world name.")
		elif self.client.factory.world_exists(parts[1]):
			self.client.sendServerMessage("Worldname in use.")
		elif len(parts) < 5:
			self.client.sendServerMessage("Please specify dimensions. (width, length, height)")
		elif int(parts[2]) < 16 or int(parts[3]) < 16 or int(parts[4]) < 16:
			self.client.sendServerMessage("No dimension may be smaller than 16.")
		elif int(parts[2]) > 1024 or int(parts[3]) > 1024 or int(parts[4]) > 1024:
			self.client.sendServerMessage("No dimension may be greater than 1024.")
		elif (int(parts[2]) % 16) > 0 or (int(parts[3]) % 16) > 0 or (int(parts[4]) % 16) > 0:
			self.client.sendServerMessage("All dimensions must be divisible by 16.")
		else:
			world_id = parts[1].lower()
			sx, sy, sz = int(parts[2]), int(parts[3]), int(parts[4])
			grass_to = (sy // 2)
			world = World.create(
				"mapdata/worlds/%s" % world_id,
				sx, sy, sz, # Size
				sx//2,grass_to+2, sz//2, 0, # Spawn
				([BLOCK_DIRT]*(grass_to-1) + [BLOCK_GRASS] + [BLOCK_AIR]*(sy-grass_to)) # Levels
			)
			self.client.factory.loadWorld("mapdata/worlds/%s" % world_id, world_id)
			self.client.factory.worlds[world_id].all_write = False
			self.client.sendServerMessage("World '%s' made and booted." % world_id)

	@config("category", "world")
	@config("rank", "admin")
	def commandDelete(self, parts, fromloc, overriderank):
		"/delete worldname - Admin\nSets the specified world to 'ignored'."
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a worldname.")
			return
		else:
			if not os.path.exists("mapdata/worlds/%s" % parts[1]):
				self.client.sendServerMessage("World %s doesn't exist." %(parts[1]))
				return
			if parts[1] in self.client.factory.worlds:
				self.client.factory.unloadWorld(parts[1])
			name = parts[1]
			extra= "_0"
			if os.path.exists("mapdata/worlds/.trash/%s" % name):
				while True:
					if os.path.exists("mapdata/worlds/.trash/%s" % (name + extra)):
						extra = "_" + str(int(extra[1:])+1)
					else:
						name = name + extra
						break
			shutil.copytree("mapdata/worlds/%s" % parts[1], "mapdata/worlds/.trash/%s" % parts[1])
			shutil.rmtree("mapdata/worlds/%s" % parts[1])
			self.client.sendServerMessage("World %s deleted." % name)

	@config("category", "world")
	@config("rank", "admin")
	def commandUnDelete(self, parts, fromloc, overriderank):
		"/undelete worldname - Admin\nRestores a deleted map."
		if len(parts) < 2:
			self.client.sendServerMessage("Please specify a worldname.")
			return
		name = parts[1]
		world_dir = ("mapdata/worlds/.trash/%s/" % name)
		if not os.path.exists(world_dir):
		   self.client.sendServerMessage("World %s is not in the world trash bin." % name)
		   return
		extra="_0"
		if os.path.exists("mapdata/worlds/%s/" % name):
			while True:
				if os.path.exists("mapdata/worlds/%s/" % (name + extra)):
					extra = "_" + str(int(extra[1:])+1)
				else:
					name = name + extra
					break
		path = ("mapdata/worlds/%s/" % name)
		shutil.move(world_dir, path)
		self.client.sendServerMessage("World %s restored as %s." % (parts[1], name))

	@config("category", "world")
	@config("rank", "admin")
	def commandDeleted(self, parts, fromloc, overriderank):
		"/deleted [letter] - Admin\nLists deleted worlds - by letter or all."
		if len(parts) != 2 and len(parts) != 3:
			self.client.sendServerMessage("Do '/deleted letter' for all starting with a letter.")
			self.client.sendServerList(["Deleted:"] + os.listdir("mapdata/worlds/.trash/"))
			return
		else:
			if len(parts[1]) != 1:
				self.client.sendServerMessage("Only specify one starting letter per entry, not multiple.")
				return
			if len(parts) == 3:
				if len(parts[2]) != 1:
					self.client.sendServerMessage("Only specify one starting letter per entry, not multiple.")
					return
			letter1 = ord(parts[1].lower())
			if len(parts) == 3:
				letter2 = ord(parts[2].lower())
			else:
				letter2 = letter1
			if letter1 > letter2:
				a = letter1
				letter1 = letter2
				letter2 = a
			worldlist = os.listdir("mapdata/worlds/.trash/")
			newlist = []
			for world in worldlist:
				if letter1 <= ord(world[0]) <= letter2 and not world.startswith("."):
					newlist.append(world)
			self.client.sendServerList(["Deleted:"] + newlist)

	@config("category", "world")
	@config("rank", "op")
	def commandUnflood(self, parts, fromloc, overriderank):
		"/unflood worldname - Op\nAliases: deflood\nSlowly removes all water and lava from the map."
		self.client.world.start_unflooding()
		self.client.sendWorldMessage("Unflooding has been initiated.")

	@config("category", "world")
	@config("rank", "admin")
	@on_off_command
	def commandPhysics(self, onoff, fromloc, overriderank):
		"/physics on|off - Admin\nEnables or disables physics in this world."
		if onoff == "on":
			if self.client.world.physics:
				self.client.sendWorldMessage("Physics is already on here.")
			else:
				if self.client.factory.numberWithPhysics() >= self.client.factory.config["physics_limit"]:
					self.client.sendWorldMessage("There are already %s worlds with physics on (the max)." % self.client.factory.config["physics_limit"])
				else:
					self.client.world.physics = True
					self.client.sendWorldMessage("This world now has physics enabled.")
		else:
			if not self.client.world.physics:
				self.client.sendWorldMessage("Physics is already off here.")
			else:
				self.client.world.physics = False
				self.client.sendWorldMessage("This world now has physics disabled.")

	@config("category", "world")
	@config("rank", "op")
	@on_off_command
	def commandFwater(self, onoff, fromloc, overriderank):
		"/fwater on|off - Op\nEnables or disables finite water in this world."
		if onoff == "on":
			self.client.world.finite_water = True
			self.client.sendWorldMessage("This world now has finite water enabled.")
		else:
			self.client.world.finite_water = False
			self.client.sendWorldMessage("This world now has finite water disabled.")

	@config("category", "world")
	@config("rank", "admin")
	@on_off_command
	def commandASD(self, onoff, fromloc, overriderank):
		"/asd on|off - Admin\nEnables or disables whether the world shuts down if no one is on it."
		if onoff == "on":
			self.client.world.autoshutdown = True
			self.client.sendWorldMessage("This world now automaticaly shuts down.")
		else:
			self.client.world.autoshutdown = False
			self.client.sendWorldMessage("This world now shuts down manualy.")

	@config("category", "world")
	@config("rank", "admin")
	def commandPhysflush(self, parts, fromloc, overriderank):
		"/physflush - Admin\nTells the physics engine to rescan the world."
		if self.client.world.physics:
			self.client.world.physics = False
			self.client.world.physics = True
			self.client.sendServerMessage("Physics flush running.")
		else:
			self.client.sendServerMessage("This world does not have physics running.")

	@config("category", "world")
	@config("rank", "op")
	def commandBackup(self, parts, fromloc, overriderank):
		"/backup worldname [backupname] - Op\nMakes a backup copy of the map of the map."
		if len(parts) == 1:
			parts.append(self.client.world.basename.lstrip("mapdata/worlds"))
		world_id = parts[1]
		if len(parts) == 2:
			backupname = parts[2]
		elif backupname == "" or len(parts) == 1:
			backupname = None
		response = self.client.factory.Backup(self, world_id, "user", backupname)
		if response == ("ERROR_WORLD_DOES_NOT_EXIST_%s" % world_id):
			self.client.sendServerMessage("World %s does not exist." % (world_id))
		elif response == ("ERROR_BACKUP_ALREADY_EXISTS_%s" % backupname):
			self.client.sendServerMessage("Backup %s already exists. Pick another name!" % backupname)
		elif response == ("SUCCESS"):
			self.client.sendServerMessage("Backup %s of world %s saved." % (backupname, world_id))
		elif response.isdigit():
			self.client.sendServerMessage("Backup %s of world %s saved." % (response, world_id))

	@config("category", "world")
	@config("rank", "op")
	def commandRestore(self, parts, fromloc, overriderank):
		"/restore worldname number|backupname - Op\nRestore map to indicated number or backup name."
		if len(parts) < 2:
			self.client.sendServerMessage("Please specify at least a world ID!")
		else:
			world_id = parts[1].lower()
			world_dir = ("mapdata/worlds/%s/" % world_id)
			if len(parts) < 3:
				try:
					backups = os.listdir(world_dir+"backup/")
				except:
					self.client.sendServerMessage("Syntax: /restore worldname number")
					return
				backups.sort(lambda x, y: int(x) - int(y))
				backup_number = str(int(backups[-1]))
			else:
				backup_number = parts[2]
			if not os.path.exists(world_dir + "backup/%s/" %backup_number):
				self.client.sendServerMessage("Backup %s does not exist." %backup_number)
			else:
				old_clients = self.client.factory.worlds[world_id].clients
				if not os.path.exists(world_dir + "blocks.gz.new"):
					shutil.copy(world_dir + "backup/%s/blocks.gz" % backup_number, world_dir)
					shutil.copy(world_dir + "backup/%s/world.meta" % backup_number, world_dir)
				else:
					reactor.callLater(1, self.commandRestore(self, parts, overriderank))
				self.client.factory.loadWorld("mapdata/worlds/%s" % world_id, world_id)
				self.client.sendServerMessage("%s has been restored to %s and booted." %(world_id,backup_number))
				self.client.factory.worlds[world_id].clients = old_clients
				for client in self.client.factory.worlds[world_id].clients:
					client.changeToWorld(world_id)

	@config("category", "world")
	@config("rank", "op")
	def commandBackups(self, parts, fromloc, overriderank):
		"/backups - Op\nLists all backups this map has."
		try:
			world_dir = ("mapdata/worlds/%s/" % self.client.world.id)
			folders = os.listdir(world_dir+"backup/")
			Num_backups = list([])
			Name_backups = list([])
			for x in folders:
				if x.isdigit():
					Num_backups.append(x)
				else:
					Name_backups.append(x)
			Num_backups.sort(lambda x, y: int(x) - int(y))
			if Num_backups > 2:
				self.client.sendServerList(["Backups for %s:" % self.client.world.id] + [Num_backups[0] + "-" + Num_backups[-1]] + Name_backups)
			else:
				self.client.sendServerList(["Backups for %s:" % self.client.world.id] + Num_backups + Name_backups)
		except:
			self.client.sendServerMessage("Sorry, but there are no backups for %s." % self.client.world.id)

	@config("category", "world")
	def commandGoto(self, parts, fromloc, overriderank):
		"/goto x y z - Guest\nTeleports you to coords. NOTE: y is up."
		try:
			x = int(parts[1])
			y = int(parts[2])
			z = int(parts[3])
			self.client.teleportTo(x, y, z)
		except IndexError, ValueError:
			self.client.sendServerMessage("Usage: /goto x y z")
			self.client.sendServerMessage("MCLawl users: /l worldname")

	@config("category", "player")
	@config("rank", "mod")
	def commandSetOwner(self, parts, fromloc, overriderank):
		"/setowner username - Mod\nAliases: owner, worldowner\nSets the world's owner string"
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify an World Owner.")
		else:
			self.client.world.owner = str(parts[1])
			self.client.sendServerMessage("The World Owner has been set.")
  
	@config("category", "world")
	@config("rank", "op")
	def commandSetspawn(self, parts, fromloc, overriderank):
		"/setspawn - Op\nSets this world's spawn point to the current location."
		x = self.client.x >> 5
		y = self.client.y >> 5
		z = self.client.z >> 5
		h = int(self.client.h * (360 / 255.0))
		self.client.world.spawn = (x, y, z, h)
		self.client.sendServerMessage("Set spawn point to %s, %s, %s" % (x, y, z))