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

import traceback
from lib import simplejson
from lib.twisted.protocols.basic import LineReceiver
from lib.twisted.internet.protocol import Factory
from myne.logger import ColoredLogger

class APIProtocol(LineReceiver):
    """
    Protocol for dealing with API requests.
    """
    def connectionMade(self):
        self.factory, self.api_factory = self.factory.main_factory, self.factory
        peer = self.transport.getPeer()
        self.api_factory.logger.info("Connection made from %s:%s" % (peer.host, peer.port))
    
    def connectionLost(self, reason):
        peer = self.transport.getPeer()
        self.api_factory.logger.info("Connection lost from %s:%s" % (peer.host, peer.port))
    
    def sendJson(self, data):
        self.sendLine(simplejson.dumps(data))
    
    def lineReceived(self, line):
        data = simplejson.loads(line)
        peer = self.transport.getPeer()
        if data['password'] != self.factory.api_password:
            self.sendJson({"error": "invalid password"})
            self.api_factory.logger.info("Invalid password %s (%s:%s)" % (data, peer.host, peer.port))
        else:
            command = data['command'].lower()
            try:
                func = getattr(self, "command%s" % command.title())
            except AttributeError:
                self.sendLine("ERROR: Unknown command '%s'" % command)
            else:
                self.api_factory.logger.info("%s %s (%s:%s)" % (command.upper(), data, peer.host, peer.port))
                try:
                    func(data)
                except Exception, e:
                    self.sendLine("ERROR: %s" % e)
                    traceback.print_exc()
    
    def commandIrcInfo(self, data):
        if self.factory.config.getboolean("irc", "use_irc"):
            self.sendJson({"irc": [self.factory.config.get("irc", "server"), self.factory.config.getint("irc", "port"), self.factory.irc_channel]})
        else:
            self.sendLine("ERROR: No IRC information for server.")
    
    def commandUsers(self, data):
        self.sendJson({"users": list(self.factory.usernames.keys())})
        
    def commandOwner(self, data):
        self.sendJson({"owner": list(self.factory.owner)})
                
    def commandDirectors(self, data):
        self.sendJson({"directors": list(self.factory.directors)})

    def commandAdmins(self, data):
        self.sendJson({"admins": list(self.factory.admins)})

    def commandMods(self, data):
        self.sendJson({"mods": list(self.factory.mods)})
                
    def commandSpecs(self, data):
        self.sendJson({"specs": list(self.factory.spectators)})
    
    def commandWorlds(self, data):
        self.sendJson({"worlds": list(self.factory.worlds.keys())})
    
    def commandUserworlds(self, data):
        self.sendJson({"worlds": [
            (world.id, [client.username for client in world.clients if client.username], {
                "id": world.id,
                "ops": list(world.ops),
                "writers": list(world.writers),
                "private": world.private,
                "archive": world.is_archive,
                "locked": not world.all_write,
                "physics": world.physics,
            })
            for world in self.factory.worlds.values()
        ]})
    
    def commandWorldinfo(self, data):
        world = self.factory.worlds[data['world_id']]
        self.sendJson({
            "id": world.id,
            "ops": list(world.ops),
            "writers": list(world.writers),
            "private": world.private,
            "archive": world.is_archive,
            "locked": not world.all_write,
            "physics": world.physics,
        })

class APIFactory(Factory):
    protocol = APIProtocol
    
    def __init__(self, main_factory):
        self.main_factory = main_factory
        self.logger = ColoredLogger("API")

