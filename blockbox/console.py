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

    def __init__(self, factory):
        threading.Thread.__init__(self)
        self.factory = factory
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
                    if len(line) > 1:
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
                            print("You cannot use a color at the end of a message.")
                            return
                        if message.startswith("/"):
                            message = message.split(" ")
                            message[0] = message[0][1:]
                            message[len(message)-1] = message[len(message)-1][:len(message[len(message)-1])-1]
                            # It's a command
                            if message[0] == "kick":
                                if len(message) == 1:
                                    print("Please specify a username.")
                                else:
                                    if message[1].lower() in self.factory.usernames:
                                        if message[2:]:
                                            self.factory.usernames[message[1].lower()].sendError("You were kicked by the console: %s" % " ".join(message[2:]))
                                        else:
                                            self.factory.usernames[message[1].lower()].sendError("You were kicked by the console!")
                                        print("%s has been kicked from the server." % message[1])
                                        continue
                                    else:
                                        print("User %s is not online." % message[1])
                                        continue
                            elif message[0] == "ban":
                                if len(message) == 1:
                                    print("Please specify a username.")
                                else:
                                    username = message[1]
                                    if self.factory.isBanned(username):
                                        print("%s is already banned." % username)
                                    else:
                                        if len(message) < 2:
                                            print("Please give a reason.")
                                        else:
                                            self.factory.addBan(username, " ".join(message[2:]))
                                            if username in self.factory.usernames:
                                                self.factory.usernames[username].sendError("You got banned!")
                                            print("%s has been banned." % username)
                            elif message[0] == "banb":
                                if len(message) == 1:
                                    print("Please specify a username.")
                                else:
                                    username = message[1]
                                    if self.factory.isBanned(username):
                                        print("%s is already banned." % username)
                                    else:
                                        if len(message) < 2:
                                            print("Please give a reason.")
                                        else:
                                            self.factory.addBan(username, " ".join(message[2:]))
                                            if username in self.factory.usernames:
                                                ip = self.factory.usernames[username].transport.getPeer().host
                                            else:
                                                # Check persist
                                                with Persist(message[1]) as p:
                                                    ip = p.string("main", "ip", None)
                                                    if ip == None:
                                                        print("Warning: %s has never come on the server, therefore no IP record of that user." % username)
                                                        continue
                                            self.factory.addIpBan(ip, " ".join(message[2:]))
                                            if username in self.factory.usernames:
                                                self.factory.usernames[username].sendError("You got banned!")
                                                print("%s has been IPBanned." % ip)
                                            print("%s has been banned." % username)
                            elif message[0] == "rank":
                                if len(message) == 1:
                                    print ("Please specify a username.")
                                else:
                                    try:
                                        print Rank(self, message, 'console', True, self.factory)
                                    except:
                                        print ("You must specify a rank and username.")
                            elif message[0] == "derank":
                                if len(message) == 1:
                                    print ("Please specify a username.")
                                else:
                                    try:
                                        print DeRank(self, message, 'console', True, self.factory)
                                    except:
                                        print ("You must specify a rank and username.")
                            elif message[0] == "spec":
                                if len(message) == 1:
                                    print ("Please specify a username.")
                                else:
                                    try:
                                        print Spec(self, message[1], 'console', True, self.factory)
                                    except:
                                        print ("Please specify a username.")
                            elif message[0] == "despec":
                                if len(message) == 1:
                                    print ("Please specify a username.")
                                else:
                                    try:
                                        print DeSpec(self, message[1], 'console', True, self.factory)
                                    except:
                                        print ("Please specify a username.")
                            elif message[0] == ("boot"):
                                try:
                                    world = str(message[1]).lower()
                                except:
                                    print("Please specify a worldname.")
                                    continue
                                try:
                                    self.factory.loadWorld("mapdata/worlds/%s" % world, world)
                                except AssertionError:
                                    print("World %s does not exist." % world)
                                    continue
                                print("World %s booted." % world)
                            elif message[0] == ("shutdown"):
                                try:
                                    world = str(message[1]).lower()
                                except:
                                    print("Please specify a worldname.")
                                    continue
                                try:
                                    self.factory.unloadWorld(world)
                                except KeyError:
                                    print("World %s does not exist." % world)
                                    continue
                                print("World %s has been shut down." % world)
                            elif message[0] == ("new"):
                                if len(message) == 1:
                                    print("Please specify a new worldname.")
                                elif self.factory.world_exists(message[1]):
                                    print("World name in use.")
                                else:
                                    if len(message) == 2:
                                        template = "default"
                                    elif len(message) == 3 or len(message) == 4:
                                        template = message[2]
                                    world_id = message[1].lower()
                                    response = self.factory.newWorld(world_id, template)
                                    if not response:
                                        print("Template '%s' does not exist." % template)
                                        continue
                                    self.factory.loadWorld("mapdata/worlds/%s" % world_id, world_id)
                                    self.factory.worlds[world_id].all_write = False
                                    if len(message) < 4:
                                        print("World '%s' made and booted." % world_id)
                            elif message[0] == ("me"):
                                if len(message) == 1:
                                    print("Please type an action.")
                                else:
                                    self.factory.queue.put((self, TASK_ACTION, (1, "&2", "Console", " ".join(message[1:]))))
                            elif message[0] == ("srb"):
                                if len(message) == 1:
                                    self.factory.queue.put((self, TASK_SERVERURGENTMESSAGE, ("[Server Reboot] Be back very soon.")))
                                else:
                                    self.factory.queue.put((self, TASK_SERVERURGENTMESSAGE, ("[Server Reboot] Be back very soon: %s" % (" ".join(message[1:])))))
                            elif message[0] == ("srs"):
                                if len(message) == 1:
                                    self.factory.queue.put((self, TASK_SERVERURGENTMESSAGE, ("[Server Shutdown] See you later.")))
                                else:
                                    self.factory.queue.put((self, TASK_SERVERURGENTMESSAGE, ("[Server Shutdown] See you later: %s" % (" ".join(message[1:])))))
                            elif message[0] == ("help"):
                                print("Whispers: @username message")
                                print("WorldChat: !worldname message")
                                print("StaffChat: #message")
                                print("Commands: /cmdlist")
                            elif message[0] == ("cmdlist"):
                                print("about boot ban cmdlist cpr derank irc_cpr help kick me new pll plr plu rank say shutdown srb srs u")
                            elif message[0] == ("about"):
                                print("About The Server")
                                print("Powered by blockBox %s - http://blockbox.hk-diy.net/" % VERSION )
                                print("Name: %s" % self.factory.config["server_name"])
                                try:
                                    print("URL: "+self.factory.heartbeat.url)
                                except:
                                    print("URL: N/A (minecraft.net is probably offline)")
                            elif message[0] == ("say"):
                                if len(message) == 1:
                                    print("Please type a message.")
                                else:
                                    self.factory.queue.put((self, TASK_SERVERMESSAGE, ("[MSG] %s" % (" ".join(message[1:])))))
                            elif message[0] == ("gc"):
                                # ManualGarbageMe
                                count = gc.collect()
                                self.logger.info("%i garbage objects collected, %i could not be collected." % (count, len(gc.garbage)))
                            elif message[0] == ("u"):
                                if len(message) == 1:
                                    print("Please type a message.")
                                else:
                                    self.factory.queue.put((self, TASK_SERVERURGENTMESSAGE, "[URGENT] %s" % (" ".join(message[1:]))))
                            elif message[0] == ("plr"):
                                if len(message) == 1:
                                    print("Please provide a plugin name.")
                                else:
                                    try:
                                        self.factory.unloadPlugin(message[1])
                                        self.factory.loadPlugin(message[1])
                                    except ImportError:
                                        print("No such plugin '%s'." % message[1])
                                    else:
                                        print("Plugin '%s' reloaded." % message[1])
                            elif message[0] == ("plu"):
                                if len(message) == 1:
                                    print("Please provide a plugin name.")
                                else:
                                    try:
                                        self.factory.unloadPlugin(message[1])
                                    except KeyError:
                                        print("No such plugin '%s'." % message[1])
                                    else:
                                        print("Plugin '%s' unloaded." % message[1])
                            elif message[0] == ("pll"):
                                if len(message) == 1:
                                    print("Please provide a plugin name.")
                                else:
                                    try:
                                        self.factory.loadPlugin(message[1])
                                    except ImportError:
                                        print("No such plugin '%s'." % message[1])
                                    else:
                                        print("Plugin '%s' loaded." % message[1])
                            elif message[0] == ("cpr"):
                                self.factory.heartbeat.turl()
                            elif message[0] == ("irc_cpr"):
                                self.factory.irc_relay.quit("Reloading the IRC Bot...")
                                self.factory.irc_relay = None
                                self.factory.irc_relay = ChatBotFactory(self.factory)
                                reactor.connectTCP(self.factory.conf_irc.get("irc", "server"), self.factory.conf_irc.getint("irc", "port"), self.factory.irc_relay)
                            #elif message[0] == ("irc_unload"):
                            #    if not self.irc_relay:
                            #        print("IRC bot is not loaded.")
                            #    else:
                            #        self.factory.irc_relay.connectionLost("IRC Bot disabled.")
                            #        self.factory.irc_relay = None
                            #        print("IRC Bot unloaded.")
                            #elif message[0] == ("irc_load"):
                            #    if self.irc_relay:
                            #        print("IRC bot is already loaded. If it failed please use /irc_cpr!")
                            #    else:
                            #        self.factory.irc_relay = ChatBotFactory(self.factory)
                            #        reactor.connectTCP(self.factory.conf_irc.get("irc", "server"), self.factory.conf_irc.getint("irc", "port"), self.factory.irc_relay)
                            #        print("IRC Bot loaded.")
                            else:
                                print("There is no %s command." % message[0])
                        elif message.startswith("@"):
                            # It's a whisper
                            try:
                                username, text = message[1:].strip().split(" ", 1)
                            except ValueError:
                                print("Please include a username and a message to send.")
                            else:
                                username = username.lower()
                                if username in self.factory.usernames:
                                    self.factory.usernames[username].sendWhisper("Console", text)
                                    self.logger.info("@Console to "+username+": "+text)
                                    self.whisperlog.write("%s | @Console to %s: %s\n" % ((datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")), username, text))
                                    self.whisperlog.flush()
                                else:
                                    print("%s is currently offline." % username)
                        elif message.startswith("!"):
                            #It's a world message.
                            if len(message) == 1:
                                print("Please include a message to send.")
                            else:
                                try:
                                    world, out = message[1:len(message)-1].split(" ")
                                    text = "%s!%sConsole: %s" % (COLOUR_YELLOW, COLOUR_DARKGREEN, COLOUR_WHITE, out)
                                except ValueError:
                                    print("Please include a message to send.")
                                else:
                                    if world in self.factory.worlds:
                                        self.factory.queue.put((self.factory.worlds[world], TASK_WORLDMESSAGE, (255, self.factory.worlds[world], text),))
                                        if self.factory.irc_relay:
                                            self.factory.irc_relay.sendServerMessage("!Console in "+str(world)+": "+out)
                                        self.logger.info("!Console in "+str(self.factory.worlds[world].id)+": "+out)
                                        self.wclog.write("%s | !Console in %s: %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), str(self.factory.worlds[world].id), out))
                                        self.wclog.flush()
                                    else:
                                        print("That world does not exist. Try !world message")
                        elif message.startswith("#"):
                            #It's an staff-only message.
                            if len(message) <= 2:
                                print("Please include a message to send.")
                            else:
                                try:
                                    text = message[1:]
                                except ValueError:
                                    self.factory.queue.put((self, TASK_MESSAGE, (0, COLOUR_DARKGREEN,"Console", message)))
                                else:
                                    text = text[:len(text)-1]
                                    self.factory.queue.put((self, TASK_STAFFMESSAGE, (0, COLOUR_DARKGREEN,"Console", text, False)))
                                    self.logger.info("#Console: %s" % text)
                                    self.adlog.write("%s | #Console: %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), text))
                                    self.adlog.flush()
                        else:
                            self.factory.queue.put((self, TASK_MESSAGE, (0, COLOUR_DARKGREEN,"Console", message[0:len(message)-1])))
                            #self.factory.queue.put((self, TASK_MESSAGE, (255, "", COLOUR_DARKGREEN+"Console", message[0:len(message)-1])))
            except:
                print traceback.format_exc()
                self.logger.error(traceback.format_exc())
        finally:
            time.sleep(0.1)