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

import urllib
import time
import logging
import os
import re
import sys
import datetime
import shutil
import traceback
import pickle
import threading
import socket
import gc
import hashlib
import random
from myne.console import StdinPlugin
from Queue import Queue, Empty
from twisted.internet.protocol import Factory
from twisted.internet import reactor
from ConfigParser import RawConfigParser as ConfigParser
from myne.protocol import MyneServerProtocol
from myne.world import World
from myne.irc_client import ChatBotFactory
from myne.constants import *
from myne.plugins import *
from myne.timer import ResettableTimer

class Heartbeat(object):
    """
Deals with registering with the Minecraft main server every so often.
The Salt is also used to help verify users' identities.
    """

    def __init__(self, factory):
        self.factory = factory
        self.turl()

    def turl(self):
        try:
            threading.Thread(target=self.get_url).start()
        except:
            logging.log(logging.ERROR, traceback.format_exc())
            reactor.callLater(1, self.turl)

    def get_url(self):
        try:
            try:
                self.factory.last_heartbeat = time.time()
                fh = urllib.urlopen("http://www.minecraft.net/heartbeat.jsp", urllib.urlencode({
                "port": self.factory.config.getint("network", "port"),
                "users": len(self.factory.clients),
                "max": self.factory.max_clients,
                "name": self.factory.server_name,
                "public": self.factory.public,
                "version": 7,
                "salt": self.factory.salt,
                }))
                self.url = fh.read().strip()
                if self.factory.console_delay == self.factory.delay_count:
                    logging.log(logging.INFO, "Heartbeat Sent. Your URL: %s" % self.url)
                    logging.log(logging.INFO, "URL saved to url.txt")
                open('url.txt', 'w').write(self.url)
                if not self.factory.console.is_alive():
                    self.factory.console.run()
            except:
                logging.log(logging.ERROR, traceback.format_exc())
        except:
            logging.log(logging.ERROR, traceback.format_exc())
        finally:
            reactor.callLater(60, self.turl)

class MyneFactory(Factory):
    """
    Factory that deals with the general world actions and cross-player comms.
    """
    protocol = MyneServerProtocol

    def __init__(self):
        self.ServerVars = dict()
        self.specs = ConfigParser()
        self.last_heartbeat = time.time()
        self.lastseen = ConfigParser()
        self.config = ConfigParser()
        self.wordfilter = ConfigParser()
        self.save_count = 1
        self.delay_count = 1
        self.config.read("server.conf")
        self.saving = False
        self.max_clients = self.config.getint("main", "max_clients")
        self.server_name = self.config.get("main", "name")
        self.server_message = self.config.get("main", "description")
        self.initial_greeting = self.config.get("main", "greeting").replace("\\n", "\n")
        self.public = self.config.getboolean("main", "public")
        self.enable_archives = self.config.getboolean("worlds", "enable_archives")
        self.duplicate_logins = self.config.getboolean("options", "duplicate_logins")
        self.verify_names = True #DON'T TURN THIS OFF UNLESS YOU KNOW WHAT YOU'RE DOING. THIS VERIFIES THE NAMES ON THE SERVER TO SEE IF THEY ARE WHO THEY SAY THEY ARE, TURNING IT OFF CAN BE DANGEROUS AND A BIG SECURITY RISK. YOU WILL NOT BE SUPPORTED BY THE ICRAFT TEAM IF THIS IS TURNED OFF.
        self.asd_delay = self.config.getint("worlds", "asd_delay")
        self.control_password = self.config.get("network", "control_password")
        self.physics_limit = self.config.getint("options", "physics_limit")
        self.console_delay = self.config.getint("options", "console_delay")
        self.info_url = self.config.get("info", "info_url")
        self.default_name = self.config.get("worlds", "default_name")
        self.default_backup = self.config.get("worlds", "default_backup")
        self.owner = self.config.get("info", "owner").lower()
        self.backup_freq = self.config.getint("backup", "backup_freq")
        self.backup_default = self.config.getboolean("backup", "backup_default")
        self.backup_max = self.config.getint("backup", "backup_max")
        self.backup_auto = self.config.getboolean("backup", "backup_auto")
        if self.backup_auto:
            reactor.callLater(float(self.backup_freq * 60),self.AutoBackup)
        # Parse IRC section
        if  self.config.getboolean("irc", "use_irc"):
            self.irc_nick = self.config.get("irc", "nick")
            self.irc_pass = self.config.get("irc", "password")
            self.irc_channel = self.config.get("irc", "channel")
            self.irc_cmdlogs = self.config.getboolean("irc", "cmdlogs")
            self.irc_relay = ChatBotFactory(self)
            reactor.connectTCP(self.config.get("irc", "server"), self.config.getint("irc", "port"), self.irc_relay)
        else:
            self.irc_relay = None
        self.default_loaded = False
        #WORD FILTER LOL
        self.wordfilter.read("wordfilter.conf")
        self.filter = []
        number = int(self.wordfilter.get("filter","count"))
        for x in range(number):
            self.filter = self.filter + [[self.wordfilter.get("filter","s"+str(x)),self.wordfilter.get("filter","r"+str(x))]]
        # Salt, for the heartbeat server/verify-names
        self.salt = hashlib.md5(hashlib.md5(str(random.getrandbits(128))).digest()).hexdigest()[-32:].strip("0")
        # Load up the plugins specified
        plugins = self.config.options("plugins")
        logging.log(logging.INFO, "Loading plugins...")
        load_plugins(plugins)
        # Open the chat log, ready for appending
        self.chatlog = open("logs/server.log", "a")
        self.chatlog = open("logs/chat.log", "a")
        # Create a default world, if there isn't one.
        if not os.path.isdir("worlds/%s" % self.default_name):
            logging.log(logging.INFO, "Generating %s world..." % self.default_name)
            sx, sy, sz = 64, 64, 64
            grass_to = (sy // 2)
            world = World.create(
                "worlds/%s" % self.default_name,
                sx, sy, sz, # Size
                sx//2,grass_to+2, sz//2, 0, # Spawn
                ([BLOCK_DIRT]*(grass_to-1) + [BLOCK_GRASS] + [BLOCK_AIR]*(sy-grass_to)) # Levels
            )
            logging.log(logging.INFO, "Generated.")
        # Initialise internal datastructures
        self.worlds = {}
        self.directors = set()
        self.admins = set()
        self.mods = set()
        self.members = set()
        self.spectators = set()
        self.silenced = set()
        self.banned = {}
        self.ipbanned = {}
        self.lastseen = {}
        # Load up the contents of those.
        self.loadMeta()
        # Set up a few more things.
        self.queue = Queue()
        self.clients = {}
        self.usernames = {}
        self.console = StdinPlugin(self)
        self.console.start()
        self.heartbeat = Heartbeat(self)
        # Boot worlds that got loaded
        for world in self.worlds:
            self.loadWorld("worlds/%s" % world, world)
        # Set up tasks to run during execution
        reactor.callLater(0.1, self.sendMessages)
        reactor.callLater(1, self.printInfo)
        # Initial startup is instant, but it updates every 10 minutes.
        self.world_save_stack = []
        reactor.callLater(60, self.saveWorlds)
        if self.enable_archives:
            self.loadPlugin('archives')
            reactor.callLater(1, self.loadArchives)

    def loadMeta(self):
        "Loads the 'meta' - variables that change with the server (worlds, admins, etc.)"
        config = ConfigParser()
        config.read("server.meta")
        specs = ConfigParser()
        specs.read("spectators.meta")
        lastseen = ConfigParser()
        lastseen.read("lastseen.meta")
        # Read in the worlds
        if config.has_section("worlds"):
            for name in config.options("worlds"):
                self.worlds[name] = None
                if name is self.default_name:
                    self.default_loaded = True
        else:
            self.worlds[self.default_name] = None
        if not self.default_loaded:
            self.worlds[self.default_name] = None
        # Read in the admins
        if config.has_section("admins"):
            for name in config.options("admins"):
                self.admins.add(name)
        # Read in the mods
        if config.has_section("mods"):
            for name in config.options("mods"):
                self.mods.add(name)
        if config.has_section("members"):
            for name in config.options("members"):
                self.members.add(name)
        # Read in the directors
        if config.has_section("directors"):
            for name in config.options("directors"):
                self.directors.add(name)
        if config.has_section("silenced"):
            for name in config.options("silenced"):
                self.silenced.add(name)
        # Read in the spectators (experimental)
        if specs.has_section("spectators"):
            for name in specs.options("spectators"):
                self.spectators.add(name)
        # Read in the bans
        if config.has_section("banned"):
            for name in config.options("banned"):
                self.banned[name] = config.get("banned", name)
        # Read in the ipbans
        if config.has_section("ipbanned"):
            for ip in config.options("ipbanned"):
                self.ipbanned[ip] = config.get("ipbanned", ip)
        # Read in the lastseen
        if lastseen.has_section("lastseen"):
            for username in lastseen.options("lastseen"):
                self.lastseen[username] = lastseen.getfloat("lastseen", username)

    def saveMeta(self):
        "Saves the server's meta back to a file."
        config = ConfigParser()
        specs = ConfigParser()
        lastseen = ConfigParser()
        # Make the sections
        config.add_section("worlds")
        config.add_section("directors")
        config.add_section("admins")
        config.add_section("mods")
        config.add_section("members")
        config.add_section("silenced")
        config.add_section("banned")
        config.add_section("ipbanned")
        specs.add_section("spectators")
        lastseen.add_section("lastseen")
        # Write out things
        for world in self.worlds:
            config.set("worlds", world, "true")
        for director in self.directors:
            config.set("directors", director, "true")
        for admin in self.admins:
            config.set("admins", admin, "true")
        for mod in self.mods:
            config.set("mods", mod, "true")
        for member in self.members:
            config.set("members", member, "true")
        for ban, reason in self.banned.items():
            config.set("banned", ban, reason)
        for spectator in self.spectators:
            specs.set("spectators", spectator, "true")
        for silence in self.silenced:
            config.set("silenced", silence, "true")
        for ipban, reason in self.ipbanned.items():
            config.set("ipbanned", ipban, reason)
        for username, ls in self.lastseen.items():
            lastseen.set("lastseen", username, str(ls))
        fp = open("server.meta", "w")
        config.write(fp)
        fp.close()
        fp = open("spectators.meta", "w")
        specs.write(fp)
        fp.close()
        fp = open("lastseen.meta", "w")
        lastseen.write(fp)
        fp.close()

    def printInfo(self):
        if self.console_delay == self.delay_count:
            logging.log(logging.INFO, "There are %s Players on the server" % len(self.clients))
            for key in self.worlds:
                logging.log(logging.INFO, "%s: %s" % (key, ", ".join(str(c.username) for c in self.worlds[key].clients)))
            self.delay_count=1
        else:
            self.delay_count+=1
        gc.collect()
        if (time.time() - self.last_heartbeat) > 180:
            self.heartbeat = None
            self.heartbeat = Heartbeat(self)
        reactor.callLater(60, self.printInfo)

    def loadArchive(self, filename):
        "Boots an archive given a filename. Returns the new world ID."
        # Get an unused world name
        i = 1
        while self.world_exists("a-%i" % i):
            i += 1
        world_id = "a-%i" % i
        # Copy and boot
        self.newWorld(world_id, "../archives/%s" % filename)
        self.loadWorld("worlds/%s" % world_id, world_id)
        world = self.worlds[world_id]
        world.is_archive = True
        return world_id

    def saveWorlds(self):
        "Saves the worlds, one at a time, with a 1 second delay."
        if not self.saving:
            if not self.world_save_stack:
                self.world_save_stack = list(self.worlds)
            key = self.world_save_stack.pop()
            self.saveWorld(key)
            if not self.world_save_stack:
                reactor.callLater(60, self.saveWorlds)
                self.saveMeta()
            else:
                reactor.callLater(1, self.saveWorlds)

    def saveWorld(self, world_id,shutdown = False):
        try:
            world = self.worlds[world_id]
            world.save_meta()
            world.flush()
            if self.console_delay == self.delay_count:
                logging.log(logging.INFO,"World '%s' has been saved." % world_id)
            if self.save_count == 5:
                for client in list(list(self.worlds[world_id].clients))[:]:
                    client.sendServerMessage("World '%s' has been saved." % world_id)
                self.save_count = 1
            else:
                self.save_count += 1
            if shutdown: del self.worlds[world_id]
        except:
            logging.log(logging.INFO,"Error saving %s" % world_id)

    def claimId(self, client):
        for i in range(1, self.max_clients+1):
            if i not in self.clients:
                self.clients[i] = client
                return i
        raise ServerFull

    def releaseId(self, id):
        del self.clients[id]

    def joinWorld(self, worldid, user):
        "Makes the player join the given World."
        new_world = self.worlds[worldid]
        try:
            logging.log(logging.INFO,"%s is joining world %s" %(user.username,new_world.basename))
        except:
            logging.log(logging.INFO,"%s is joining world %s" %(user.transport.getPeer().host,new_world.basename))
        if hasattr(user, "world") and user.world:
            self.leaveWorld(user.world, user)
        user.world = new_world
        new_world.clients.add(user)
        if not worldid == self.default_name and not new_world.ASD == None:
            new_world.ASD.kill()
            new_world.ASD = None
        return new_world

    def leaveWorld(self, world, user):
        world.clients.remove(user)
        if world.autoshutdown and len(world.clients)<1:
            if world.basename == ("worlds/" + self.default_name):
                return
            else:
                if not self.asd_delay == 0:
                    world.ASD = ResettableTimer(self.asd_delay*60,1,world.unload)
                    world.ASD.start()

    def loadWorld(self, filename, world_id):
        """
        Loads the given world file under the given world ID, or a random one.
        Returns the ID of the new world.
        """
        world = self.worlds[world_id] =  World(filename)
        world.source = filename
        world.clients = set()
        world.id = world_id
        world.factory = self
        world.start()
        logging.log(logging.INFO, "World '%s' Booted." % world_id)
        return world_id

    def unloadWorld(self, world_id,ASD=False):
        """
        Unloads the given world ID.
        """
        try:
            if ASD and len(self.worlds[world_id].clients)>0:
                logging.log(logging.ERROR, "YOU HAS ERROR, REPORT THIS TO GOOBER")
                return
        except KeyError:
            return
        assert world_id != self.default_name
        if  not self.worlds[world_id].ASD == None:
            self.worlds[world_id].ASD.kill()
            self.worlds[world_id].ASD = None
        for client in list(list(self.worlds[world_id].clients))[:]:
            client.changeToWorld(self.default_name)
            client.sendServerMessage("World '%s' has been Shutdown." % world_id)
        self.worlds[world_id].stop()
        self.saveWorld(world_id,True)
        logging.log(logging.INFO, "World '%s' Shutdown." % world_id)

    def rebootworld(self, world_id):
        """
        Reboots a world in a crash case
        """
        for client in list(list(self.worlds[world_id].clients))[:]:
            if world_id == self.default_name:
                client.changeToWorld(self.factory.default_backup)
            else:
                client.changeToWorld(self.default_name)
            client.sendServerMessage("%s has been Rebooted" % world_id)
        self.worlds[world_id].stop()
        self.worlds[world_id].flush()
        self.worlds[world_id].save_meta()
        del self.worlds[world_id]
        world = self.worlds[world_id] =  World("worlds/%s" % world_id, world_id)
        world.source = "worlds/" + world_id
        world.clients = set()
        world.id = world_id
        world.factory = self
        world.start()
        logging.log(logging.INFO, "Rebooted %s" % world_id)

    def publicWorlds(self):
        """
        Returns the IDs of all public worlds
        """
        for world_id, world in self.worlds.items():
            if not world.private:
                yield world_id

    def recordPresence(self, username):
        """
        Records a sighting of 'username' in the lastseen dict.
        """
        self.lastseen[username.lower()] = time.time()

    def unloadPlugin(self, plugin_name):
        "Reloads the plugin with the given module name."
        # Unload the plugin from everywhere
        for plugin in plugins_by_module_name(plugin_name):
            if issubclass(plugin, ProtocolPlugin):
                for client in self.clients.values():
                    client.unloadPlugin(plugin)
        # Unload it
        unload_plugin(plugin_name)

    def loadPlugin(self, plugin_name):
        # Load it
        load_plugin(plugin_name)
        # Load it back into clients etc.
        for plugin in plugins_by_module_name(plugin_name):
            if issubclass(plugin, ProtocolPlugin):
                for client in self.clients.values():
                    client.loadPlugin(plugin)

    def sendMessages(self):
        "Sends all queued messages, and lets worlds recieve theirs."
        try:
            while True:
                # Get the next task
                source_client, task, data = self.queue.get_nowait()
                try:
                    if isinstance(source_client, World):
                        world = source_client
                    elif str(source_client).startswith("<StdinPlugin"):
                        world = self.worlds[self.default_name]
                    else:
                        try:
                            world = source_client.world
                        except AttributeError:
                            logging.log(logging.WARN, "Source client for message has no world. Ignoring.")
                            continue
                    # Someone built/deleted a block
                    if task is TASK_BLOCKSET:
                        # Only run it for clients who weren't the source.
                        for client in world.clients:
                            if client is not source_client:
                                client.sendBlock(*data)
                    # Someone moved
                    elif task is TASK_PLAYERPOS:
                        # Only run it for clients who weren't the source.
                        for client in world.clients:
                            if client != source_client:
                                client.sendPlayerPos(*data)
                    # Someone moved only their direction
                    elif task is TASK_PLAYERDIR:
                        # Only run it for clients who weren't the source.
                        for client in world.clients:
                            if client != source_client:
                                client.sendPlayerDir(*data)
                    # Someone spoke!
                    elif task is TASK_MESSAGE:
                        #LOL MOAR WORD FILTER
                        id, colour, username, text = data
                        text = self.messagestrip(text)
                        data = (id,colour,username,text)
                        for client in self.clients.values():
                            if (client.world.global_chat or client.world is source_client.world):
                                client.sendMessage(*data)
                        id, colour, username, text = data
                        logging.log(logging.INFO, "%s: %s" % (username, text))
                        self.chatlog.write("%s - %s: %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, text))
                        self.chatlog.flush()
                        if self.irc_relay and world:
                            self.irc_relay.sendMessage(username, text)
                    # Someone spoke!
                    elif task is TASK_IRCMESSAGE:
                        for client in self.clients.values():
                            client.sendMessage(*data)
                        id, colour, username, text = data
                        logging.log(logging.INFO, "<%s> %s" % (username, text))
                        self.chatlog.write("[%s] <%s> %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, text))
                        self.chatlog.flush()
                        if self.irc_relay and world:
                            self.irc_relay.sendMessage(username, text)
                    # Someone actioned!
                    elif task is TASK_ACTION:
                        #WORD FALTER
                        id, colour, username, text = data
                        text = self.messagestrip(text)
                        data = (id,colour,username,text)
                        for client in self.clients.values():
                            client.sendAction(*data)
                        id, colour, username, text = data
                        logging.log(logging.INFO, "ACTION - *%s %s" % (username, text))
                        self.chatlog.write("%s *%s %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, text))
                        self.chatlog.flush()
                        if self.irc_relay and world:
                            self.irc_relay.sendAction(username, text)
                    # Someone connected to the server
                    elif task is TASK_PLAYERCONNECT:
                        for client in self.usernames:
                            self.usernames[client].sendNewPlayer(*data)
                            self.usernames[client].sendServerMessage("%s has come online." % source_client.username)
                        if self.irc_relay and world:
                            self.irc_relay.sendServerMessage("%s has come online." % source_client.username)
                    # Someone joined a world!
                    elif task is TASK_NEWPLAYER:
                        for client in world.clients:
                            if client != source_client:
                                client.sendNewPlayer(*data)
                            client.sendServerMessage("%s has joined the map." % source_client.username)
                    # Someone left!
                    elif task is TASK_PLAYERLEAVE:
                        # Only run it for clients who weren't the source.
                        for client in self.clients.values():
                            client.sendPlayerLeave(*data)
                            if not source_client.username is None:
                                client.sendServerMessage("%s has gone offline." % source_client.username)
                            else:
                                source_client.log("Pinged the server.")
                        if not source_client.username is None:
                            if self.irc_relay and world:
                                self.irc_relay.sendServerMessage("%s has gone offline." % source_client.username)
                    # Someone changed worlds!
                    elif task is TASK_WORLDCHANGE:
                        # Only run it for clients who weren't the source.
                        for client in data[1].clients:
                            client.sendPlayerLeave(data[0])
                            client.sendServerMessage("%s joined '%s'" % (source_client.username, world.id))
                        if self.irc_relay and world:
                            self.irc_relay.sendServerMessage("%s joined '%s'" % (source_client.username, world.id))
                        logging.log(logging.INFO, "%s has now joined '%s'" % (source_client.username, world.id))
                    elif task == TASK_STAFFMESSAGE:
                        # Give all staff the message :D
                        id, colour, username, text = data
                        message = self.messagestrip(text);
                        for user, client in self.usernames.items():
                            if self.isMod(user):
                                client.sendMessage(100, COLOUR_YELLOW+"#"+colour, username, message, False, False)
                        if self.irc_relay and len(data)>3:
                            self.irc_relay.sendServerMessage("#"+username+": "+text,True,username)
                        logging.log(logging.INFO,"#"+username+": "+text)
                        self.adlog = open("logs/server.log", "a")
                        self.adlog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" - "+username+": "+text+"\n")
                        self.adlog.flush()
                    elif task == TASK_GLOBALMESSAGE:
                        # Give all world people the message
                        id, world, message = data
                        message = self.messagestrip(message);
                        for client in world.clients:
                            client.sendNormalMessage(message)
                    elif task == TASK_WORLDMESSAGE:
                        # Give all world people the message
                        id, world, message = data
                        for client in world.clients:
                            client.sendNormalMessage(message)
                    elif task == TASK_SERVERMESSAGE:
                        # Give all people the message
                        message = data
                        message = self.messagestrip(message);
                        for client in self.clients.values():
                            client.sendNormalMessage(COLOUR_DARKBLUE + message)
                        logging.log(logging.INFO,message)
                        if self.irc_relay and world:
                            self.irc_relay.sendServerMessage(message)
                    elif task == TASK_ONMESSAGE:
                        # Give all people the message
                        message = data
                        message = self.messagestrip(message);
                        for client in self.clients.values():
                            client.sendNormalMessage(COLOUR_YELLOW + message)
                        if self.irc_relay and world:
                            self.irc_relay.sendServerMessage(message)
                    elif task == TASK_PLAYERRESPAWN:
                        # We need to immediately respawn the player to update their nick.
                        for client in world.clients:
                            if client != source_client:
                                id, username, x, y, z, h, p = data
                                client.sendPlayerLeave(id)
                                client.sendNewPlayer(id, username, x, y, z, h, p)
                    elif task == TASK_SERVERURGENTMESSAGE:
                        # Give all people the message
                        message = data
                        for client in self.clients.values():
                            client.sendNormalMessage(COLOUR_DARKRED + message)
                        logging.log(logging.INFO,message)
                        if self.irc_relay and world:
                            self.irc_relay.sendServerMessage(message)
                    elif task == TASK_AWAYMESSAGE:
                        # Give all world people the message
                        message = data
                        for client in world.clients:
                            client.sendNormalMessage(COLOUR_DARKPURPLE + message)
                        logging.log(logging.INFO, "AWAY - %s %s" % (username, text))
                        self.chatlog.write("%s %s %s\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, text))
                        self.chatlog.flush()
                        if self.irc_relay and world:
                            self.irc_relay.sendAction(username, text)
                except Exception, e:
                    logging.log(logging.ERROR, traceback.format_exc())
        except Empty:
            pass
        # OK, now, for every world, let them read their queues
        for world in self.worlds.values():
            world.read_queue()
        # Come back soon!
        reactor.callLater(0.1, self.sendMessages)

    def newWorld(self, new_name, template="default"):
        "Creates a new world from some template."
        # Make the directory
        os.mkdir("worlds/%s" % new_name)
        # Find the template files, copy them to the new location
        for filename in ["blocks.gz", "world.meta"]:
            shutil.copyfile("templates/%s/%s" % (template, filename), "worlds/%s/%s" % (new_name, filename))

    def renameWorld(self, old_worldid, new_worldid):
        "Renames a world."
        assert old_worldid not in self.worlds
        assert self.world_exists(old_worldid)
        assert not self.world_exists(new_worldid)
        os.rename("worlds/%s" % (old_worldid), "worlds/%s" % (new_worldid))

    def numberWithPhysics(self):
        "Returns the number of worlds with physics enabled."
        return len([world for world in self.worlds.values() if world.physics])

    def isSilenced(self, username):
        return username.lower() in self.silenced

    def isOwner(self, username):
        return username.lower()==self.owner

    def isDirector(self, username):
        return username.lower() in self.directors or self.isOwner(username)

    def isAdmin(self, username):
        return username.lower() in self.admins or self.isDirector(username)

    def isMod(self, username):
        return username.lower() in self.mods or self.isAdmin(username)

    def isMember(self, username):
        #print "here" needs to check for op level also.
        return username.lower() in self.members or self.isMod(username)

    def isSpectator(self, username):
        return username.lower() in self.spectators

    def isBanned(self, username):
        return username.lower() in self.banned

    def isIpBanned(self, ip):
        return ip in self.ipbanned

    def addBan(self, username, reason):
        self.banned[username.lower()] = reason

    def removeBan(self, username):
        del self.banned[username.lower()]

    def banReason(self, username):
        return self.banned[username.lower()]

    def addIpBan(self, ip, reason):
        self.ipbanned[ip] = reason

    def removeIpBan(self, ip):
        del self.ipbanned[ip]

    def ipBanReason(self, ip):
        return self.ipbanned[ip]

    def world_exists(self, world_id):
        "Says if the world exists (even if unbooted)"
        return os.path.isdir("worlds/%s/" % world_id)

    def AutoBackup(self):
        for world in self.worlds:
            self.Backup(world)
        if self.backup_auto:
            reactor.callLater(float(self.backup_freq * 60),self.AutoBackup)

    def Backup(self,world_id):
            world_dir = ("worlds/%s/" % world_id)
            if world_id == self.default_name and not self.backup_default:
                return
            if not os.path.exists(world_dir):
                logging.log(logging.INFO, "World %s does not exist." % (world.id))
            else:
                if not os.path.exists(world_dir+"backup/"):
                    os.mkdir(world_dir+"backup/")
                folders = os.listdir(world_dir+"backup/")
                backups = list([])
                for x in folders:
                    if x.isdigit():
                        backups.append(x)
                backups.sort(lambda x, y: int(x) - int(y))

                path = os.path.join(world_dir+"backup/", "0")
                if backups:
                    path = os.path.join(world_dir+"backup/", str(int(backups[-1])+1))
                os.mkdir(path)
                shutil.copy(world_dir + "blocks.gz", path)
                try:
                    logging.log(logging.INFO, "%s's backup %s is saved." %(world_id, str(int(backups[-1])+1)))
                except:
                    logging.log(logging.INFO, "%s's backup 0 is saved.")
                if len(backups)+1 > self.backup_max:
                    for i in range(0,((len(backups)+1)-self.backup_max)):
                        shutil.rmtree(os.path.join(world_dir+"backup/", str(int(backups[i]))))

    def messagestrip(factory,message):
        strippedmessage = ""
        for x in message:
            if ord(str(x)) < 128:
                strippedmessage = strippedmessage + str(x)
        message = strippedmessage
        for x in factory.filter:
            rep = re.compile(x[0], re.IGNORECASE)
            message = rep.sub(x[1], message)
        return message   
    
    def loadArchives(self):
        self.archives = {}
        for name in os.listdir("archives/"):
            if os.path.isdir(os.path.join("archives", name)):
                for subfilename in os.listdir(os.path.join("archives", name)):
                    match = re.match(r'^(\d\d\d\d\-\d\d\-\d\d_\d?\d\_\d\d)$', subfilename)
                    if match:
                        when = match.groups()[0]
                        try:
                            when = datetime.datetime.strptime(when, "%Y-%m-%d_%H_%M")
                        except ValueError, e:
                            logging.log(logging.WARN, "Bad archive filename %s" % subfilename)
                            continue
                        if name not in self.archives:
                            self.archives[name] = {}
                        self.archives[name][when] = "%s/%s" % (name, subfilename)
        logging.log(logging.INFO, "Loaded %s discrete archives." % len(self.archives))
        reactor.callLater(300, self.loadArchives)        
