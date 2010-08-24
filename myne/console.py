#    iCraft is Copyright 2010 both
#
#    The Archives team:
#                   <Adam Guy> adam@adam-guy.com AKA "Adam01"
#                   <Andrew Godwin> andrew@aeracode.org AKA "Aera"
#                   <Dylan Lukes> lukes.dylan@gmail.com AKA "revenant"
#                   <Gareth Coles> colesgareth2@hotmail.com AKA "gdude2002"
#
#    And,
#
#    The iCraft team:
#                   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#                   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#                   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#                   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#                   <James Kirslis> james@helplarge.com AKA "iKJames"
#                   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#                   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
#                   <Nick Tolrud> ntolrud@yahoo.com AKA "ntfwc"
#                   <Noel Benzinger> ronnygmod@gmail.com AKA "Dwarfy"
#                   <Randy Lyne> qcksilverdragon@gmail.com AKA "goober"
#                   <Willem van der Ploeg> willempieeploeg@live.nl AKA "willempiee"
#
#    iCraft is licensed under the Creative Commons
#    Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
#    To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#    Or, send a letter to Creative Commons, 171 2nd Street,
#    Suite 300, San Francisco, California, 94105, USA.

import threading
import traceback, sys
import time
import datetime
from myne.constants import *
from myne.logger import ColoredLogger
from globals import *

class StdinPlugin(threading.Thread):

    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server
        self.stop = False
        self.whisperlog = open("logs/server.log", "a")
        self.whisperlog = open("logs/whisper.log", "a")
        self.wclog = open("logs/server.log", "a")
        self.wclog = open("logs/staff.log", "a")
        self.adlog = open("logs/server.log", "a")
        self.adlog = open("logs/world.log", "a")
        self.logger = ColoredLogger("Console")

    def run(self):
        try:
            try:
                while not self.stop:
                    line = sys.stdin.readline()
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
                        if message[len(message)-3] == "&":
                            print "You can not use a color at the end of a message"
                            return
                        if message.startswith("/"):
                            message = message.split(" ")
                            message[0] = message[0][1:]
                            message[len(message)-1] = message[len(message)-1][:len(message[len(message)-1])-1]
                            # It's a command
                            #kick*, ban*, boot*, shutdown*, new*, about*, plr, plu, pll, u, say*, me*, srb*,
                            if message[0] == "kick":
                                for client in self.server.clients.values():
                                    if client.username==message[1]:
                                        client.sendError("You were kicked!")
                                        print message[1]+" has been kicked from the server."
                                    else:
                                        print "User "+str(message[1])+" is not online."
                            elif message[0] == "ban":
                                username = message[1]
                                if self.server.isBanned(username):
                                    print "%s is already Banned." % username
                                else:
                                    if not len(message)>2:
                                        print "Please give a reason."
                                    else:
                                        self.server.addBan(username, " ".join(message[2:]))
                                        if username in self.server.usernames:
                                            ip = self.server.usernames[username].transport.getPeer().host
                                            self.server.usernames[username].sendError("You got Banned!")
                                            self.server.addIpBan(ip, " ".join(message[2:]))
                                            if username in self.server.usernames:
                                                self.server.usernames[username].sendError("You got Banned!")
                                            print "%s has been IPBanned." % ip
                                        print "%s has been Banned." % username
                            elif message[0] == "rank":
                                if not message > 1:
                                    print "You must provide a username."
                                else:
                                    print Rank(self, message, False, True, self.server)
                            elif message[0] == "derank":
                                if not message > 1:
                                    print "You must provide a username."
                                else:
                                    print DeRank(self, message, False, True, self.server)
                            elif message[0] == "spec":
                                if not message > 1:
                                    print "You must provide a username."
                                else:
                                    print Spec(self, message[1], False, True, self.server)
                            elif message[0] == ("boot"):
                                world = str(message[1]).lower()
                                self.server.loadWorld("worlds/"+world, world)
                                print "World '"+world+"' booted."
                            elif message[0] == ("shutdown"):
                                world = str(message[1]).lower()
                                self.server.unloadWorld(world)
                                print "World '"+world+"' shutdown."
                            elif message[0] == ("new"):
                                if len(message) == 1:
                                    print "Please specify a new worldname."
                                elif self.server.world_exists(parts[1]):
                                    print "Worldname in use"
                                else:
                                    if len(message) == 2:
                                        template = "default"
                                    elif len(message) == 3 or len(message) == 4:
                                        template = message[2]
                                    world_id = message[1].lower()
                                    self.server.newWorld(world_id, template)
                                    self.server.loadWorld("worlds/%s" % world_id, world_id)
                                    self.server.worlds[world_id].all_write = False
                                    if len(message) < 4:
                                        self.client.sendServerMessage("World '%s' made and booted." % world_id)
                            elif message[0] == ("me"):
                                if len(message) == 1:
                                    print "Please type an action."
                                else:
                                    self.server.queue.put((self, TASK_ACTION, (1, "&d", "Console", " ".join(message[1:]))))
                            elif message[0] == ("srb"):
                                self.server.queue.put((self, TASK_SERVERURGENTMESSAGE, ("[URGENT] Server Reboot - Back in a Flash")))
                            elif message[0] == ("help"):
                                print "Commands available are: about, boot, ban, cpr, derank, kick, me, new, pll, plr, plu, rank, say, shutdown, spec, srb and u."
                                print "Chats available are: normal, whisper; @<player> <message>, world; !<world name> <message> and staff; #<message>."
                            elif message[0] == ("about"):
                                print "About The Server"
                                print ("Powered by iCraft %s - http://hlmc.net/"%VERSION)
                                print ("Name: "+self.server.server_name)
                                print ("URL: "+self.server.heartbeat.url)
                            elif message[0] == ("say"):
                                if len(message) == 1:
                                    self.client.sendServerMessage("Please type a message.")
                                else:
                                    self.server.queue.put((self, TASK_SERVERMESSAGE, ("[MSG] "+(" ".join(message[1:])))))
                            elif message[0] == ("srb"):
                                self.server.queue.put((self, TASK_SERVERURGENTMESSAGE, ("[URGENT] Server Reboot - Back in a Flash")))
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
                                    except IOError:
                                        print ("No such plugin '%s'." % message[1])
                                    else:
                                        print ("Plugin '%s' reloaded." % message[1])
                            elif message[0] == ("plu"):
                                try:
                                    self.server.unloadPlugin(message[1])
                                except IOError:
                                    print ("No such plugin '%s'." % message[1])
                                else:
                                    print ("Plugin '%s' unloaded." % message[1])
                            elif message[0] == ("pll"):
                                try:
                                    self.server.loadPlugin(message[1])
                                except IOError:
                                    print ("No such plugin '%s'." % message[1])
                                else:
                                    print ("Plugin '%s' loaded." % message[1])
                            elif message[0] == ("cpr"):
                                self.server.heartbeat.turl()
                            else:
                                print "There is no " + message[0] + " command."
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
                                    self.logger.info("Whisper to "+username+": "+text)
                                    self.whisperlog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" | WHISPER | Console to "+username+": "+text+"\n")
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
                                   text = "!"+COLOUR_DARKGREEN+"Console:"+COLOUR_WHITE+" "+out
                                except ValueError:
                                    print ("Please include a message to send.")
                                else:
                                    if world in self.server.worlds:
                                        self.server.queue.put ((self.server.worlds[world],TASK_WORLDMESSAGE,(255, self.server.worlds[world], text),))
                                        self.logger.info("WorldChat on '"+str(self.server.worlds[world].id)+"': "+out)
                                        self.wclog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" | WORLD | Console in "+str(self.server.worlds[world].id)+": "+out+"\n")
                                        self.wclog.flush()
                                    else:
                                        print "That world does not exist. Try !world message"
                        elif message.startswith("#"):
                            #It's an staff-only message.
                            if len(message) == 1:
                                print ("Please include a message to send.")
                            else:
                                try:
                                    text = message[1:]
                                except ValueError:
                                    self.server.queue.put((self, TASK_MESSAGE, (0, COLOUR_DARKGREEN,"Console", message)))
                                else:
                                    self.server.queue.put((self, TASK_STAFFMESSAGE, ("#%s%s: %s%s" % (COLOUR_DARKGREEN, "Console", COLOUR_GREEN, text))))
                                    self.logger.info("StaffChat: "+text)
                                    self.adlog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" | STAFF | Console: "+text+"\n")
                                    self.adlog.flush()
                        else:
                            self.server.queue.put((self, TASK_MESSAGE, (255, "", "Console", message[0:len(message)-1])))
            except:
                self.logger.error(traceback.format_exc())
        finally:
            time.sleep(0.1)
