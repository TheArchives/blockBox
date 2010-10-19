# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from lib.twisted.internet import reactor

class IRCPlugin(ProtocolPlugin):
	
	commands = {
		"irc_cpr": "commandIRCReload",
	}

	@admin_only
	def commandIRCReload(self, parts, byuser, overriderank):
		"/irc_cpr - Admin\nRehashes the IRC Bot."
		self.client.factory.irc_relay = None
		self.client.factory.irc_relay = ChatBotFactory(self.server)
		reactor.connectTCP(self.client.factory.config.get("irc", "server"), self.client.factory.config.getint("irc", "port"), self.client.factory.irc_relay)
		self.client.sendServerMessage("IRC Bot reloaded.")
