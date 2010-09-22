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

import datetime
import traceback
from lib.twisted.words.protocols import irc
from lib.twisted.words.protocols.irc import IRC
from lib.twisted.internet import protocol
import logging
from constants import *
from globals import *
from blockbox.plugins import protocol_plugins
from blockbox.decorators import *

class ChatBot(irc.IRCClient):
	"""An IRC-server chat integration bot."""
	
	def connectionMade(self):
		self.logger = logging.getLogger("IRC Bot")
		self.ops = []
		self.nickname = self.factory.main_factory.irc_nick
		self.password = self.factory.main_factory.irc_pass
		self.prefix = "none"
		irc.IRCClient.connectionMade(self)
		self.factory.instance = self
		self.factory, self.controller_factory = self.factory.main_factory, self.factory
		self.world = None
		self.sendLine('NAMES ' + self.factory.irc_channel)

	def connectionLost(self, reason):
		irc.IRCClient.connectionLost(self, reason)
		self.logger.info("Disconnected. (%s)" % reason)

	# callbacks for events

	def signedOn(self):
		"""Called when bot has succesfully signed on to server."""
		self.join(self.factory.irc_channel)

	def joined(self, channel):
		"""This will get called when the bot joins the channel."""
		self.logger.info("Joined %s." % channel)
		self.msg("NickServ", "IDENTIFY %s" % self.password)

	def sendError(self, error):
		self.log("Sending error: %s" % error)
		self.sendPacked(TYPE_ERROR, error)
		reactor.callLater(0.2, self.transport.loseConnection)

	def lineReceived(self, line): #use instead of priv message
		line = irc.lowDequote(line)
		try:
			prefix, command, params = irc.parsemsg(line)
			if irc.numeric_to_symbolic.has_key(command):
				command = irc.numeric_to_symbolic[command]
			self.handleCommand(command, prefix, params)
		except irc.IRCBadMessage:
			self.badMessage(line, *sys.exc_info())
		try:
			if command == "RPL_NAMREPLY":
				names = params[3].split()
				for name in names:
					if name.startswith("@"):
						self.ops.append(name[1:])
		except:
			self.logger.error(traceback.format_exc())
			#self.msg(user,"ERROR " + traceback.format_exc())

	def AdminCommand(self, command):
		try:
			user = command[0]
			if user in self.ops:
				if command[1].startswith("#"):
					#It's an staff-only message.
					if len(command[1]) == 1:
						print ("Please include a message to send.")
					else:
						try:
							text = " ".join(command[1:])[1:]
						except ValueError:
							self.factory.queue.put((self, TASK_MESSAGE, (0, COLOUR_DARKGREEN,"Console", message)))
						else:
							self.factory.queue.put((self, TASK_STAFFMESSAGE, (0, COLOUR_PURPLE,command[0],text)))
							self.adlog = open("logs/server.log", "a")
							self.adlog = open("logs/world.log", "a")
							self.adlog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" | STAFF | " + command[0] + ": "+text+"\n")
							self.adlog.flush()
				elif command[1] == ("help"):
					self.msg(user, "Admin Help")
					self.msg(user, "Commands: Use 'cmdlist'")
					self.msg(user, "StaffChat: Use '#message'")
				elif command[1] == ("cmdlist"):
					self.msg(user, "Here are your Admin Commands:")
					self.msg(user, "ban, banned, banreason, boot, derank, kick, rank, shutdown and spec")
					self.msg(user, "Use 'command arguments' to do it.")
				elif command[1] == ("banreason"):
					if len(msg_command) == 3:
						username = msg_command[2]
						if not self.factory.isBanned(username):
							self.msg(user,"%s is not Banned." % username)
						else:
							self.msg(user,"Reason: %s" % self.factory.banReason(username))
					else:
						self.msg(user,"You must provide a name.")
				elif command[1] == ("banned"):
					self.msg(user,  ", ".join(self.factory.banned))
				elif command[1] == ("kick"):
					user = command[2]
					for client in self.factory.clients.values():
						if client.username.lower() == user.lower():
							client.sendError("You were kicked!")
							self.msg(user, user+": "+str(command[2])+" has been kicked from the server.")
							return
					self.msg(user, "User "+str(command[2])+" is not online.")
				elif command[1] == ("ban"):
					if command > 3:
						if self.factory.isBanned(command[2]):
							self.msg(user,"%s is already Banned." % command[2])
						else:
							self.factory.addBan(command[2], " ".join(command[3:]))
							if command[2] in self.factory.usernames:
								self.factory.usernames[command[2]].sendError("You got Banned!")
							self.msg(user,"%s has been Banned for %s." % (command[2]," ".join(command[3:])))
					else:
						self.msg(user,"Please give a username and reason.")
				elif command[1] == ("shutdown"):
					world = str(command[2]).lower()
					self.factory.unloadWorld(world)
					self.msg(user,"World '"+world+"' shutdown.")
				elif command[1] == ("rank"):
					if not command > 2:
						self.msg(user, "You must provide a username.")
					else:
						self.msg(user,Rank(self, command[1:] + [user], False, True, self.factory))
				elif command[1] == ("derank"):
					if not command > 2:
						self.msg(user, "You must provide a username.")
					else:
						self.msg(user,DeRank(self, command[1:] + [user], False, True, self.factory))
				elif command[1] == ("spec"):
					if not command > 2:
						self.msg(user, "You must provide a username.")
					else:
						self.msg(user,Spec(self, command[1], False, True, self.factory))
				elif command[1] == ("boot"):
					world = str(command[2]).lower()
					self.factory.loadWorld("worlds/"+world, world)
					self.msg(user,"World '"+world+"' booted.")
				else:
					self.msg(user, "Sorry, "+command[1]+" is not a command!")
			else:
				if command[1].startswith("#"):
					self.msg(user, "You must be an op to use StaffChat")
				else:
					self.msg(user, "You must be an op to use %s." %command[1])
			if not command[1].startswith("#"):
				self.logger.info("%s just used: %s" %(user," ".join(command[1:])))
		except:
			self.logger.error(traceback.format_exc())
			self.msg(user,"ERROR " + traceback.format_exc())

	def privmsg(self, user, channel, msg):
		"""This will get called when the bot receives a message."""
		try:
			user = user.split('!', 1)[0]
			msg = "".join([char for char in msg if ord(char) < 128 and char != "" or "0"])
			if channel == self.nickname:
				if not self.nickname == user and not user == "NickServ" and not user == "ChanServ" and not user == "MemoServ":
					msg_command = msg.split()
					self.AdminCommand([user] + msg_command)
			elif channel.lower() == self.factory.irc_channel.lower():
				if msg.lstrip(self.nickname).startswith("$"+self.nickname):
					msg_command = msg.split()
					if msg_command > 1:
						if msg_command[1] == ("who"):
							self.msg(self.factory.irc_channel, "Who's Online?")
							none=True
							for key in self.factory.worlds:
								users =  ", ".join(str(c.username) for c in self.factory.worlds[key].clients)
								if users:
									whois = ("%s: %s" % (key,users))
									self.msg(self.factory.irc_channel, whois)
									users=None
									none=False
							if none:
								self.msg(self.factory.irc_channel, "No users are online.")
						elif msg_command[1] == ("worlds"):
							self.msg(self.factory.irc_channel, "Worlds Booted")
							worlds = ", ".join([id for id, world in self.factory.worlds.items()])
							self.msg(self.factory.irc_channel, "Online Worlds: "+worlds)
						elif msg_command[1] == ("staff"):
							self.msg(self.factory.irc_channel,"The Server Staff")
							list = Staff(self, self.factory)
							for each in list:
								self.msg(self.factory.irc_channel," ".join(each))
						elif msg_command[1] == ("credits"):
							self.msg(self.factory.irc_channel,"Credits")
							list = Credits(self, self.factory)
							for each in list:
								self.msg(self.factory.irc_channel,"".join(each))
						elif msg_command[1] == ("help"):
							self.msg(self.factory.irc_channel, "Help Center")
							self.msg(self.factory.irc_channel, "About: Use '$"+self.nickname+" about'")
							self.msg(self.factory.irc_channel, "Credits: Use '$"+self.nickname+" credits'")
							self.msg(self.factory.irc_channel, "Commands: Use '$"+self.nickname+" cmdlist'")
							self.msg(self.factory.irc_channel, "WorldChat: Use '!world message'")
						elif msg_command[1] == ("cmdlist"):
							self.msg(self.factory.irc_channel, "Command List")
							self.msg(self.factory.irc_channel, "about, cmdlist, credits, help, staff, who and worlds")
							self.msg(self.factory.irc_channel, "Use '$"+self.nickname+" command arguments' to do it.")
							self.msg(self.factory.irc_channel, "NOTE: Admin Commands are by PMing "+self.nickname+" - only for ops.")
						elif msg_command[1] == ("about"):
							self.msg(self.factory.irc_channel, "About the Server - blockBox %s - http://blockbox.hk-diy.net/" % VERSION)
							self.msg(self.factory.irc_channel, "Name: "+self.factory.server_name)
							self.msg(self.factory.irc_channel, "URL: "+self.factory.heartbeat.url)
							self.msg(self.factory.irc_channel, "Site: "+self.factory.info_url)
							self.msg(self.factory.irc_channel, "Owner: "+self.factory.owner)
						else:
							self.msg(self.factory.irc_channel, "Sorry, "+msg_command[1]+" is not a command!")
					self.logger.info("%s just used: %s" %(user," ".join(msg_command[1:])))
				elif msg.startswith("!"):
					#It's a world message.
					message = msg.split(" ")
					if len(message) == 1:
						self.msg(self.factory.irc_channel,"Please include a message to send.")
					else:
						try:
						   world = message[0][1:len(message[0])]
						   out = " ".join(message[1:])
						   text = COLOUR_YELLOW+"!"+COLOUR_PURPLE+user+":"+COLOUR_WHITE+" "+out
						except ValueError:
							self.msg(self.factory.irc_channel,"Please include a message to send.")
						else:
							if world in self.factory.worlds:
								self.factory.queue.put ((self.factory.worlds[world],TASK_WORLDMESSAGE,(255, self.factory.worlds[world], text),))
								self.logger.info("WORLD - "+user+" in "+str(self.factory.worlds[world].id)+": "+out)
								self.wclog = open("logs/server.log", "a")
								self.wclog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" | WORLD | "+user+" in "+str(self.factory.worlds[world].id)+": "+out+"\n")
								self.wclog.flush()
								self.wclog.close()
							else:
								self.msg(self.factory.irc_channel,"That world does not exist. Try !world message")
				elif self.prefix == "none":
					allowed = True
					goodchars = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", " ", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", " ", "!", "@", "#", "$", "%", "*", "(", ")", "-", "_", "+", "=", "{", "[", "}", "]", ":", ";", "\"", "\'", "<", ",", ">", ".", "?", "/", "\\", "|"]
					for character in msg:
						if not character.lower() in goodchars:
							msg = msg.replace(character, "*")
					msg = msg.replace("%0", "&0")
					msg = msg.replace("%1", "&1")
					msg = msg.replace("%2", "&2")
					msg = msg.replace("%3", "&3")
					msg = msg.replace("%4", "&4")
					msg = msg.replace("%5", "&5")
					msg = msg.replace("%6", "&6")
					msg = msg.replace("%7", "&7")
					msg = msg.replace("%8", "&8")
					msg = msg.replace("%9", "&9")
					msg = msg.replace("%a", "&a")
					msg = msg.replace("%b", "&b")
					msg = msg.replace("%c", "&c")
					msg = msg.replace("%d", "&d")
					msg = msg.replace("%e", "&e")
					msg = msg.replace("%f", "&f")
					msg = msg.replace("&0", "&0")
					msg = msg.replace("&1", "&1")
					msg = msg.replace("&2", "&2")
					msg = msg.replace("&3", "&3")
					msg = msg.replace("&4", "&4")
					msg = msg.replace("&5", "&5")
					msg = msg.replace("&6", "&6")
					msg = msg.replace("&7", "&7")
					msg = msg.replace("&8", "&8")
					msg = msg.replace("&9", "&9")
					msg = msg.replace("&a", "&a")
					msg = msg.replace("&b", "&b")
					msg = msg.replace("&c", "&c")
					msg = msg.replace("&d", "&d")
					msg = msg.replace("&e", "&e")
					msg = msg.replace("&f", "&f")
					msg = msg.replace("1", "&0")
					msg = msg.replace("2", "&1")
					msg = msg.replace("3", "&2")
					msg = msg.replace("10", "&3")
					msg = msg.replace("5", "&4")
					msg = msg.replace("4", "&5")
					msg = msg.replace("7", "&6")
					msg = msg.replace("15", "&7")
					msg = msg.replace("14", "&8")
					msg = msg.replace("12", "&9")
					msg = msg.replace("9", "&a")
					msg = msg.replace("11", "&b")
					msg = msg.replace("4", "&c")
					msg = msg.replace("13", "&d")
					msg = msg.replace("8", "&e")
					msg = msg.replace("0", "&f")
					msg = msg.replace("01", "&0")
					msg = msg.replace("02", "&1")
					msg = msg.replace("03", "&2")
					msg = msg.replace("05", "&4")
					msg = msg.replace("04", "&5")
					msg = msg.replace("07", "&6")
					msg = msg.replace("09", "&a")
					msg = msg.replace("04", "&c")
					msg = msg.replace("08", "&e")
					msg = msg.replace("00", "&f")
					msg = msg.replace("./", " /")
					msg = msg.replace(".!", " !")
					if msg[len(msg)-2] == "&":
						self.msg(self.factory.irc_channel,"You can not use a color at the end of a message")
						return
					if len(msg) > 51:
						moddedmsg = msg[:51].replace(" ", "")
						if moddedmsg[len(moddedmsg)-2] == "&":
							msg = msg.replace("&", "*")
					self.factory.queue.put((self, TASK_IRCMESSAGE, (127, userColour(user), user, msg)))
		except:
			self.logger.error(traceback.format_exc())
			self.msg(self.factory.irc_channel,"ERROR " + traceback.format_exc())

	def userColour(self, user):
		if user in self.factory.spectators:
			color = COLOUR_BLACK
		elif user is self.factory.owner:
			color = COLOUR_DARKGREEN
		elif user in self.factory.directors:
			color = COLOUR_GREEN
		elif user in self.factory.admins:
			color = COLOUR_DARKRED
		elif user in self.factory.mods:
			color = COLOUR_RED
		elif self.username.lower() == "notch" or self.username.lower() == "dock" or self.username.lower() == "pixeleater" or self.username.lower() == "andrewph" or self.username.lower() == "ikjames" or self.username.lower() == "goober" or self.username.lower() == "gothfox" or self.username.lower() == "destroyerx1" or self.username.lower() == "willempiee" or self.username.lower() == "dwarfy" or self.username.lower() == "erronjason" or self.username.lower() == "adam01" or self.username.lower() == "aera" or self.username.lower() == "andrewgodwin" or self.username.lower() == "revenant" or self.username.lower() == "gdude2002" or self.username.lower() == "varriount" or self.username.lower() == "notmeh" or self.username.lower() == "bidoof_king" or self.username.lower() == "rils" or self.username.lower() == "fragmer" or self.username.lower() == "tktech" or self.username.lower() == "pyropyro":
			color = COLOUR_YELLOW
		elif user in self.factory.members:
			color = COLOUR_WHITE
		else:
			color = COLOUR_GREY
		return color

	def action(self, user, channel, msg):
		msg = msg.replace("./", " /")
		msg = msg.replace(".!", " !")
		"""This will get called when the bot sees someone do an action."""
		user = user.split('!', 1)[0]
		msg = "".join([char for char in msg if ord(char) < 128 and char != "" or "0"])
		self.factory.queue.put((self, TASK_ACTION, (127, COLOUR_PURPLE, user, msg)))

	def sendMessage(self, username, message):
		message = message.replace("&0", "01")
		message = message.replace("&1", "02")
		message = message.replace("&2", "03")
		message = message.replace("&3", "10")
		message = message.replace("&4", "05")
		message = message.replace("&5", "04")
		message = message.replace("&6", "07")
		message = message.replace("&7", "15")
		message = message.replace("&8", "14")
		message = message.replace("&9", "12")
		message = message.replace("&a", "09")
		message = message.replace("&b", "11")
		message = message.replace("&c", "04")
		message = message.replace("&d", "13")
		message = message.replace("&e", "08")
		message = message.replace("&f", "00")
		self.msg(self.factory.irc_channel, "%s: %s" % (username, message))

	def sendServerMessage(self, message,admin=False,user=""):
		message = message.replace("./", " /")
		message = message.replace(".!", " !")
		message = message.replace("&0", "01")
		message = message.replace("&1", "02")
		message = message.replace("&2", "03")
		message = message.replace("&3", "10")
		message = message.replace("&4", "05")
		message = message.replace("&5", "04")
		message = message.replace("&6", "07")
		message = message.replace("&7", "15")
		message = message.replace("&8", "14")
		message = message.replace("&9", "12")
		message = message.replace("&a", "09")
		message = message.replace("&b", "11")
		message = message.replace("&c", "04")
		message = message.replace("&d", "13")
		message = message.replace("&e", "08")
		message = message.replace("&f", "00")
		if admin:
			for op in self.ops:
				if not op == user:
					self.IRCClient.msg(op, "%s" % (message))
		else:
			self.msg(self.factory.irc_channel, "%s" % (message, ))

	def sendAction(self, username, message):
		message = message.replace("&0", "01")
		message = message.replace("&1", "02")
		message = message.replace("&2", "03")
		message = message.replace("&3", "10")
		message = message.replace("&4", "05")
		message = message.replace("&5", "04")
		message = message.replace("&6", "07")
		message = message.replace("&7", "15")
		message = message.replace("&8", "14")
		message = message.replace("&9", "12")
		message = message.replace("&a", "09")
		message = message.replace("&b", "11")
		message = message.replace("&c", "04")
		message = message.replace("&d", "13")
		message = message.replace("&e", "08")
		message = message.replace("&f", "00")
		self.msg(self.factory.irc_channel, "* %s %s" % (username, message))

	# irc callbacks

	def irc_NICK(self, prefix, params):
		"""Called when an IRC user changes their nickname."""
		old_nick = prefix.split('!')[0]
		new_nick = params[0]
		if old_nick in self.ops:
			self.ops.remove(old_nick)
			self.ops.append(new_nick)
		pass

		
	def userKicked(self, kickee, channel, kicker, message):
		"""Called when I observe someone else being kicked from a channel.
		"""
		if kickee in self.ops:
			self.ops.remove(kickee)
		pass

	def userLeft(self, user, channel):
		"""Called when I see another user leaving a channel.
		"""
		if user in self.ops:
			self.ops.remove(user)

	def modeChanged(self, user, channel, set, modes, args):
		if set and modes.startswith("o"):
			for name in args:
				if not name in self.ops:
					self.ops.append(name)
		elif not set and modes.startswith("o"):
			for name in args:
				if name in self.ops:
					self.ops.remove(name)

class ChatBotFactory(protocol.ClientFactory):
	# the class of the protocol to build when new connection is made
	protocol = ChatBot
	
	def __init__(self, main_factory):
		self.main_factory = main_factory
		self.instance = None

	def clientConnectionLost(self, connector, reason):
		"""If we get disconnected, reconnect to server."""
		self.instance = None
		connector.connect()

	def clientConnectionFailed(self, connector, reason):
		self.logger.warning("IRC connection failed: %s" % reason)
		self.instance = None

	def sendMessage(self, username, message):
		if self.instance:
			message = message.replace("&0", "01")
			message = message.replace("&1", "02")
			message = message.replace("&2", "03")
			message = message.replace("&3", "10")
			message = message.replace("&4", "05")
			message = message.replace("&5", "04")
			message = message.replace("&6", "07")
			message = message.replace("&7", "15")
			message = message.replace("&8", "14")
			message = message.replace("&9", "12")
			message = message.replace("&a", "09")
			message = message.replace("&b", "11")
			message = message.replace("&c", "04")
			message = message.replace("&d", "13")
			message = message.replace("&e", "08")
			message = message.replace("&f", "00")
			message = message.replace("./", " /")
			message = message.replace(".!", " !")
			message = message.replace(".@", " @")
			message = message.replace(".#", " #")
			self.instance.sendMessage(username, message)

	def sendAction(self, username, message):
		if self.instance:
			message = message.replace("&0", "01")
			message = message.replace("&1", "02")
			message = message.replace("&2", "03")
			message = message.replace("&3", "10")
			message = message.replace("&4", "05")
			message = message.replace("&5", "04")
			message = message.replace("&6", "07")
			message = message.replace("&7", "15")
			message = message.replace("&8", "14")
			message = message.replace("&9", "12")
			message = message.replace("&a", "09")
			message = message.replace("&b", "11")
			message = message.replace("&c", "04")
			message = message.replace("&d", "13")
			message = message.replace("&e", "08")
			message = message.replace("&f", "00")
			message = message.replace("./", " /")
			message = message.replace(".!", " !")
			message = message.replace(".@", " @")
			message = message.replace(".#", " #")
			self.instance.sendAction(username, message)

	def sendServerMessage(self, message,admin=False,user=""):
		if self.instance:
			message = message.replace("&0", "01")
			message = message.replace("&1", "02")
			message = message.replace("&2", "03")
			message = message.replace("&3", "10")
			message = message.replace("&4", "05")
			message = message.replace("&5", "04")
			message = message.replace("&6", "07")
			message = message.replace("&7", "15")
			message = message.replace("&8", "14")
			message = message.replace("&9", "12")
			message = message.replace("&a", "09")
			message = message.replace("&b", "11")
			message = message.replace("&c", "04")
			message = message.replace("&d", "13")
			message = message.replace("&e", "08")
			message = message.replace("&f", "00")
			message = message.replace("./", " /")
			message = message.replace(".!", " !")
			message = message.replace(".@", " @")
			message = message.replace(".#", " #")
			self.instance.sendServerMessage(message,admin,user,IRC)