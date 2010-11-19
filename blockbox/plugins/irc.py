# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class IRCPlugin(ProtocolPlugin):

	commands = {
		"irc_cpr": "commandIRCReload",
		"ircload": "commandIRCLoad",
		"ircunload": "commandIRCUnload",
	}

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