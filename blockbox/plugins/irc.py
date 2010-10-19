# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class IRCPlugin(ProtocolPlugin):
	
	commands = {
		"irc_cpr": "commandIRCReload",
		"ircrehash": "commandIRCReload",
		"ircreload": "commandIRCReload",
	}

	@admin_only
	def commandIRCReload(self, parts, fromloc, overriderank):
		"/ircrehash - Admin\nAliases: irc_cpr, ircreload\nRehashes the IRC Bot."
		self.client.factory.reloadIrcBot()
		self.client.sendServerMessage("Reloaded the IRC Bot.")
