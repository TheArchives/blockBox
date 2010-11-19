# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import random
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class MessagingPlugin(ProtocolPlugin):
	commands = {
		"say": "commandSay",
		"msg": "commandSay",
		"me": "commandMe",
		"srb": "commandSRB",
		"srs": "commandSRS",
		"u": "commandUrgent",
		"urgent": "commandUrgent",
		"away": "commandAway",
		"afk": "commandAway",
		"brb": "commandAway",
		"back": "commandBack",
	}

	@player_list
	def commandBack(self, parts, fromloc, overriderank):
		"/back - Guest\nPrints out message of you coming back."
		if len(parts) != 1:
			self.client.sendServerMessage("This command doesn't need arguments")
		else:
			self.client.factory.queue.put((self.client, TASK_AWAYMESSAGE, self.client.username + " is now: "+COLOUR_DARKGREEN+"Back."))
			self.client.gone = 0
	@player_list
	def commandAway(self, parts, fromloc, overriderank):
		 "/away reason - Guest\nAliases: afk, brb\nPrints out message of you going away."
		 if len(parts) == 1:
			 self.client.factory.queue.put((self.client, TASK_AWAYMESSAGE, self.client.username + " has gone: Away."))
			 self.client.gone = 1
		 else:
			 self.client.factory.queue.put((self.client, TASK_AWAYMESSAGE, self.client.username + " has gone: Away"+COLOUR_WHITE+" "+(" ".join(parts[1:]))))
			 self.client.gone = 1

	@player_list
	def commandMe(self, parts, fromloc, overriderank):
		"/me action - Guest\nPrints 'username action'"
		if len(parts) == 1:
			self.client.sendServerMessage("Please type an action.")
		else:
			if self.client.isSilenced():
				self.client.sendServerMessage("You are Silenced and lost your tongue.")
			else:
				self.client.factory.queue.put((self.client, TASK_ACTION, (self.client.id, self.client.userColour(), self.client.username, " ".join(parts[1:]))))
	@mod_only
	def commandSay(self, parts, fromloc, overriderank):
		"/say message - Mod\nAliases: msg\nPrints out message in the server color."
		if len(parts) == 1:
			self.client.sendServerMessage("Please type a message.")
		else:
			self.client.factory.queue.put((self.client, TASK_SERVERMESSAGE, ("[MSG] "+(" ".join(parts[1:])))))
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
