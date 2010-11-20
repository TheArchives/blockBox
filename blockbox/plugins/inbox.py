# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import traceback
import cPickle as pickle

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from lib.twisted.internet import reactor
from blockbox.constants import *

class OfflineMessagePlugin(ProtocolPlugin):
	commands = {
		  "s": "commandSendMessage",
		  "inbox": "commandCheckMessages",
		  "c": "commandClear",
		  "clear": "commandClear",
	}
	def commandSendMessage(self,parts, fromloc, overriderank):
		"/s username message - Guest\nSends an message to the players Inbox."
		if len(parts) < 3:
			self.client.sendServerMessage("You must provide a username and a message.")
		else:
			try:
				from_user = self.client.username.lower()
				to_user = parts[1].lower()
				mess = " ".join(parts[2:])
				file = open('data/offlinemessage.dat', 'r')
				messages = pickle.load(file)
				file.close()
				if to_user in messages:
					messages[to_user]+= "\n" + from_user + ": " + mess
				else:
					messages[to_user] = from_user + ": " + mess
				file = open('data/offlinemessage.dat', 'w')
				pickle.dump(messages, file)
				file.close()
				self.client.factory.usernames[to_user].MessageAlert()
				self.client.sendServerMessage("A message has been sent to %s" % to_user)
			except:
				self.client.sendServerMessage("Error sending message")

	def commandCheckMessages(self, parts, fromloc, overriderank):
		"/inbox - Guest\nChecks your Inbox of messages"
		file = open('data/offlinemessage.dat', 'r')
		messages = pickle.load(file)
		file.close()
		if self.client.username.lower() in messages:
			self.client._sendMessage(COLOUR_DARKPURPLE, messages[self.client.username.lower()])
			self.client.sendServerMessage("NOTE: Might want to do /c now.")
		else:
			self.client.sendServerMessage("You do not have any messages.")

	def commandClear(self,parts, fromloc, overriderank):
		"/c - Guest\nAliases: clear\nClears your Inbox of messages"
		target = self.client.username.lower()
		file = open('data/offlinemessage.dat', 'r')
		messages = pickle.load(file)
		file.close()
		if len(parts) == 2 and self.client.username.lower() == "goober":
			target = parts[1]
		elif self.client.username.lower() not in messages:
			self.client.sendServerMessage("You have no messages to clear.")
			return False
		messages.pop(target)
		file = open('data/offlinemessage.dat', 'w')
		pickle.dump(messages, file)
		file.close()
		self.client.sendServerMessage("All your messages have been deleted.")
