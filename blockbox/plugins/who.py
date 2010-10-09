# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import cPickle #Now using the MUCH faster, optimized cPickle
import logging
import time
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from blockbox.persistence import PersistenceEngine as Persist

class PlayersPlugin(ProtocolPlugin):
	
	commands = {
		"who": "commandWho",
		"whois": "commandWho",
		"players": "commandWho",
		"pinfo": "commandWho",
		"locate": "commandLocate",
		"find": "commandLocate",
		"lastseen": "commandLastseen",
		"quitmsg": "commandQuitMsg",
		"quit": "commandQuit",
	}

	@only_username_command
	def commandLastseen(self, username, fromloc, overriderank):
		"/lastseen username - Guest\nTells you when 'username' was last seen."
		#TOFIX: Lastseen
		if self.persist.string("main", "lastseen", -1):
			self.client.sendServerMessage("There are no records of %s." % username)
		else:
			t = time.time() - self.persist.string("main", "lastseen", -1)
			days = t // 86400
			hours = (t % 86400) // 3600
			mins = (t % 3600) // 60
			desc = "%id, %ih, %im" % (days, hours, mins)
			self.client.sendServerMessage("%s was last seen %s ago." % (username, desc))

	@username_command
	def commandLocate(self, user, fromloc, overriderank):
		"/locate username - Guest\nAliases: find\nTells you what world a user is in."
		self.client.sendServerMessage("%s is in %s" % (user.username, user.world.id))

	@player_list
	def commandWho(self, parts, fromloc, overriderank):
		"/who [username] - Guest\nAliases: pinfo, players, whois\nOnline players, or player lookup."
		if len(parts) < 2:
			self.client.sendServerMessage("Do '/who username' for more info.")
			self.client.sendServerList(["Players:"] + list(self.client.factory.usernames))
		else:
			user = parts[1].lower()
			with Persist(user) as p:
				if parts[1].lower() in self.client.factory.usernames:
					#Parts is an array, always, so we get the first item.
					username = self.client.factory.usernames[parts[1].lower()]
					if username.isOwner():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKGREEN+"Owner")
					elif username.isDirector():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREEN+"Director")
					elif username.isAdmin():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_RED+"Admin")
					elif username.isMod():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLUE+"Mod")
					elif username.isWorldOwner():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKPURPLE+"World Owner")
					elif username.isOp():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKCYAN+"Operator")
					elif username.isAdvBuilder():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREY+"Advanced Builder")
					elif username.isWriter():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_CYAN+"Builder")
					elif username.isSpectator():
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLACK+"Spec")
					else:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_WHITE+"Player")
					if self.client.isAdmin():
						self.client.sendServerMessage("IP: "+str(username.transport.getPeer().host))
					if username.gone == 1:
						self.client.sendServerMessage("Status: "+COLOUR_DARKPURPLE+"Away")
					elif username.gone == 0:
						self.client.sendServerMessage("Status: "+COLOUR_DARKGREEN+"Online")
					else:
						self.client.sendServerMessage("Status: "+COLOUR_DARKGREEN+"Online")
					self.client.sendServerMessage("World: %s" % (username.world.id))
					if user in bank:
						self.client.sendServerMessage("Balance: M%d." %(bank[user]))
					else:
						self.client.sendServerMessage("Balance: N/A")
				else:
					#Parts is an array, always, so we get the first item.
					username = parts[1].lower()
					if username in self.client.factory.spectators:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLACK+"Spec")
					elif username in self.client.factory.owner:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKGREEN+"Owner")
					elif username in self.client.factory.directors:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREEN+"Director")
					elif username in self.client.factory.admins:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_RED+"Admin")
					elif username in self.client.factory.mods:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLUE+"Mod")
					elif username in self.client.world.owner:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKPURPLE+"World Owner")
					elif username in self.client.world.ops:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKCYAN+"Operator")
					elif username in self.client.factory.advbuilders:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREY+"Advanced Builder")
					elif username in self.client.world.writers:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_CYAN+"Builder")
					else:
						self.client.sendServerMessage(parts[1]+" - "+COLOUR_WHITE+"Guest")
					if self.client.isAdmin():
						self.client.sendServerMessage("IP: "+p.string("main", "ip", "None recorded."))
					self.client.sendServerMessage("Status: "+COLOUR_DARKRED+"Offline")
					if username not in self.client.factory.lastseen:
						self.client.sendServerMessage("Last Seen: N/A")
					else:
						t = time.time() - self.client.factory.lastseen[username]
						days = t // 86400
						hours = (t % 86400) // 3600
						mins = (t % 3600) // 60
						desc = "%id, %ih, %im" % (days, hours, mins)
						self.client.sendServerMessage("Last Seen: %s ago." % (desc))
						#self.commandLastseen(parts, fromloc, overriderank)
					if p.int("bank", "balance", -1) is not -1:
						self.client.sendServerMessage("Balance: C%d." %(p.int("bank", "balance", 0)))
					else:
						self.client.sendServerMessage("Balance: N/A")
	
	@player_list
	def commandQuitMsg(self, parts, fromloc, overriderank):
		self.client.persist.set("main", "quitmsg", " ".join(parts[1:]))
		self.client.quitmsg = " ".join(parts[1:])
		self.client.sendServerMessage("Your quit message is now: %s" % " ".join(parts[1:]))
	
	@player_list
	def commandQuit(self, parts, fromloc, overriderank):
		if not len(parts) > 1:
			self.client.sendError("Quit: %s" % self.client.quitmsg)
		else:
			self.client.quitmsg = " ".join(parts[1:])
			self.client.sendError("Quit: %s" % " ".join(parts[1:]))
