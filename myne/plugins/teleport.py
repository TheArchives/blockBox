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

class TeleportPlugin(ProtocolPlugin):
    
    commands = {
        "goto": "commandGoto",
        "tp": "commandTeleport",
        "teleport": "commandTeleport",
    }

    @world_list
    def commandGoto(self, parts, byuser, overriderank):
        "/goto x y z - Guest\nTeleports you to coords. NOTE: y is up."
        try:
            x = int(parts[1])
            y = int(parts[2])
            z = int(parts[3])
            self.client.teleportTo(x, y, z)
        except (IndexError, ValueError):
            self.client.sendServerMessage("Usage: /goto x y z")
    
    @player_list
    @username_command
    def commandTeleport(self, user, byuser, overriderank):
        "/tp username - Guest\nAliases: teleport\nTeleports you to the players location."
        x = user.x >> 5
        y = user.y >> 5
        z = user.z >> 5
        if user.world == self.client.world:
            self.client.teleportTo(x, y, z)
        else:
            if self.client.canEnter(user.world):
                self.client.changeToWorld(user.world.id, position=(x, y, z))
            else:
                self.client.sendServerMessage("Sorry, that world is private.")
