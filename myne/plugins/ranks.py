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
from myne.globals import *

class ModsPlugin(ProtocolPlugin):
    
    commands = {
        "rank": "commandRank",
        "setrank": "commandRank",
        "derank": "commandDeRank",
        "colors": "commandColors",
        "showops": "commandColors",
        "spec": "commandSpec",
        "unspec": "commandDeSpec",
        "specced": "commandSpecced",
        "writer": "commandOldRanks",
        "builder": "commandOldRanks",
        "op": "commandOldRanks",
        "mod": "commandOldRanks",
        "admin": "commandOldRanks",
        "director": "commandOldRanks",
        "dewriter": "commandOldDeRanks",
        "debuilder": "commandOldDeRanks",
        "deop": "commandOldDeRanks",
        "demod": "commandOldDeRanks",
        "deadmin": "commandOldDeRanks",
        "dedirector": "commandOldDeRanks",
    }

    @player_list
    @mod_only
    def commandSpecced(self, user, byuser, overriderank):
        "/specced - Mod\nShows who is specced."
        if len(self.client.factory.spectators):
            self.client.sendServerList(["Specced:"] + list(self.client.factory.spectators))
        else:
            self.client.sendServerList(["Specced: No one."])

    @player_list
    @op_only
    def commandRank(self, parts, byuser, overriderank):
        "/rank rankname username - Op\nAliases: setrank\nMakes username the rank of rankname."
        if len(parts) < 3:
            self.client.sendServerMessage("You must specify a rank and username.")
        else:
            self.client.sendServerMessage(Rank(self, parts, byuser, overriderank))

    @player_list
    @op_only
    def commandDeRank(self, parts, byuser, overriderank):
        "/derank rankname username - Op\nMakes playername lose the rank of rankname."
        if len(parts) < 3:
            self.client.sendServerMessage("You must specify a rank and username.")
        else:
            self.client.sendServerMessage(DeRank(self, parts, byuser, overriderank))

    @player_list
    @op_only
    def commandOldRanks(self, parts, byuser, overriderank):
        "/rankname username [world] - Op\nAliases: writer, builder, op, mod, admin, director\nThis is here for Myne users."
        if len(parts) < 2:
            self.client.sendServerMessage("You must specify a rank and username.")
        else:
            if parts[0] == "/writer":
                parts[0] = "/builder"
            parts = ["/rank", parts[0][1:]] + parts[1:]
            self.client.sendServerMessage(Rank(self, parts, byuser, overriderank))

    @player_list
    @op_only
    def commandOldDeRanks(self, parts, byuser, overriderank):
        "/derankname username [world] - Op\nAliases: dewriter, debuilder, deop, demod, deadmin, dedirector\nThis is here for Myne users."
        if len(parts) < 2:
            self.client.sendServerMessage("You must specify a rank and username.")
        else:
            if parts[0] == "/dewriter":
                parts[0] = "/debuilder"
            parts = ["/derank", parts[0][1:]] + parts[1:]
            self.client.sendServerMessage(DeRank(self, parts, byuser, overriderank))
                
    @player_list
    @op_only
    @on_off_command
    def commandColors(self, onoff, byuser, overriderank):
        "/colors on|off - Op\nAliases: showops\nEnables or disables colors in this world."
        if onoff == "on":
            self.client.world.highlight_ops = True
            self.client.sendServerMessage("%s now has staff highlighting." % self.client.world.id)
        else:
            self.client.world.highlight_ops = False
            self.client.sendServerMessage("%s no longer has staff highlighting." % self.client.world.id)

    @player_list
    @mod_only
    @only_username_command
    def commandSpec(self, username, byuser, overriderank):
        "/spec username - Mod\nMakes the player as a spec."
        self.client.sendServerMessage(Spec(self, username, byuser, overriderank))
     
    @player_list
    @mod_only
    @only_username_command
    def commandDeSpec(self, username, byuser, overriderank):
        "/unspec username - Mod\nRemoves the player as a spec."
        self.client.factory.spectators.remove(username)
        self.client.sendServerMessage("%s is no longer a spec." % username)
        if username in self.client.factory.usernames:
            self.client.factory.usernames[username].sendSpectatorUpdate()
