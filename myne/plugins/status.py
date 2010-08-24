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

from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class WorldUtilPlugin(ProtocolPlugin):
    
    commands = {
        "status": "commandStatus",
        "mapinfo": "commandStatus",
        "setspawn": "commandSetspawn",
        "setowner": "commandSetOwner",
        "owner": "commandSetOwner",
        "worldowner": "commandSetOwner",
        "where": "commandWhere",
        "ops": "commandOps",
        "writers": "commandWriters",
        "builders": "commandWriters",
    }

    @player_list
    @mod_only
    def commandSetOwner(self, parts, byuser, overriderank):
        "/setowner username - Mod\nAliases: owner, worldowner\nSets the world's owner string"
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify an World Owner.")
        else:
            self.client.world.owner = str(parts[1])
            self.client.sendWorldOwnerUpdate()
            self.client.sendServerMessage("The World Owner has been set.")

    @info_list
    def commandOps(self, parts, byuser, overriderank):
        "/ops - Guest\nLists this world's ops"
        if not self.client.world.ops:
            self.client.sendServerMessage("This world has no Ops.")
        else:
            self.client.sendServerList(["Ops for %s:" % self.client.world.id] + list(self.client.world.ops))

    @info_list
    def commandWriters(self, parts, byuser, overriderank):
        "/writers - Guest\nAliases: builders\nLists this world's writers"
        if not self.client.world.writers:
            self.client.sendServerMessage("This world has no Builders.")
        else:
            self.client.sendServerList(["Builders for %s:" % self.client.world.id] + list(self.client.world.writers))
    
    @info_list
    def commandStatus(self, parts, byuser, overriderank):
        "/status - Guest\nAliases: mapinfo\nReturns info about the current world"
        self.client.sendServerMessage("World: %s" % (self.client.world.id))
        self.client.sendServerMessage("Owner: %s" % self.client.world.owner)
        self.client.sendServerMessage("Size: %sx%sx%s" % (self.client.world.x, self.client.world.y, self.client.world.z))
        self.client.sendServerMessage("- " + \
            (self.client.world.all_write and "&4Unlocked" or "&2Locked") + "&e | " + \
            (self.client.world.zoned and "&2Zones" or "&4Zones") + "&e | " + \
            (self.client.world.private and "&2Private" or "&4Private") + "&e | " + \
            (self.client.world.global_chat and "&2GChat" or "&4GChat")
        )
        self.client.sendServerMessage("- " + \
            (self.client.world.highlight_ops and "&2Colors" or "&4Colors") + "&e | " + \
            (self.client.world.physics and "&2Physics" or "&4Physics") + "&e | " + \
            (self.client.world.finite_water and "&4FWater" or "&2FWater") + "&e | " + \
            (self.client.world.admin_blocks and "&2Solids" or "&4Solids")
        )
        if not self.client.world.ops:
            self.client.sendServerMessage("Ops: N/A")
        else:
            self.client.sendServerList(["Ops:"] + list(self.client.world.ops))
        if not self.client.world.writers:
            self.client.sendServerMessage("Builders: N/A")
        else:
            self.client.sendServerList(["Builders:"] + list(self.client.world.writers))
  
    @world_list
    @op_only
    def commandSetspawn(self, parts, byuser, overriderank):
        "/setspawn - Op\nSets this world's spawn point to the current location."
        x = self.client.x >> 5
        y = self.client.y >> 5
        z = self.client.z >> 5
        h = int(self.client.h*(360/255.0))
        self.client.world.spawn = (x, y, z, h)
        self.client.sendServerMessage("Set spawn point to %s, %s, %s" % (x, y, z))
    
    @info_list
    def commandWhere(self, parts, byuser, overriderank):
        "/where - Guest\nReturns your current coordinates"
        x = self.client.x >> 5
        y = self.client.y >> 5
        z = self.client.z >> 5
        h = self.client.h
        p = self.client.p
        self.client.sendServerMessage("You are at %s, %s, %s [h%s, p%s]" % (x, y, z, h, p))
