# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import datetime, gc, logging, sys, threading, time, traceback

from lib.twisted.internet import reactor

from blockbox.constants import *
from blockbox.globals import *
from blockbox.irc_client import ChatBotFactory

class StdinPlugin(threading.Thread):
	"The console."

	def __init__(self, server):
		threading.Thread.__init__(self)
		self.server = server
		self.stop = False
		self.console = True
		self.whisperlog = open("logs/whisper.log", "a")
		self.wclog = open("logs/staff.log", "a")
		self.adlog = open("logs/world.log", "a")
		self.logger = logging.getLogger("Console")

	def run(self):
		try:
			try:
				while not self.stop:
					try:
						line = sys.stdin.readline()
					except:
						return
					message = line
					if len(line)>1:
						goodchars = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", " ", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", " ", "!", "@", "#", "$", "%", "*", "(", ")", "-", "_", "+", "=", "{", "[", "}", "]", ":", ";", "\"", "\'", "<", ",", ">", ".", "?", "/", "\\", "|"]
						for character in message:
							if not character.lower() in goodchars:
								message = message.replace(character, "*")
						message = message.replace("%0", "&0")
						message = message.replace("%1", "&1")
						message = message.replace("%2", "&2")
						message = message.replace("%3", "&3")
						message = message.replace("%4", "&4")
						message = message.replace("%5", "&5")
						message = message.replace("%6", "&6")
						message = message.replace("%7", "&7")
						message = message.replace("%8", "&8")
						message = message.replace("%9", "&9")
						message = message.replace("%a", "&a")
						message = message.replace("%b", "&b")
						message = message.replace("%c", "&c")
						message = message.replace("%d", "&d")
						message = message.replace("%e", "&e")
						message = message.replace("%f", "&f")
						message = message.replace("&0", "&0")
						message = message.replace("&1", "&1")
						message = message.replace("&2", "&2")
						message = message.replace("&3", "&3")
						message = message.replace("&4", "&4")
						message = message.replace("&5", "&5")
						message = message.replace("&6", "&6")
						message = message.replace("&7", "&7")
						message = message.replace("&8", "&8")
						message = message.replace("&9", "&9")
						message = message.replace("&a", "&a")
						message = message.replace("&b", "&b")
						message = message.replace("&c", "&c")
						message = message.replace("&d", "&d")
						message = message.replace("&e", "&e")
						message = message.replace("&f", "&f")
						message = message.replace("./", " /")
						message = message.replace(".!", " !")
						message = message.replace(".@", " @")
						message = message.replace(".#", " #")
						if message[len(message)-3] == "&":
							print ("You cannot use a color at the end of a message.")
							return
						if message.startswith("/"):
							message = message.split(" ")
							message[0] = message[0][1:]
							message[len(message)-1] = message[len(message)-1][:len(message[len(message)-1])-1]
							# It's a command
							if message[0] == "kick":
								if len(message) == 1:
									print ("Please specify a username.")
								else:
									for client in self.server.clients.values():
										if client.username==message[1]:
											client.sendError("You were kicked!")
											print (message[1]+" has been kicked from the server.")
											pass
										else:
											print ("User "+str(message[1])+" is not online.")
											pass
							elif message[0] == "ban":
								if len(message) == 1:
									print ("Please specify a username.")
								else:
									username = message[1]
									if self.server.isBanned(username):
										print ("%s is already Banned." % username)
									else:
										if len(message) < 2:
											print ("Please give a reason.")
										else:
											self.server.addBan(username, " ".join(message[2:]))
											if username in self.server.usernames:
												ip = self.server.usernames[username].transport.getPeer().host
												self.server.usernames[username].sendError("You got Banned!")
												self.server.addIpBan(ip, " ".join(message[2:]))
												if username in self.server.usernames:
													self.server.usernames[username].sendError("You got Banned!")
												print ("%s has been IPBanned." % ip)
											print ("%s has been Banned." % username)
							elif message[0] == "rank":
								if len(message) == 1:
									print ("Please specify a username.")
								else:
									try:
										print Rank(self, message, 'console', True, self.server)
									except:
										print ("You must specify a rank and username.")
							elif message[0] == "derank":
								if len(message) == 1:
									print ("Please specify a username.")
								else:
									try:
										print DeRank(self, message, 'console', True, self.server)
									except:
										print ("You must specify a rank and username.")
							elif message[0] == "spec":
								if len(message) == 1:
									print ("Please specify a username.")
								else:
									try:
										print Spec(self, message[1], 'console', True, self.server)
									except:
										print ("Please specify a username.")
							elif message[0] == ("boot"):
								try:
									world = str(message[1]).lower()
								except:
									print ("Please specify a worldname.")
									continue
								try:
									self.server.loadWorld("mapdata/worlds/"+world, world)
								except AssertionError:
									print ("World '%s' does not exist." % world)
									continue
								print ("World '"+world+"' booted.")
							elif message[0] == ("shutdown"):
								try:
									world = str(message[1]).lower()
								except:
									print ("Please specify a worldname.")
									continue
								try:
									self.server.unloadWorld(world)
								except KeyError:
									print ("World '%s' does not exist." % world)
									continue
								print ("World '"+world+"' shutdown.")
							elif message[0] == ("new"):
								if len(message) == 1:
									print ("Please specify a new worldname.")
								elif self.server.world_exists(message[1]):
									print ("World name in use.")
								else:
									if len(message) == 2:
										template = "default"
									elif len(message) == 3 or len(message) == 4:
										template = message[2]
									world_id = message[1].lower()
									try:
										self.server.newWorld(world_id, template)
									except TemplateDoesNotExist:
										print ("Template '%s' does not exist." % template)
									self.server.loadWorld("mapdata/worlds/%s" % world_id, world_id)
									self.server.worlds[world_id].all_write = False
									if len(message) < 4:
										self.client.sendServerMessage("World '%s' made and booted." % world_id)
							elif message[0] == ("me"):
								if len(message) == 1:
									print ("Please type an action.")
								else:
									self.server.queue.put((self, TASK_ACTION, (1, "&2", "Console", " ".join(message[1:]))))
							elif message[0] == ("srb"):
								if len(message) == 1:
									self.server.queue.put((self, TASK_SERVERURGENTMESSAGE, ("[Server Reboot] Be back very soon.")))
								else:
									self.server.queue.put((self, TASK_SERVERURGENTMESSAGE, ("[Server Reboot] Be back very soon: "+(" ".join(message[1:])))))
							elif message[0] == ("srs"):
								if len(message) == 1:
									self.server.queue.put((self, TASK_SERVERURGENTMESSAGE, ("[Server Shutdown] See you later.")))
								else:
									self.server.queue.put((self, TASK_SERVERURGENTMESSAGE, ("[Server Shutdown] See you later: "+(" ".join(message[1:])))))
							elif message[0] == ("help"):
								print ("Whispers: @username message")
								print ("WorldChat: !worldname message")
								print ("StaffChat: #message")
								print ("Commands: /cmdlist")
							elif message[0] == ("cmdlist"):
								print ("about boot ban cmdlist cpr derank irc_cpr help kick me new pll plr plu rank say shutdown spec srb srs u")
							elif message[0] == ("about"):
								print ("About The Server")
								print ("Powered by blockBox %s - http://blockbox.hk-diy.net/"% VERSION )
								print ("Name: "+self.server.server_name)
								try:
									print ("URL: "+self.server.heartbeat.url)
								except:
									print ("URL: N/A (minecraft.net is probably offline)")
							elif message[0] == ("say"):
								if len(message) == 1:
									print ("Please type a message.")
								else:
									self.server.queue.put((self, TASK_SERVERMESSAGE, ("[MSG] "+(" ".join(message[1:])))))
							elif message[0] == ("gc"):
								#ManualGarbageMe
								count = gc.collect()
								self.logger.info("%i garbage objects collected, %i could not be collected." % (count, len(gc.garbage)))
							elif message[0] == ("u"):
								if len(message) == 1:
									print ("Please type a message.")
								else:
									self.server.queue.put((self, TASK_SERVERURGENTMESSAGE, "[URGENT] "+(" ".join(message[1:]))))
							elif message[0] == ("plr"):
								if len(message) == 1:
									print ("Please provide a plugin name.")
								else:
									try:
										self.server.unloadPlugin(message[1])
										self.server.loadPlugin(message[1])
									except ImportError:
										print ("No such plugin '%s'." % message[1])
									else:
										print ("Plugin '%s' reloaded." % message[1])
							elif message[0] == ("plu"):
								if len(message) == 1:
									print ("Please provide a plugin name.")
								else:
									try:
										self.server.unloadPlugin(message[1])
									except KeyError:
										print ("No such plugin '%s'." % message[1])
									else:
										print ("Plugin '%s' unloaded." % message[1])
							elif message[0] == ("pll"):
								if len(message) == 1:
									print ("Please provide a plugin name.")
								else:
									try:
										self.server.loadPlugin(message[1])
									except ImportError:
										print ("No such plugin '%s'." % message[1])
									else:
										print ("Plugin '%s' loaded." % message[1])
							elif message[0] == ("cpr"):
								self.server.heartbeat.turl()
							elif message[0] == ("irc_cpr"):
								self.server.irc_relay.quit("Reloading the IRC Bot...")
								self.server.irc_relay = None
								self.server.irc_relay = ChatBotFactory(self.server)
								reactor.connectTCP(self.server.conf_irc.get("irc", "server"), self.server.conf_irc.getint("irc", "port"), self.server.irc_relay)
							#elif message[0] == ("irc_unload"):
							#	if not self.irc_relay:
							#		print ("IRC bot is not loaded.")
							#	else:
							#		self.server.irc_relay.connectionLost("IRC Bot disabled.")
							#		self.server.irc_relay = None
							#		print ("IRC Bot unloaded.")
							#elif message[0] == ("irc_load"):
							#	if self.irc_relay:
							#		print ("IRC bot is already loaded. If it failed please use /irc_cpr!")
							#	else:
							#		self.server.irc_relay = ChatBotFactory(self.server)
							#		reactor.connectTCP(self.server.conf_irc.get("irc", "server"), self.server.conf_irc.getint("irc", "port"), self.server.irc_relay)
							#		print ("IRC Bot loaded.")
							else:
								print ("There is no " + message[0] + " command.")
						elif message.startswith("@"):
							# It's a whisper
							try:
								username, text = message[1:].strip().split(" ", 1)
							except ValueError:
								print ("Please include a username and a message to send.")
							else:
								username = username.lower()
								if username in self.server.usernames:
									self.server.usernames[username].sendWhisper("Console", text)
									self.logger.info("@Console to "+username+": "+text)
									self.whisperlog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" | @Console to "+username+": "+text+"\n")
									self.whisperlog.flush()
								else:
									print ("%s is currently offline." % username)
						elif message.startswith("!"):
							#It's a world message.
							if len(message) == 1:
								print ("Please include a message to send.")
							else:
								try:
								   world, out = message[1:len(message)-1].split(" ")
								   text = COLOUR_YELLOW+"!"+COLOUR_DARKGREEN+"Console:"+COLOUR_WHITE+" "+out
								except ValueError:
									print ("Please include a message to send.")
								else:
									if world in self.server.worlds:
										self.server.queue.put ((self.server.worlds[world],TASK_WORLDMESSAGE,(255, self.server.worlds[world], text),))
										if self.server.irc_relay:
											self.server.irc_relay.sendServerMessage("!Console in "+str(world)+": "+out)
										self.logger.info("!Console in "+str(self.server.worlds[world].id)+": "+out)
										self.wclog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" | !Console in "+str(self.server.worlds[world].id)+": "+out+"\n")
										self.wclog.flush()
									else:
										print ("That world does not exist. Try !world message")
						elif message.startswith("#"):
							#It's an staff-only message.
							if len(message) <= 2:
								print ("Please include a message to send.")
							else:
								try:
									text = message[1:]
								except ValueError:
									self.server.queue.put((self, TASK_MESSAGE, (0, COLOUR_DARKGREEN,"Console", message)))
								else:
									text = text[:len(text)-1]
									self.server.queue.put((self, TASK_STAFFMESSAGE, (0, COLOUR_DARKGREEN,"Console", text,False)))
									self.logger.info("#Console: "+text)
									self.adlog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" | #Console: "+text+"\n")
									self.adlog.flush()
						else:
							self.server.queue.put((self, TASK_MESSAGE, (0, COLOUR_DARKGREEN,"Console", message[0:len(message)-1])))
							#self.server.queue.put((self, TASK_MESSAGE, (255, "", COLOUR_DARKGREEN+"Console", message[0:len(message)-1])))
			except:
				print traceback.format_exc()
				self.logger.error(traceback.format_exc())
		finally:
			time.sleep(0.1)