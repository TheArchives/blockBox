# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from __future__ import with_statement

import math, random

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.irc_client import *
from blockbox.persistence import PersistenceEngine as Persist
from blockbox.plugins import ProtocolPlugin

class InteractionPlugin(ProtocolPlugin):
	"Commands for player interactions."

	commands = {
		"say": "commandSay",
		"msg": "commandSay",
		"me": "commandMe",
		"away": "commandAway",
		"afk": "commandAway",
		"brb": "commandAway",
		"back": "commandBack",
		"slap": "commandSlap",
		"punch": "commandPunch",
		"roll": "commandRoll",

		"bank": "commandBalance",
		"balance": "commandBalance",
		"pay": "commandPay",
		"setbank": "commandSetAccount",
		"removebank": "commandRemoveAccount",

		"count": "commandCount",
		"countdown": "commandCount",

		"s": "commandSendMessage",
		"inbox": "commandCheckMessages",
		"c": "commandInboxClear",
		"clear": "commandInboxClear",

		"spectate": "commandSpectate",
		"watch": "commandSpectate",
		"follow": "commandSpectate",
	}

	hooks = {
		"poschange": "posChanged",
	}

	money_logger = logging.getLogger('TransactionLogger')

	def gotClient(self):
		self.num = int(0)
		self.spectating = False

	def posChanged(self, x, y, z, h, p):
		"Hook trigger for when the player moves"
		spectators = set()
		for uid in self.client.factory.clients:
			user = self.client.factory.clients[uid]
			try:
				if user.spectating == self.client.id:
					if user.x != x and user.y != y and user.z != z:
						user.teleportTo(x >> 5, y >> 5, z >> 5, h, p)
			except AttributeError:
				pass

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

	@player_list
	def commandSlap(self, parts, fromloc, overriderank):
		"/slap username [with object] - Guest\nSlap username [with object]."
		if len(parts) == 1:
			self.client.sendServerMessage("Enter the name for the slappee")
		else:
			stage = 0
			name = ''
			object = ''
			for i in range(1, len(parts)):
				if parts[i] == "with":
					stage = 1
					continue
					if stage == 0 : 
						name += parts[i]
						if (i+1 != len(parts) ) : 
							if ( parts[i+1] != "with" ) : name += " "
					else:
						object += parts[i]
						if ( i != len(parts) - 1 ) : object += " "
				else:
					if stage == 1:
						self.client.sendWorldMessage("* "+COLOUR_PURPLE+"%s slaps %s with %s!" % (self.client.username,name,object))
						self.client.factory.irc_relay.sendServerMessage("%s slaps %s with %s!" % (self.client.username,name,object))
					else:
						self.client.sendWorldMessage("* "+COLOUR_PURPLE+"%s slaps %s with a giant smelly trout!" % (self.client.username,name))
						self.client.factory.irc_relay.sendServerMessage("* %s slaps %s with a giant smelly trout!" % (self.client.username,name))

	@player_list
	def commandPunch(self, parts, fromloc, overriderank):
		"/punch username [by bodypart] - Punch username [by bodypart]."
		if len(parts) == 1:
			self.client.sendServerMessage("Enter the name for the punchee")
		else:
			stage = 0
			name = ''
			object = ''
			for i in range(1, len(parts)):
				if parts[i] == "by":
					stage = 1
					continue
					if stage == 0 : 
						name += parts[i]
						if (i+1 != len(parts) ) : 
							if ( parts[i+1] != "by" ) : name += " "
					else:
						object += parts[i]
						if ( i != len(parts) - 1 ) : object += " "
				else:
					if stage == 1:
						self.client.sendWorldMessage("* "+COLOUR_PURPLE+"%s punches %s in the %s!" % (self.client.username,name,object))
						self.client.factory.irc_relay.sendServerMessage("%s punches %s in the %s!" % (self.client.username,name,object))
					else: 
						self.client.sendWorldMessage("* "+COLOUR_PURPLE+"%s punches %s in the face!" % (self.client.username,name))
						self.client.factory.irc_relay.sendServerMessage("* %s punches %s in the face!" % (self.client.username,name))

	def commandRoll(self, parts, fromloc, overriderank):
		"/roll max - Guest\nRolls a random number from 1 to max. Announces to world."
		if len(parts) == 1:
			self.client.sendServerMessage("Please enter a number as the maximum roll.")
		else:
			try:
				roll = roll = int(math.floor((random.random()*(int(parts[1])-1)+1)))
			except ValueError:
				self.client.sendServerMessage("Please enter an integer as the maximum roll.")
			else:
				self.client.sendWorldMessage("%s rolled a %s" % (self.client.username, roll))

	def commandBalance(self, parts, fromloc, overriderank):
		"/bank - Guest\nAliases: balance\nFirst time: Creates you a account.\nOtherwise: Checks your balance."
		if self.client.persist.int("bank", "balance", -1) is not -1:
			self.client.sendServerMessage("Welcome to the Bank!")
			self.client.sendServerMessage("Your current balance is %d %s." % (self.client.persist.int("bank", "balance", -1), self.client.factory.credit_name))
		else:
			self.client.persist.set("bank", "balance", self.client.factory.initial_amount)
			self.client.factory.balancesqllog.write("INSERT INTO " + self.client.factory.table_prefix + "players (username, balance) VALUES ('" + self.client.username + "', " + self.client.factory.initial_amount + ");")
			self.client.factory.balancesqllog.flush()
			self.client.sendServerMessage("Welcome to the Bank!")
			self.client.sendServerMessage("We have created your account.")
			self.client.sendServerMessage("Your current balance is %d %s." % (self.client.persist.int("bank", "balance", -1), self.client.factory.credit_name))
			self.client.sendServerMessage("NOTE: We CAN detect cheating. Do NOT try it.")
			self.money_logger.info("%s has created an account." % self.client.username)

	@director_only
	def commandSetAccount(self, parts, fromloc, overriderank):
		"/setbank username amount - Director\nEdits Bank Account"
		if len(parts) != 3:
			self.client.sendServerMessage("Syntax: /set <target> <amount>")	
			return False
		target = parts[1]
		with Persist(target) as p:
			tbalance = p.int("bank", "balance", -1)
		if tbalance is -1:
			self.client.sendServerMessage("Invalid target.")
			return False
		try:
			amount = int(parts[2])
		except ValueError:
			self.client.sendServerMessage("Invalid amount.")
			return False
		with Persist(target) as p:
			p.set("bank", "balance", amount)
		self.client.factory.balancesqllog.write("UPDATE " + self.client.factory.table_prefix + "players SET balance=" + amount + " WHERE username='" + target + "';")
		self.client.factory.balancesqllog.flush()
		self.client.sendServerMessage("Set player balance to %d %s." % (amount, self.client.factory.credit_name))

	def commandPay(self, parts, fromloc, overriderank):
		"/pay username amount - Guest\nThis lets you send money to other people."
		if len(parts) != 3:
			self.client.sendServerMessage("/pay <target> <amount>")
			return False
		user = self.client.username.lower()
		ubalance = self.client.persist.int("bank", "balance", -1)
		target = parts[1].lower()
		with Persist(target) as p:
			tbalance = p.int("bank", "balance", -1)
		if tbalance is -1:
			self.client.sendServerMessage("Error: Invalid target.")
			return False
		try:
			amount = int(parts[2])
		except ValueError:
			self.client.sendServerMessage("Error: Invalid amount.")
			return False
		if ubalance is -1:
			self.client.sendServerMessage("Error: You don't have an account.")
			self.client.sendServerMessage("Notice: Do /bank to create one.")
			return False
		elif amount < 0 and not self.client.isDirector():
			self.client.sendServerMessage("Error: Amount must be positive.")
			return False
		elif amount > ubalance or amount < -(tbalance):
			self.client.sendServerMessage("Error: Not enough %s." % self.client.factory.credit_name)
			return False
		else:
			with Persist(target) as p:
				p.set("bank", "balance", tbalance + amount)
			self.client.persist.set("bank", "balance", ubalance - amount)
			self.client.factory.balancesqllog.write("UPDATE " + self.client.factory.table_prefix + "players SET balance=(balance-" + amount + ") WHERE username='" + self.client.username + "';")
			self.client.factory.balancesqllog.flush()
			self.client.sendServerMessage("You sent %d ." % amount)
			if target in self.client.factory.usernames:
				self.client.factory.usernames[target].sendServerMessage("You received %(amount)d %(creditname)s from %(user)s." % {'amount': amount, 'creditname': self.client.factory.credit_name, 'user': user})
				self.client.factory.balancesqllog.write("UPDATE " + self.client.factory.table_prefix + "players SET balance=(balance+" + amount + ") WHERE username='" + target + "';")
				self.client.factory.balancesqllog.flush()
			self.money_logger.info("%(user)s sent %(amount)d to %(target)s" % {'user': user, 'amount': amount, 'target': target})

	@director_only
	def commandRemoveAccount(self, parts, fromloc, overriderank):
		"/removebank username - Director\nRemoves Bank Account"
		if len(parts) != 2:
			self.client.sendServerMessage("Syntax: /removebank <target>")	
			return False
		target = parts[1]
		with Persist(target) as p:
			if p.int("bank", "balance", -1) is -1:
				self.client.sendServerMessage("Invalid target.")
				return False
			p.set("bank", "balance", -1)
			self.client.factory.balancesqllog.write("UPDATE " + self.client.factory.table_prefix + "players SET balance=-1 WHERE username='" + target + "';")
			self.client.factory.balancesqllog.flush()
		self.client.sendServerMessage("Account deleted.")

	@writer_only
	def commandCount(self, parts, fromloc, overriderank):
		"/count [number] - Builder\nAliases: countdown\nCounts down from 3 or from number given (up to 15)"
		if self.num != 0:
			self.client.sendServerMessage("You can only have one count at a time!")
			return
		if len(parts) > 1:
			try:
				self.num = int(parts[1])
			except ValueError:
				self.client.sendServerMessage("Number must be an integer!")
				return
		else:
			self.num = 3
		if self.num > 15:
			self.client.sendServerMessage("You can't count from higher than 15!")
			self.num = 0
			return
		counttimer = ResettableTimer(self.num, 1, self.sendgo, self.sendcount)
		self.client.sendPlainWorldMessage("&2[COUNTDOWN] %s" %self.num)
		counttimer.start()

	def sendgo(self):
		self.client.sendPlainWorldMessage("&2[COUNTDOWN] GO!")
		self.num = 0

	def sendcount(self, count):
		if not int(self.num)-int(count) == 0:
			self.client.sendPlainWorldMessage("&2[COUNTDOWN] %s" %(int(self.num)-int(count)))

	def commandSendMessage(self,parts, fromloc, overriderank):
		"/s username message - Guest\nSends an message to the player's Inbox."
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

	def commandInboxClear(self,parts, fromloc, overriderank):
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

	@player_list
	@op_only
	@only_username_command
	def commandSpectate(self, user, fromloc, overriderank):
		"/spectate username - Guest\nAliases: follow, watch\nFollows specified player around"
		nospec_check = True
		try:
			self.client.spectating
		except AttributeError:
			nospec_check = False
		if not nospec_check or self.client.spectating != user.id:
			self.client.sendServerMessage("You are now spectating %s" % user.username)
			self.client.spectating = user.id
		else:
			self.client.sendServerMessage("You are no longer spectating %s" % user.username)
			self.client.spectating = False