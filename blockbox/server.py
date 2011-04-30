# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from __future__ import with_statement

import datetime, gc, hashlib, logging, os, random, re, shutil, sys, time, traceback

from collections import defaultdict
from ConfigParser import RawConfigParser as ConfigParser
from Queue import Queue, Empty

from lib.twisted.internet import reactor, task
from lib.twisted.internet.protocol import Factory

from blockbox.console import StdinPlugin
from blockbox.constants import *
from blockbox.globals import *
from blockbox.heartbeat import Heartbeat
from blockbox.irc_client import ChatBotFactory
from blockbox.persistence import PersistenceEngine as Persist
from blockbox.plugins import *
from blockbox.protocol import BlockBoxServerProtocol
from blockbox.timer import ResettableTimer
from blockbox.world import World

class BlockBoxFactory(Factory):
	"""
	Factory that deals with the general world actions and cross-player comms.
	"""
	protocol = BlockBoxServerProtocol

	def __init__(self):
		"""Constructor method."""
		self.initVariables()

	def startFactory(self):
		"""Launches the factory."""
		self.initLoops()

	def initVariables(self):
		"""Loads variables from server configuration."""
		if (os.path.exists("conf/options.dist.ini") and not os.path.exists("conf/options.ini")) or \
			(os.path.exists("conf/plugins.dist.ini") and not os.path.exists("conf/plugins.ini")) or \
			(os.path.exists("conf/server.dist.ini") and not os.path.exists("conf/server.ini")) or \
			(os.path.exists("conf/wordfilter.dist.ini") and not os.path.exists("conf/wordfilter.ini")):
			raise NotConfigured
		self.logger = logging.getLogger("Server")
		self.loops = recursive_default()
		self.timers = recursive_default()
		self.specs = ConfigParser()
		self.last_heartbeat = time.time()
		self.config = ConfigParser()
		self.conf_options = ConfigParser()
		self.conf_plugins = ConfigParser()
		self.wordfilter = ConfigParser()
		self.save_count = 1
		self.delay_count = 1
		self.config.read("conf/server.ini")
		self.conf_options.read("conf/options.ini")
		self.conf_plugins.read("conf/plugins.ini")
		# Initialise internal datastructures
		self.worlds = {}
		self.directors = set()
		self.admins = set()
		self.mods = set()
		self.worldowners = set()
		self.advbuilders = set()
		self.spectators = set()
		self.silenced = set()
		self.banned = {}
		self.ipbanned = {}

		self.use_irc = False
		if os.path.exists("conf/irc.ini"):
			self.use_irc = True
			self.conf_irc = ConfigParser()
			self.conf_irc.read("conf/irc.ini")

		self.use_email = False
		if  (os.path.exists("conf/email.ini")):
			self.use_email = True
			self.conf_email = ConfigParser()
			self.conf_email.read("conf/email.ini")

		self.saving = False
		self.blblimit = defaultdict()
		self.max_clients = self.config.getint("main", "max_clients")
		self.server_name = self.config.get("main", "name")
		self.server_message = self.config.get("main", "description")
		self.initial_greeting = self.config.get("main", "greeting").replace("\\n", "\n")
		self.public = self.config.getboolean("main", "public")
		self.info_url = self.config.get("main", "info_url")
		self.owner = self.config.get("main", "owner").lower()
		self.isDebugging = self.config.getboolean("main", "debug_mode")
		self.enable_archives = self.conf_options.getboolean("worlds", "enable_archives")
		self.duplicate_logins = self.config.getboolean("options", "duplicate_logins")
		self.verify_names = self.config.getboolean("options", "verify_names")
		self.asd_delay = self.conf_options.getint("worlds", "asd_delay")
		self.api_password = self.config.get("network", "api_password")
		self.physics_limit = self.conf_options.getint("worlds", "physics_limit")
		self.console_delay = self.config.getint("options", "console_delay")
		self.credit_name = self.conf_options.get("bank", "credit_name")
		self.initial_amount = self.conf_options.get("bank", "initial_amount")
		self.info_store = self.config.get("options", "info_store")
		self.table_prefix = self.config.get("options", "table_prefix")
		self.main_backup = self.conf_options.get("worlds", "main_backup")
		self.backup_freq = self.conf_options.getint("backup", "backup_freq")
		self.backup_main = self.conf_options.getboolean("backup", "backup_main")
		self.backup_max = self.conf_options.getint("backup", "backup_max")
		self.backup_auto = self.conf_options.getboolean("backup", "backup_auto")
		self.useblblimit = self.conf_options.getboolean("blb", "use_blb_limiter")
		if self.useblblimit:
			self.blblimit["player"] = self.conf_options.getint("blb", "player")
			self.blblimit["builder"] = self.conf_options.getint("blb", "builder")
			self.blblimit["advbuilder"] = self.conf_options.getint("blb", "advbuilder")
			self.blblimit["op"] = self.conf_options.getint("blb", "op")
			self.blblimit["worldowner"] = self.conf_options.getint("blb", "worldowner")
			self.blblimit["mod"] = self.conf_options.getint("blb", "mod")
			self.blblimit["admin"] = self.conf_options.getint("blb", "admin")
			self.blblimit["director"] = self.conf_options.getint("blb", "director")
			self.blblimit["owner"] = self.conf_options.getint("blb", "owner")

		# Parse IRC section
		if self.use_irc:
			self.irc_nick = self.conf_irc.get("irc", "nick")
			self.irc_pass = self.conf_irc.get("irc", "password")
			self.irc_channel = self.conf_irc.get("irc", "channel")
			self.irc_cmdlogs = self.conf_irc.getboolean("irc", "cmdlogs")
		# Parse heartbeat related section
		self.send_heartbeat = self.conf_options.getboolean("heartbeat", "send_heartbeat")
		self.use_blockbeat = self.conf_options.getboolean("heartbeat", "use_blockbeat")
		if self.use_blockbeat:
			self.blockbeat_authkey = self.conf_options.get("heartbeat", "blockbeat_authkey")
			self.blockbeat_passphrase = self.conf_options.get("heartbeat", "blockbeat_passphrase")
		self.main_loaded = False
		# Word Filter
		self.wordfilter.read("conf/wordfilter.ini")
		self.filter = []
		number = self.wordfilter.getint("filter","count")
		for x in range(number):
			self.filter = self.filter + [self.wordfilter.get("filter", "s"+str(x)), self.wordfilter.get("filter", "r" + str(x))]
		# Salt, for the heartbeat server/verify-names
		self.salt = hashlib.md5(hashlib.md5(str(random.getrandbits(128))).digest()).hexdigest()[-32:].strip("0")
		# Load up the plugins specified
		plugins = self.conf_plugins.options("plugins")
		self.logger.info("Loading %i plugins..." % len(plugins))
		load_plugins(plugins)
		# Open the chat log, ready for appending
		create_if_not("logs/server.log")
		create_if_not("logs/chat.log")
		create_if_not("data/balances.sql")
		self.chatlog = open("logs/server.log", "a")
		self.chatlog = open("logs/chat.log", "a")
		self.balancesqllog = open("data/balances.sql", "a")

		# Create a default world, if there isn't one.
		if not os.path.isdir("mapdata/worlds/main"):
			self.logger.info("Generating main world...")
			sx, sy, sz = 64, 64, 64
			grass_to = (sy // 2)
			world = World.create(
				"mapdata/worlds/main",
				sx, sy, sz, # Size
				sx//2,grass_to+2, sz//2, 0, # Spawn
				([BLOCK_DIRT]*(grass_to-1) + [BLOCK_GRASS] + [BLOCK_AIR]*(sy-grass_to)) # Levels
			)
			self.logger.info("Generated.")
		# Load up the contents of data.
		self.loadMeta()
		# Set up a few more things.
		self.queue = Queue()
		self.clients = {}
		self.usernames = {}
		# Boot worlds that got loaded
		for world in self.worlds:
			self.loadWorld("mapdata/worlds/%s" % world, world)

	def initLoops(self):
		"""Initialize server loops to run during execution."""
		self.console = StdinPlugin(self)
		self.console.start()
		reactor.callLater(0.1, self.sendMessages)
		self.loops["printinfo"] = task.LoopingCall(self.printInfo)
		self.loops["printinfo"].start(60)
		if self.use_blockbeat or self.send_heartbeat:
			self.heartbeat = Heartbeat(self)
		if self.use_irc:
			self.irc_relay = ChatBotFactory(self)
			reactor.connectTCP(self.conf_irc.get("irc", "server"), self.conf_irc.getint("irc", "port"), self.irc_relay)
		else:
			self.irc_relay = None
		# Initial startup is instant, but it updates every 10 minutes.
		self.world_save_stack = []
		reactor.callLater(60, self.saveWorlds)
		if self.enable_archives:
			if "archives" not in protocol_plugins:
				self.loadPlugin("archives")
			#self.loops["loadarchives"] = task.LoopingCall(self.loadArchives)
			#self.loops["loadarchives"].start(60)
			reactor.callLater(60, self.loadArchives)
		gc.disable()
		self.loops["gc"] = task.LoopingCall(self.cleanGarbage)
		self.loops["gc"].start(900)
#		if self.backup_auto:
#			self.loops["autobackup"] = task.LoopingCall(self.AutoBackup)
#			self.loops["autobackup"].start(float(self.backup_freq * 60))

	def cleanGarbage(self, slient=False):
		"""Garbage cleaning."""
		count = gc.collect()
		if not slient:
			self.logger.info("%i garbage objects collected, %i were uncollected." % (count, len(gc.garbage)))
		#reactor.callLater(900, self.cleanGarbage)

	def loadMeta(self):
		"""Loads the 'meta' - variables that change with the server (worlds, admins, etc.)"""
		config = ConfigParser()
		config.read("data/server.meta")
		specs = ConfigParser()
		specs.read("data/spectators.meta")
		# Read in the worlds
		if config.has_section("worlds"):
			for name in config.options("worlds"):
				self.worlds[name] = None
				if name is "main":
					self.main_loaded = True
		else:
			self.worlds["main"] = None
		if not self.main_loaded:
			self.worlds["main"] = None
		# Read in the directors
		if config.has_section("directors"):
			for name in config.options("directors"):
				self.directors.add(name)
		# Read in the admins
		if config.has_section("admins"):
			for name in config.options("admins"):
				self.admins.add(name)
		# Read in the mods
		if config.has_section("mods"):
			for name in config.options("mods"):
				self.mods.add(name)
		# Read in the advanced builders
		if config.has_section("advbuilders"):
			for name in config.options("advbuilders"):
				self.advbuilders.add(name)
		if config.has_section("silenced"):
			for name in config.options("silenced"):
				self.silenced.add(name)
		# Read in the spectators
		if specs.has_section("spectators"):
			for name in specs.options("spectators"):
				self.spectators.add(name)
		# Read in the bans
		if config.has_section("banned"):
			for name in config.options("banned"):
				self.banned[name] = config.get("banned", name)
		# Read in the ipbans
		if config.has_section("ipbanned"):
			for ip in config.options("ipbanned"):
				self.ipbanned[ip] = config.get("ipbanned", ip)

	def saveMeta(self):
		"""Saves the server's meta back to a file."""
		config = ConfigParser()
		specs = ConfigParser()
		# Make the sections
		config.add_section("worlds")
		config.add_section("directors")
		config.add_section("admins")
		config.add_section("mods")
		config.add_section("advbuilders")
		config.add_section("silenced")
		config.add_section("banned")
		config.add_section("ipbanned")
		specs.add_section("spectators")
		# Write out things
		for world in self.worlds:
			config.set("worlds", world, "true")
		for director in self.directors:
			config.set("directors", director, "true")
		for admin in self.admins:
			config.set("admins", admin, "true")
		for mod in self.mods:
			config.set("mods", mod, "true")
		for advbuilder in self.advbuilders:
			config.set("advbuilders", advbuilder, "true")
		for ban, reason in self.banned.items():
			config.set("banned", ban, reason)
		for spectator in self.spectators:
			specs.set("spectators", spectator, "true")
		for silence in self.silenced:
			config.set("silenced", silence, "true")
		for ipban, reason in self.ipbanned.items():
			config.set("ipbanned", ipban, reason)
		fp = open("data/server.meta", "w")
		config.write(fp)
		fp.close()
		fp = open("data/spectators.meta", "w")
		specs.write(fp)
		fp.close()

	def printInfo(self):
		"""Prints console info every minute, and performs other utility actions."""
		if self.console_delay == self.delay_count:
			if not len(self.clients) == 0:
				self.logger.info("There are %s players on the server" % len(self.clients))
				for key in self.worlds:
					self.logger.info("%s: %s" % (key, ", ".join(str(c.username) for c in self.worlds[key].clients)))
			self.delay_count = 1
		else:
			self.delay_count += 1
		gc.collect()
		if (time.time() - self.last_heartbeat) > 180 and (self.use_blockbeat or self.send_heartbeat):
			self.heartbeat = None
			self.heartbeat = Heartbeat(self)

	def loadArchive(self, filename):
		"""Boots an archive given a filename. Returns the new world ID."""
		# Get an unused world name
		i = 1
		while self.world_exists("a-%i" % i):
			i += 1
		world_id = "a-%i" % i
		# Copy and boot
		self.newWorld(world_id, "mapdata/archives/%s" % filename)
		self.loadWorld("mapdata/worlds/%s" % world_id, world_id)
		world = self.worlds[world_id]
		world.is_archive = True
		return world_id

	def saveWorlds(self):
		"""Saves the worlds, one at a time, with a 1 second delay."""
		if not self.saving:
			if not self.world_save_stack:
				self.world_save_stack = list(self.worlds)
			key = self.world_save_stack.pop()
			self.saveWorld(key)
			if not self.world_save_stack:
				reactor.callLater(60, self.saveWorlds)
				self.saveMeta()
			else:
				reactor.callLater(1, self.saveWorlds)

	def saveWorld(self, world_id, shutdown=False):
		"""Save the world, and flush it on disk."""
		try:
			world = self.worlds[world_id]
			world.save_meta()
			world.flush()
			if self.console_delay == self.delay_count:
				self.logger.info("World '%s' has been saved." % world_id)
			if self.save_count == 5:
				for client in list(list(self.worlds[world_id].clients))[:]:
					client.sendServerMessage("World '%s' has been saved." % world_id)
				self.save_count = 1
			else:
				self.save_count += 1
			if shutdown: del self.worlds[world_id]
		except:
			self.logger.error("Error saving world %s" % world_id)

	def claimId(self, client):
		"""Claims an empty player ID, and store it in the clients table."""
		for i in range(1, self.max_clients+1):
			if i not in self.clients:
				self.clients[i] = client
				return i
		# Max client reached, return server full message
		raise ServerFull

	def releaseId(self, id):
		"""Releases player ID from the clients table."""
		del self.clients[id]

	def joinWorld(self, worldid, user):
		"""Makes the player join the given world."""
		new_world = self.worlds[worldid]
		try:
			self.logger.info("%s is joining world %s" % (user.username, new_world.basename))
		except:
			self.logger.info("%s is joining world %s" % (user.transport.getPeer().host, new_world.basename))
		if hasattr(user, "world") and user.world:
			self.leaveWorld(user.world, user)
		user.world = new_world
		new_world.clients.add(user)
		if not worldid == "main" and not new_world.ASD == None:
			new_world.ASD.kill()
			new_world.ASD = None
		return new_world

	def leaveWorld(self, world, user):
		"""Leaves the current world."""
		world.clients.remove(user)
		if world.autoshutdown and len(world.clients) < 1:
			if world.basename == ("mapdata/worlds/main"): # Can't leave main
				return
			else:
				if not self.asd_delay == 0:
					world.ASD = self.timers["asd"] = ResettableTimer(self.asd_delay*60,1,world.unload)
					world.ASD.start()

	def loadWorld(self, filename, world_id):
		"""
		Loads the given world file under the given world ID, or a random one.
		Returns the ID of the new world.
		"""
		world = self.worlds[world_id] = World(filename)
		world.source = filename
		world.clients = set()
		world.id = world_id
		world.factory = self
		world.start()
		self.logger.info("World '%s' Booted." % world_id)
		return world_id

	def unloadWorld(self, world_id, ASD=False):
		"""Unloads the given world ID."""
		try:
			if ASD and len(self.worlds[world_id].clients) > 0:
				try:
					self.worlds[world_id].ASD.kill()
					self.worlds[world_id].ASD = None
					return
				except TypeError:
					return
		except KeyError:
			return
		try:
			assert world_id != "main"
		except:
			if not client.console:
				client.sendServerMessage("You can't shut down main.")
			else:
				self.logger.warning("You can't shut down main.")
		if not self.worlds[world_id].ASD == None:
			self.worlds[world_id].ASD.kill()
			self.worlds[world_id].ASD = None
		for client in list(list(self.worlds[world_id].clients))[:]:
			client.changeToWorld("main")
			client.sendServerMessage("World '%s' has been shut down." % world_id)
		self.worlds[world_id].stop()
		self.saveWorld(world_id, True)
		self.logger.info("World '%s' has been shut down." % world_id)

	def rebootWorld(self, world_id):
		"""Reboots a world in a crash case."""
		for client in list(list(self.worlds[world_id].clients))[:]:
			if world_id == "main":
				client.changeToWorld(self.factory.main_backup)
			else:
				client.changeToWorld("main")
			client.sendServerMessage("%s has been rebooted." % world_id)
		self.worlds[world_id].stop()
		self.worlds[world_id].flush()
		self.worlds[world_id].save_meta()
		del self.worlds[world_id]
		world = self.worlds[world_id] = World("mapdata/worlds/%s" % world_id, world_id)
		world.source = "mapdata/worlds/" + world_id
		world.clients = set()
		world.id = world_id
		world.factory = self
		world.start()
		self.logger.info("Rebooted world %s." % world_id)

	def publicWorlds(self):
		"""
		Returns the IDs of all public worlds
		"""
		for world_id, world in self.worlds.items():
			if not world.private:
				yield world_id

	def recordPresence(self, username):
		"""Records a sighting of 'username' in the user's persistence file."""
		with Persist(username) as p:
			p.set("main", "lastseen", time.time())

	def unloadPlugin(self, plugin_name):
		"""Reloads the plugin with the given module name."""
		# Unload the plugin from everywhere
		for plugin in plugins_by_module_name(plugin_name):
			if issubclass(plugin, ProtocolPlugin):
				for client in self.clients.values():
					client.unloadPlugin(plugin)
		# Unload it
		unload_plugin(plugin_name)

	def loadPlugin(self, plugin_name):
		"""Loads a plugin."""
		# Load it
		load_plugin(plugin_name)
		# Load it back into clients etc.
		for plugin in plugins_by_module_name(plugin_name):
			if issubclass(plugin, ProtocolPlugin):
				for client in self.clients.values():
					client.loadPlugin(plugin)

	def sendMessages(self):
		"""Sends all queued messages, and lets worlds recieve theirs."""
		try:
			while True:
				# Get the next task
				source_client, task, data = self.queue.get_nowait()
				if source_client == None:
					# Client is None
					pass
				try:
					if isinstance(source_client, World):
						world = source_client
					elif str(source_client).startswith("<StdinPlugin"):
						world = self.worlds["main"]
					else:
						try:
							world = source_client.world
						except AttributeError:
							if not source_client.connected or self.console:
								continue
							else:
								self.logger.warning("Source client for message has no world. Ignoring.")
								continue
					# Someone built/deleted a block
					if task is TASK_BLOCKSET:
						# Only run it for clients who weren't the source.
						for client in world.clients:
							if client is not source_client:
								client.sendBlock(*data)
					# Someone moved
					elif task is TASK_PLAYERPOS:
						# Only run it for clients who weren't the source.
						for client in world.clients:
							if client != source_client:
								client.sendPlayerPos(*data)
					# Someone moved only their direction
					elif task is TASK_PLAYERDIR:
						# Only run it for clients who weren't the source.
						for client in world.clients:
							if client != source_client:
								client.sendPlayerDir(*data)
					# Someone spoke!
					elif task is TASK_MESSAGE:
						#LOL MOAR WORD FILTER
						id, colour, username, text = data
						text = self.messagestrip(text)
						data = (id, colour, username, text)
						for client in self.clients.values():
							if not client.console:
								if client.world.global_chat or client.world is source_client.world:
									client.sendMessage(*data)
						self.logger.info("%s: %s" % (username, text))
						self.chatlog.write("%s - %s: %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, text))
						self.chatlog.flush()
						if self.irc_relay and world:
							self.irc_relay.sendMessage(username, text)
					# Someone spoke!
					elif task is TASK_IRCMESSAGE:
						# Word Filter
						id, colour, username, text = data
						text = self.messagestrip(text)
						data = (id, colour, username, text)
						for client in self.clients.values():
							client.sendIrcMessage(*data)
						self.logger.info("<%s> %s" % (username, text))
						self.chatlog.write("[%s] <%s> %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, text))
						self.chatlog.flush()
						if self.irc_relay and world:
							self.irc_relay.sendMessage(username, text)
					# Someone actioned!
					elif task is TASK_ACTION:
						# Word Filter
						id, colour, username, text = data
						text = self.messagestrip(text)
						data = (id, colour, username, text)
						for client in self.clients.values():
							client.sendAction(*data)
						id, colour, username, text = data
						self.logger.info("ACTION - *%s %s" % (username, text))
						self.chatlog.write("%s *%s %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, text))
						self.chatlog.flush()
						if self.irc_relay and world:
							self.irc_relay.sendAction(username, text)
					# Someone connected to the server
					elif task is TASK_PLAYERCONNECT:
						for client in self.usernames:
							self.usernames[client].sendNewPlayer(*data)
							self.usernames[client].sendServerMessage("%s has come online." % source_client.username)
						if self.irc_relay and world:
							self.irc_relay.sendServerMessage("%s has come online." % source_client.username)
					# Someone joined a world!
					elif task is TASK_NEWPLAYER:
						for client in world.clients:
							if client != source_client:
								client.sendNewPlayer(*data)
							client.sendServerMessage("%s has joined the map." % source_client.username)
					# Someone left!
					elif task is TASK_PLAYERLEAVE:
						# Only run it for clients who weren't the source.
						for client in self.clients.values():
							client.sendPlayerLeave(*data)
							if not source_client.username is None:
								client.sendServerMessage("%s has quit! (%s%s%s)" % (source_client.username, COLOUR_RED, source_client.quitmsg, COLOUR_YELLOW))
							else:
								source_client.logger.info("Pinged the server.")
						if not source_client.username is None:
							if self.irc_relay and world:
								self.irc_relay.sendServerMessage("%s has quit! (%s%s%s)" % (source_client.username, COLOUR_RED, source_client.quitmsg, COLOUR_BLACK))
						self.logger.info("%s has quit! (%s)" % (source_client.username, source_client.quitmsg))
					# Someone changed worlds!
					elif task is TASK_WORLDCHANGE:
						# Only run it for clients who weren't the source.
						for client in data[1].clients:
							client.sendPlayerLeave(data[0])
							client.sendServerMessage("%s joined '%s'" % (source_client.username, world.id))
						if self.irc_relay and world:
							self.irc_relay.sendServerMessage("%s joined '%s'" % (source_client.username, world.id))
						self.logger.info("%s has now joined '%s'" % (source_client.username, world.id))
					elif task == TASK_STAFFMESSAGE:
						# Give all staff the message
						id, colour, username, text = data
						message = self.messagestrip(text)
						for user, client in self.usernames.items():
							if self.isMod(user):
								client.sendMessage(100, COLOUR_YELLOW+"#"+colour, username, message, False, False)
						if self.irc_relay and len(data) > 3:
							self.irc_relay.sendServerMessage("#"+username+": "+text,True,username)
						self.logger.info("#"+username+": "+text)
						self.adlog = open("logs/server.log", "a")
						self.adlog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" - "+username+": "+text+"\n")
						self.adlog.flush()
					elif task == TASK_GLOBALMESSAGE:
						# Give all world people the message
						id, world, message = data
						message = self.messagestrip(message);
						for client in world.clients:
							client.sendNormalMessage(message)
					elif task == TASK_WORLDMESSAGE:
						# Give all world people the message
						id, world, message = data
						for client in world.clients:
							client.sendNormalMessage(message)
					elif task == TASK_SERVERMESSAGE:
						# Give all people the message
						message = data
						message = self.messagestrip(message)
						for client in self.clients.values():
							client.sendNormalMessage(COLOUR_DARKBLUE + message)
						self.logger.info(message)
						if self.irc_relay and world:
							self.irc_relay.sendServerMessage(message)
					elif task == TASK_ONMESSAGE:
						# Give all people the message
						id, world, text = data
						message = self.messagestrip(text)
						for client in self.clients.values():
							client.sendNormalMessage(COLOUR_YELLOW + message)
						if self.irc_relay and world:
							self.irc_relay.sendServerMessage(message)
					elif task == TASK_ADMINMESSAGE:
						# Give all people the message
						id, world, text = data
						message = self.messagestrip(text)
						for client in self.clients.values():
							client.sendNormalMessage(COLOUR_YELLOW + message)
						if self.irc_relay and world:
							self.irc_relay.sendServerMessage(message)
					elif task == TASK_PLAYERRESPAWN:
						# We need to immediately respawn the player to update their nick.
						for client in world.clients:
							if client != source_client:
								id, username, x, y, z, h, p = data
								client.sendPlayerLeave(id)
								client.sendNewPlayer(id, username, x, y, z, h, p)
					elif task == TASK_SERVERURGENTMESSAGE:
						# Give all people the message
						id, colour, username, text = data
						message = self.messagestrip(text)
						message = self.messagestrip(message)
						for client in self.clients.values():
							client.sendNormalMessage(COLOUR_DARKRED + message)
						self.logger.info(message)
						if self.irc_relay and world:
							self.irc_relay.sendServerMessage(message)
					elif task == TASK_AWAYMESSAGE:
						# Give all world people the message
						id, colour, username, text = data
						message = self.messagestrip(text)
						data = (id, colour, username, text)
						for client in world.clients:
							client.sendNormalMessage(COLOUR_DARKPURPLE + message)
						self.logger.info("AWAY - %s %s" % (username, text))
						self.chatlog.write("%s %s %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, text))
						self.chatlog.flush()
						if self.irc_relay and world:
							self.irc_relay.sendAction(username, text)
				except Exception, e:
					self.logger.error(traceback.format_exc())
		except Empty:
			pass
		# OK, now, for every world, let them read their queues
		for world in self.worlds.values():
			world.read_queue()
		# Come back soon!
		reactor.callLater(0.1, self.sendMessages)

	def newWorld(self, new_name, template="default"):
		"""Creates a new world from some template."""
		# Make the directory
		os.mkdir("mapdata/worlds/%s" % new_name)
		# Find the template files, copy them to the new location
		for filename in ["blocks.gz", "world.meta"]:
				response = shutil.copyfile("mapdata/templates/%s/%s" % (template, filename), "mapdata/worlds/%s/%s" % (new_name, filename))
				return response

	def renameWorld(self, old_worldid, new_worldid):
		"Renames a world."
		assert old_worldid not in self.worlds
		assert self.world_exists(old_worldid)
		assert not self.world_exists(new_worldid)
		os.rename("mapdata/worlds/%s" % (old_worldid), "mapdata/worlds/%s" % (new_worldid))

	def numberWithPhysics(self):
		"Returns the number of worlds with physics enabled."
		return len([world for world in self.worlds.values() if world.physics])

	def userColour(self, user):
		"Returns the colour of the user. Global ranks only."
		if user is self.owner:
			color = COLOUR_DARKGREEN
		if user in self.spectators:
			color = COLOUR_BLACK
		elif user in self.directors:
			color = COLOUR_GREEN
		elif user in self.admins:
			color = COLOUR_RED
		elif user in self.mods:
			color = COLOUR_BLUE
		elif user in VIPS:
			color = COLOUR_YELLOW
		elif user in self.advbuilders:
			color = COLOUR_GREY
		else:
			color = COLOUR_WHITE
		return color

	def isSilenced(self, username):
		return username.lower() in self.silenced

	def isOwner(self, username):
		return username.lower()==self.owner

	def isDirector(self, username):
		return username.lower() in self.directors or self.isOwner(username)

	def isAdmin(self, username):
		return username.lower() in self.admins or self.isDirector(username)

	def isMod(self, username):
		return username.lower() in self.mods or self.isAdmin(username)

	def isAdvBuilder(self, username):
		return username.lower() in self.advbuilders or self.isMod(username)

	def isSpectator(self, username):
		return username.lower() in self.spectators

	def isBanned(self, username):
		return username.lower() in self.banned

	def isIpBanned(self, ip):
		return ip in self.ipbanned

	def addBan(self, username, reason):
		self.banned[username.lower()] = reason

	def removeBan(self, username):
		del self.banned[username.lower()]

	def banReason(self, username):
		return self.banned[username.lower()]

	def addIpBan(self, ip, reason):
		self.ipbanned[ip] = reason

	def removeIpBan(self, ip):
		del self.ipbanned[ip]

	def ipBanReason(self, ip):
		return self.ipbanned[ip]

	def world_exists(self, world_id):
		"Says if the world exists (even if unbooted)"
		return os.path.isdir("mapdata/worlds/%s/" % world_id)

	def AutoBackup(self):
		for world in self.worlds:
			self.Backup(world, "server")
		if self.backup_auto:
			reactor.callLater(float(self.backup_freq * 60), self.AutoBackup)

	def Backup(self, world_id, fromloc, backupname=None):
		error = None
		world_dir = ("mapdata/worlds/%s/" % world_id)
		if world_id == "main" and not self.backup_main and not (fromloc == "user" or fromloc == "console"): # This is to ensure manual backup still works
			return
		if not os.path.exists(world_dir):
			if fromloc == "console":
				self.logger.error("World %s does not exist." % (world_id))
			elif fromloc == "server":
				self.logger.warning("AutoBackup tried to backup world %s which does not exist." % (world_id))
			elif fromloc == "user":
				error = ("ERROR_WORLD_DOES_NOT_EXIST_%s" % world_id)
				return error
			return
		else:
			if not os.path.exists(world_dir + "backup/"):
				os.mkdir(world_dir + "backup/")
			folders = os.listdir(world_dir + "backup/")
			if backupname is not None:
				path = os.path.join(world_dir + "backup/", backupname)
				if os.path.exists(path):
					if fromloc == "console":
						self.logger.error("Backup %s already exists." % (backupname))
					elif fromloc == "server":
						# Should never reach here
						self.logger.warning("AutoBackup error, please contact the blockBox team.")
					elif fromloc == "user":
						error = ("ERROR_BACKUP_ALREADY_EXISTS_%s" % (backupname))
						return error
					return
			else:
				backups = list([])
				for x in folders:
					if x.isdigit():
						backups.append(x)
				backups.sort(lambda x, y: int(x) - int(y))
				path = os.path.join(world_dir + "backup/", "0")
				if backups:
					path = os.path.join(world_dir + "backup/", str(int(backups[-1])+1))
			try:
				os.mkdir(path)
				shutil.copy(world_dir + "blocks.gz", path)
				shutil.copy(world_dir + "world.meta", path)
			except:
				if backupname is not None:
					if fromloc == "console":
						self.logger.error("Unable to save backup %s of world %s" % (backupname, world_id))
					elif fromloc == "console":
						self.logger.error("Unable to save backup %s of world %s" % (backupname, world_id))
					elif fromloc == "user":
						error = ("ERROR_UNABLE_TO_SAVE_BACKUP_%s" % (backupname))
						return error
				else:
					if fromloc == "console":
						self.logger.error("Unable to save backup %s of world %s" % (str(int(backups[-1])+1)), world_id)
					elif fromloc == "server":
						self.logger.error("Unable to save backup %s of world %s" % (str(int(backups[-1])+1)), world_id)
					elif fromloc == "user":
						error = ("ERROR_UNABLE_TO_SAVE_BACKUP_%s" % (backup))
						return error
			if backupname is not None:
				if fromloc == "console":
					self.logger.error("Unable to save backup %s of world %s" % (backupname, world_id))
				elif fromloc == "server":
					self.logger.error("Unable to save backup %s of world %s" % (backupname, world_id))
				elif fromloc == "user":
					error = ("ERROR_UNABLE_TO_SAVE_BACKUP_%s" % (backupname))
					return error
			else:
				try:
					if fromloc == "console":
						self.logger.info("%s's backup %s is saved." %(world_id, str(int(backups[-1])+1)))
					elif fromloc == "server":
						self.logger.debug("%s's backup %s is saved." %(world_id, str(int(backups[-1])+1)))
					elif fromloc == "user":
						error = str(int(backups[-1])+1)
				except:
					if fromloc == "console":
						self.logger.info("%s's backup 0 is saved." % (world_id))
					elif fromloc == "server":
						self.logger.debug("%s's backup 0 is saved." %(world_id))
					elif fromloc == "user":
						error = 0
			if self.backup_max > 0:
				if len(backups)+1 > self.backup_max:
					for i in range(0,((len(backups)+1)-self.backup_max)):
						shutil.rmtree(os.path.join(world_dir+"backup/", str(int(backups[i]))))
			if error is not None:
				return error

	def messagestrip(self, message):
		strippedmessage = ""
		for x in message:
			if ord(str(x)) < 128:
				strippedmessage = strippedmessage + str(x)
		message = strippedmessage
		for x in self.filter:
			rep = re.compile(x[0], re.IGNORECASE)
			message = rep.sub(x[1], message)
		return message

	def loadArchives(self):
		self.archives = {}
		for name in os.listdir("mapdata/archives/"):
			if os.path.isdir(os.path.join("mapdata/archives", name)):
				for subfilename in os.listdir(os.path.join("mapdata/archives", name)):
					match = re.match(r'^(\d\d\d\d\-\d\d\-\d\d_\d?\d\_\d\d)$', subfilename)
					if match:
						when = match.groups()[0]
						try:
							when = datetime.datetime.strptime(when, "%Y-%m-%d_%H_%M")
						except ValueError, e:
							self.logger.warning("Bad archive filename %s" % subfilename)
							continue
						if name not in self.archives:
							self.archives[name] = {}
						self.archives[name][when] = "%s/%s" % (name, subfilename)
		self.logger.info("Loaded %s discrete archives." % len(self.archives))
		reactor.callLater(60, self.loadArchives)

	def reloadOptions(self, toReload="all"):
		self.reloading = True
		followup = set()
		loopsToReset = dict()
		timersToReset = set()
		if toReload == "max_clients" or toReload == "info" or toReload == "all":
			self.max_clients = self.config.getint("main", "max_clients")
			if "heartbeat" not in followup:
				followup.add("heartbeat")
		if toReload == "server_name" or toReload == "info" or toReload == "all":
			self.server_name = self.config.get("main", "name")
			if "heartbeat" not in followup:
				followup.add("heartbeat")
		if toReload == "server_message" or toReload == "info" or toReload == "all":
			self.server_message = self.config.get("main", "description")
			if "heartbeat" not in followup:
				followup.add("heartbeat")
		if toReload == "initial_greeting" or toReload == "info" or toReload == "all":
			self.initial_greeting = self.config.get("main", "greeting").replace("\\n", "\n")
		if toReload == "public" or toReload == "info" or toReload == "all":
			self.public = self.config.getboolean("main", "public")
			if "heartbeat" not in followup:
				followup.add("heartbeat")
		if toReload == "enable_archives" or toReload == "worlds" or toReload == "all":
			self.enable_archives = self.conf_options.getboolean("worlds", "enable_archives")
		if toReload == "asd_delay" or toReload == "worlds" or toReload == "all":
			self.asd_delay = self.conf_options.getint("worlds", "asd_delay")
			if "resetloop" not in followup:
				followup.add("resetloop")
			loopsToReset["asd"] = self.asd_delay
			if "resetimer" not in followup:
				followup.add("resettimer")
			timersToReset.add("asd")
		if toReload == "physics_limit" or toReload == "worlds" or toReload == "all":
			self.physics_limit = self.conf_options.getint("worlds", "physics_limit")
		if toReload == "main_backup" or toReload == "worlds" or toReload == "all":
			self.main_backup = self.conf_options.get("worlds", "main_backup")
		if toReload == "duplicate_logins" or toReload == "players" or toReload == "all":
			self.duplicate_logins = self.config.getboolean("options", "duplicate_logins")
		if toReload == "verify_names" or toReload == "players" or toReload == "all":
			self.verify_names = self.config.getboolean("options", "verify_names")
		if toReload == "api_password" or toReload == "api" or toReload == "all":
			self.api_password = self.config.get("network", "api_password")
		if toReload == "console_delay" or toReload == "api" or toReload == "all":
			self.console_delay = self.config.getint("options", "console_delay")
			if "resetloop" not in followup:
				followup.add("resetloop")
			loopsToReset["printinfo"] = self.console_delay
		if toReload == "info_url" or toReload == "info" or toReload == "all":
			self.info_url = self.config.get("info", "info_url")
		if toReload == "credit_name" or toReload == "players" or toReload == "all":
			self.credit_name = self.conf_options.get("bank", "credit_name")
		if toReload == "initial_amount" or toReload == "players" or toReload == "all":
			self.initial_amount = self.conf_options.get("bank", "initial_amount")
		if toReload == "backup_freq" or toReload == "backup" or toReload == "all":
			self.backup_freq = self.conf_options.getint("backup", "backup_freq")
			if "resetloop" not in followup:
				followup.add("resetloop")
			if "autobackup" not in loopsToReset:
				loopsToReset["autobackup"] = self.backup_freq
		if toReload == "backup_main" or toReload == "backup" or toReload == "all":
			self.backup_main = self.conf_options.getboolean("backup", "backup_main")
		if toReload == "backup_max" or toReload == "backup" or toReload == "all":
			self.backup_max = self.conf_options.getint("backup", "backup_max")
		if toReload == "backup_auto" or toReload == "backup" or toReload == "all":
			self.backup_auto = self.conf_options.getboolean("backup", "backup_auto")
			if self.backup_auto:
				if "resetloop" not in followup:
					followup.add("resetloop")
				if "autobackup" not in loopsToReset:
					loopsToReset["autobackup"] = self.backup_freq
		if toReload == "useblblimit" or toReload == "blb" or toReload == "all":
			self.useblblimit = self.conf_options.getboolean("blb", "use_blb_limiter")
			if self.useblblimit:
				self.blblimit["player"] = self.conf_options.getint("blb", "player")
				self.blblimit["builder"] = self.conf_options.getint("blb", "builder")
				self.blblimit["advbuilder"] = self.conf_options.getint("blb", "advbuilder")
				self.blblimit["op"] = self.conf_options.getint("blb", "op")
				self.blblimit["worldowner"] = self.conf_options.getint("blb", "worldowner")
				self.blblimit["mod"] = self.conf_options.getint("blb", "mod")
				self.blblimit["admin"] = self.conf_options.getint("blb", "admin")
				self.blblimit["director"] = self.conf_options.getint("blb", "director")
				self.blblimit["owner"] = self.conf_options.getint("blb", "owner")
		if toReload == "blblimit" or toReload == "blb" or toReload == "all":
				self.blblimit["player"] = self.conf_options.getint("blb", "player")
				self.blblimit["builder"] = self.conf_options.getint("blb", "builder")
				self.blblimit["advbuilder"] = self.conf_options.getint("blb", "advbuilder")
				self.blblimit["op"] = self.conf_options.getint("blb", "op")
				self.blblimit["worldowner"] = self.conf_options.getint("blb", "worldowner")
				self.blblimit["mod"] = self.conf_options.getint("blb", "mod")
				self.blblimit["admin"] = self.conf_options.getint("blb", "admin")
				self.blblimit["director"] = self.conf_options.getint("blb", "director")
				self.blblimit["owner"] = self.conf_options.getint("blb", "owner")
		for todo in followup:
			if todo == "heartbeat":
				# Resend heartbeat
				self.Heartbeat.get_url()
			elif todo == "resetloop":
				# Look in the loopsToReset set
				for toreset in loopsToReset:
					if toreset in self.loops:
						self.loops[toreset].stop()
						self.loops[toreset].start(loopsToReset[toreset])
			elif todo == "resettimer":
				for toreset in timersToReset:
					if toreset in self.timers:
						self.timers["_server"][toreset].reset()
