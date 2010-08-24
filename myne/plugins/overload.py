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

class OverloadPlugin(ProtocolPlugin):
    
    commands = {
        "overload": "commandOverload",
        "send": "commandSend"
    }
    
    @player_list
    @admin_only
    @username_command
    def commandOverload(self, client, byuser, overriderank):
        "/overload username - Admin\nSends the players client a massive fake map."
        client.sendOverload()
        self.client.sendServerMessage("Overload sent to %s" % client.username)

    @player_list
    @mod_only
    @username_command
    def commandSend(self, client, byuser, overriderank):
        "/send username [world] - Mod\nSends the players client another world."
        if params:
            user.changeToWorld("%s" % " ".join(params))
            self.client.sendServerMessage("Map send to %s" % client.username)
        else:
            user.changeToWorld("default")
            self.client.sendServerMessage("Map send to %s" % client.username)
