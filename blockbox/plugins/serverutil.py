# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class ServerUtilPlugin(ProtocolPlugin):
	"Server Maintenance Tools and Commands."
	commands = {
		"srb": "commandSRB",
		"srs": "commandSRS",
		"u": "commandUrgent",
		"urgent": "commandUrgent",
		#"irc_cpr": "commandIRCReload",
		#"ircload": "commandIRCLoad",
		#"ircunload": "commandIRCUnload",
	}
	@director_only
	def commandSRB(self, parts, fromloc, overriderank):
		"/srb [reason] - Director\nPrints out a reboot message."
		if len(parts) == 1:
			self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, ("[Server Reboot] Be back in a few.")))
		else:
			self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, ("[Server Reboot] Be back in a few: "+(" ".join(parts[1:])))))

	@director_only
	def commandSRS(self, parts, fromloc, overriderank):
		"/srs [reason] - Director\nPrints out a shutdown message."
		if len(parts) == 1:
			self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, ("[Server Shutdown] See you later.")))
		else:
			self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, ("[Server Shutdown] See you later: "+(" ".join(parts[1:])))))

	@admin_only
	def commandUrgent(self, parts, fromloc, overriderank):
		"/u message - Admin\nAliases: urgent\nPrints out message in the server color."
		if len(parts) == 1:
			self.client.sendServerMessage("Please type a message.")
		else:
			self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, "[URGENT] "+(" ".join(parts[1:]))))

	@admin_only
	def commandIRCReload(self, parts, fromloc, overriderank):
		"/irc_cpr - Admin\nRehashes the IRC Bot."
		self.client.factory.irc_relay.disconnect()
		self.client.factory.irc_relay = None
		self.client.factory.irc_relay = ChatBotFactory(self.server)
		reactor.connectTCP(self.client.factory.conf_irc.get("irc", "server"), self.client.factory.conf_irc.getint("irc", "port"), self.client.factory.irc_relay)
		self.client.sendServerMessage("IRC Bot reloaded.")

	@admin_only
	def commandIRCLoad(self, parts, fromloc, overriderank):
		"/icr_load - Admin\nLoads the IRC bot."
		if self.irc_relay:
			self.client.factory.sendServerMessage("IRC Bot already loaded. If it failed please use /irc_cpr!")
			return
		self.client.factory.irc_relay = ChatBotFactory(self.server)
		reactor.connectTCP(self.client.factory.conf_irc.get("irc", "server"), self.client.factory.conf_irc.getint("irc", "port"), self.client.factory.irc_relay)
		self.client.sendServerMessage("IRC Bot loaded.")

	@director_only
	def commandIRCUnload(self, parts, fromloc, overriderank):
		"/irc_unload - Director\nUnloads the IRC bot."
		if not self.irc_relay:
			self.client.factory.sendServerMessage("IRC bot is not loaded.")
			return
		self.client.factory.irc_relay.disconnect()
		self.client.factory.irc_relay = None
		self.client.sendServerMessage("IRC Bot unloaded.")