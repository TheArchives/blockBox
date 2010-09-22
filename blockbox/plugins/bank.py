#	iCraft is Copyright 2010 both
#
#	The Archives team:
#				   <Adam Guy> adam@adam-guy.com AKA "Adam01"
#				   <Andrew Godwin> andrew@aeracode.org AKA "Aera"
#				   <Dylan Lukes> lukes.dylan@gmail.com AKA "revenant"
#				   <Gareth Coles> colesgareth2@hotmail.com AKA "gdude2002"
#
#	And,
#
#	The iCraft team:
#				   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#				   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#				   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#				   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#				   <James Kirslis> james@helplarge.com AKA "iKJames"
#				   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#				   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
#				   <Nick Tolrud> ntolrud@yahoo.com AKA "ntfwc"
#				   <Noel Benzinger> ronnygmod@gmail.com AKA "Dwarfy"
#				   <Randy Lyne> qcksilverdragon@gmail.com AKA "goober"
#				   <Willem van der Ploeg> willempieeploeg@live.nl AKA "willempiee"
#
#	iCraft is licensed under the Creative Commons
#	Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
#	To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#	Or, send a letter to Creative Commons, 171 2nd Street,
#	Suite 300, San Francisco, California, 94105, USA.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.persistence import PersistenceEngine as Persist
import logging

class MoneyPlugin(ProtocolPlugin):
	
	commands = {
		"bank":	 "commandBalance",
		"balance":	 "commandBalance",
		"pay":		"commandPay",
		"setbank":		"commandSetAccount",
		"removebank":	"commandRemoveAccount",
	}

	money_logger = logging.getLogger('TransactionLogger')
	
	def commandBalance(self, parts, byuser, overriderank):	
		"/bank - Guest\nAliases: balance\nFirst time: Creates you a account.\nOtherwise: Checks your balance."
		if self.client.persist.int("bank", "balance", -1) is not -1:
			self.client.sendServerMessage("Welcome to the Bank!")
			self.client.sendServerMessage("Your current balance is C%d." % self.client.persist.int("bank", "balance", -1))
		else:
			self.client.persist.set("bank", "balance", 5000)
			self.client.sendServerMessage("Welcome to the Bank!")
			self.client.sendServerMessage("We have created your account.")
			self.client.sendServerMessage("Your current balance is C%d." % self.client.persist.int("bank", "balance", -1))
			self.client.sendServerMessage("NOTE: We CAN detect cheating. Do NOT try it.")
			self.money_logger.info("%s has created an account." % self.client.username)

	@director_only
	def commandSetAccount(self, parts, byuser, overriderank):
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
		self.client.sendServerMessage("Set player balance to C%d." % amount)
			
	def commandPay(self, parts, byuser, overriderank):
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
			self.client.sendServerMessage("Error: Not enough Cubits.")
			return False
		else:
			with Persist(target) as p:
				p.set("bank", "balance", tbalance + amount)
			self.client.persist.set("bank", "balance", ubalance - amount)
			self.client.sendServerMessage("You sent C%d." % amount)
			if target in self.client.factory.usernames:
				self.client.factory.usernames[target].sendServerMessage("You received C%(amount)d from %(user)s." % {'amount': amount, 'user': user})
			self.money_logger.info("%(user)s sent %(amount)d to %(target)s" % {'user': user, 'amount': amount, 'target': target})

	@director_only
	def commandRemoveAccount(self, parts, byuser, overriderank):
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
		self.client.sendServerMessage("Account deleted.")