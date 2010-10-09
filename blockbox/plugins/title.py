# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.persistence import PersistenceEngine as Persist
class TitlePlugin(ProtocolPlugin):
	
	commands = {
		"title":	 "commandSetTitle",
		"settitle":	 "commandSetTitle",
	}

	@player_list
	@director_only
	def commandSetTitle(self, parts, fromloc, overriderank):
		"/title username [title] - Director\nAliases: settitle\nGives or removes a title to username."
		with Persist(parts[1]) as p:
			if len(parts)==3:
				if len(parts[2])<6:
					p.set("main", "title", parts[2])
					self.client.sendServerMessage("Added title.")
				else:
					self.client.sendServerMessage("A title must be 5 character or less")
			elif len(parts)==2:
				if p.string("main", "title") is None:
					self.client.sendServerMessage("Syntax: /title username title")
					return False
				else:
					p.set("main", "title", "")
					self.client.sendServerMessage("Removed title.")
			elif len(parts)>3:
				self.client.sendServerMessage("You may only set one word as a title.")
