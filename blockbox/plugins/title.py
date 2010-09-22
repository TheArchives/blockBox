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
	def commandSetTitle(self, parts, byuser, overriderank):
		"/title username [title] - Director\nAliases: settitle\nGives or removes a title to username."
		with Persist(parts[1]) as p:
			if len(parts)==3:
				if len(parts[2])<6:
					p.set("misc", "title", parts[2])
					self.client.sendServerMessage("Added title.")
				else:
					self.client.sendServerMessage("A title must be 5 character or less")
			elif len(parts)==2:
				if p.string("misc", "title") is None:
					self.client.sendServerMessage("Syntax: /title username title")
					return False
				else:
					p.set("misc", "title", "")
					self.client.sendServerMessage("Removed title.")
			elif len(parts)>3:
				self.client.sendServerMessage("You may only set one word as a title.")
