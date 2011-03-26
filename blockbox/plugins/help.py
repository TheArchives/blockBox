# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.globals import *
from blockbox.plugins import ProtocolPlugin

class HelpPlugin(ProtocolPlugin):
	"Command that shows help and information of the server."

	commands = {
		"status": "commandStatus",
		"mapinfo": "commandStatus",
		"help": "commandHelp",
		"?": "commandHelp",
		"cmdlist": "commandCmdlist",
		"commands": "commandCmdlist",
		"about": "commandAbout",
		"credits": "commandCredits",
		"motd": "commandMOTD",
		"greeting": "commandMOTD",
	}

	@config("category", "info")
	def commandStatus(self, parts, fromloc, overriderank):
		"/status - Guest\nAliases: mapinfo\nReturns info about the current world"
		self.client.sendServerMessage("World: %s" % (self.client.world.id))
		self.client.sendServerMessage("Owner: %s" % self.client.world.owner)
		self.client.sendServerMessage("Size: %sx%sx%s" % (self.client.world.x, self.client.world.y, self.client.world.z))
		self.client.sendServerMessage("- " + \
			(self.client.world.all_write and "&4Unlocked" or "&2Locked") + "&e | " + \
			(self.client.world.zoned and "&2Zones" or "&4Zones") + "&e | " + \
			(self.client.world.private and "&2Private" or "&4Private") + "&e | " + \
			(self.client.world.global_chat and "&2GChat" or "&4GChat")
		)
		self.client.sendServerMessage("- " + \
			(self.client.world.highlight_ops and "&2Colors" or "&4Colors") + "&e | " + \
			(self.client.world.physics and "&2Physics" or "&4Physics") + "&e | " + \
			(self.client.world.finite_water and "&4FWater" or "&2FWater") + "&e | " + \
			(self.client.world.admin_blocks and "&2Solids" or "&4Solids")
		)
		if not self.client.world.ops:
			self.client.sendServerMessage("Ops: N/A")
		else:
			self.client.sendServerList(["Ops:"] + list(self.client.world.ops))
		if not self.client.world.writers:
			self.client.sendServerMessage("Builders: N/A")
		else:
			self.client.sendServerList(["Builders:"] + list(self.client.world.builders))

	@config("category", "info")
	def commandHelp(self, parts, fromloc, overriderank):
		"/help [document/command] - Guest\nHelp for this server and commands."
		if len(parts) > 1:
			try:
				func = self.client.commands[parts[1].lower()]
			except KeyError:
				if parts[1].lower() == "basics":
					self.client.sendServerMessage("The Basics")
					self.client.sendServerMessage("/worlds - Lists all worlds.")
					self.client.sendServerMessage("/l worldname - Takes you to another world.")
					self.client.sendServerMessage("/tp username - This takes you to someone else.")
					self.client.sendServerMessage("Step through portals to teleport around.")
				elif parts[1].lower() == "chat":
					self.client.sendServerMessage("The Chats")
					if self.client.isMod():
						self.client.sendServerMessage("Whispers: @username Whispers")	
						self.client.sendServerMessage("WorldChat: !message")
						self.client.sendServerMessage("StaffChat: #message")
					else:
						self.client.sendServerMessage("Whispers: @username Whispers")
						self.client.sendServerMessage("WorldChat: !message")
				elif parts[1].lower() == "physic":
					self.client.sendServerMessage("The Physic Engine")
					self.client.sendServerMessage("Turn physics on to use Physics (max of 5 worlds)")
					self.client.sendServerMessage("If fwater is on then your water won't move.")
					self.client.sendServerMessage("Orange blocks make Lavafalls, darkblue blocks make Waterfalls.")
					self.client.sendServerMessage("Spouts need fwater to be on in order to work.")
					self.client.sendServerMessage("Sand will fall, grass will grow, sponges will absorb.")
					self.client.sendServerMessage("Use unflood to move all water, lava, and spouts from the map.")
				elif parts[1].lower() == "ranks":
					self.client.sendNormalMessage(COLOUR_YELLOW + "The Server Ranks - " + COLOUR_DARKGREEN + "Owner/Console (10/11) " + COLOUR_GREEN+ "Director (9) " + COLOUR_RED + "Admin (8) " + COLOUR_BLUE+"Mod (7) ")
					self.client.sendNormalMessage(COLOUR_PURPLE + "IRC " + COLOUR_DARKYELLOW + "World Owner (6) " + COLOUR_DARKCYAN + "Op (5) " + COLOUR_GREY + "Advanced Builder (4) " + COLOUR_CYAN + "Builder (3) " + COLOUR_WHITE + "Guest (2)")
					self.client.sendNormalMessage(COLOUR_BLACK + "Spectator (1) Banned(0)")
				elif parts[1].lower() == "cc":
					self.client.sendServerMessage("The Color Codes")
					self.client.sendNormalMessage("&a%a &b%b &c%c &d%d &e%e &f%f")
					self.client.sendNormalMessage("&0%0 &1%1 &2%2 &3%3 &4%4 &5%5 &6%6 &7%7 &8%8 &9%9")
				else:
					self.client.sendServerMessage("Unknown command '%s'" % parts[1])
			else:
				if func.__doc__:
					for line in func.__doc__.split("\n"):
						self.client.sendServerMessage(line)
				else:
					self.client.sendServerMessage("There's no help for that command.")
		else:
			self.client.sendServerMessage("Help Center")
			self.client.sendServerMessage("Documents: /help [basics|chat|ranks|physic|cc]")
			self.client.sendServerMessage("Commands: /cmdlist - Lookup: /help command")
			self.client.sendServerMessage("About: /about | Credits: /credits")

	@config("category", "info")
	def commandCmdlist(self, parts, fromloc, overriderank):
		"/cmdlist category - Guest\nThe command list of your rank, categories."
		if len(parts) > 1:
			if parts[1].lower() not in ["all", "build", "world", "player", "info", "other"]:
				self.client.sendServerMessage("Unknown cmdlist '%s'" % parts[1])
			else:
				self.ListCommands(parts[1].lower())
		else:
			self.client.sendServerMessage("The Command List - Use: /cmdlist category")
			self.client.sendServerMessage("Categories: all build world player info other")

	def ListCommands(self, list):
		self.client.sendServerMessage("%s Commands:" % list.title())
		commands = []
		for name, command in self.client.commands.items():
			try:
				config = getattr(command, "config")
			except AttributeError:
				config = recursive_default()
			if config["disabled"]:
				continue
			if not list == "other":
				if not list == "all":
					if not config["category"]:
						continue
				if config["rank"] == "owner" and not self.client.isOwner():
					continue
				if config["rank"] == "director" and not self.client.isDirector():
					continue
				if config["rank"] == "admin" and not self.client.isAdmin():
					continue
				if config["rank"] == "mod" and not self.client.isMod():
					continue
				if config["rank"] == "worldowner" and not self.client.isWorldOwner():
					continue
				if config["rank"] == "op" and not self.client.isOp():
					continue
				if config["rank"] == "advbuilder" and not self.client.isAdvBuilder():
					continue
				if config["rank"] == "builder" and not self.client.isBuilder():
					continue
			else:
				if config["category"]:
					continue
				if config["rank"] == "owner" and not self.client.isOwner():
					continue
				if config["rank"] == "director" and not self.client.isDirector():
					continue
				if config["rank"] == "admin" and not self.client.isAdmin():
					continue
				if config["rank"] == "mod" and not self.client.isMod():
					continue
				if config["rank"] == "worldowner" and not self.client.isWorldOwner():
					continue
				if config["rank"] == "op" and not self.client.isOp():
					continue
				if config["rank"] == "advbuilder" and not self.client.isAdvBuilder():
					continue
				if config["rank"] == "builder" and not self.client.isBuilder():
					continue
			commands.append(name)
		if commands:
			self.client.sendServerList(sorted(commands))
		else:
			self.client.sendServerMessage("None.")

	@config("category", "info")
	def commandAbout(self, parts, fromloc, overriderank):
		self.client.sendServerMessage("About The Server - blockBox %s" % VERSION)
		self.client.sendServerMessage("Name: "+self.client.factory.server_name)
		self.client.sendServerMessage("URL: "+self.client.factory.info_url)
		self.client.sendServerMessage("Owner: "+self.client.factory.owner)
		if self.client.factory.use_irc:
			self.client.sendServerMessage("IRC: "+self.client.factory.conf_irc.get("irc", "server")+" "+self.client.factory.irc_channel)

	@config("category", "info")
	def commandCredits(self, parts, fromloc, overriderank):
		"/credits - Guest\nCredits for the creators, devs and testers."
		self.client.sendServerMessage("The Credits")
		list = Credits()
		for each in list:
			self.client.sendSplitServerMessage(each)

	@config("category", "info")
	def commandMOTD(self, parts, fromloc, overriderank):
		"/motd - Guest\nAliases: greeting\nShows the greeting."
		self.client.sendServerMessage("MOTD for "+self.client.factory.server_name+":")
		for line in self.client.factory.initial_greeting.split("\n"):
			self.client.sendNormalMessage(line)