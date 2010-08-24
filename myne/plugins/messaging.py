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

import random
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class MessagingPlugin(ProtocolPlugin):
    
    commands = {
        "say": "commandSay",
        "msg": "commandSay",
        "me": "commandMe",
        "srb": "commandSRB",
        "u": "commandUrgent",
        "urgent": "commandUrgent",
        "afk": "commandAway",
        "back": "commandBack",
    }

    @player_list
    def commandBack(self, parts, byuser, overriderank):
        "/back - Guest\nPrints out message of you coming back."
        if len(parts) != 1:
            self.client.sendServerMessage("This command doesn't need arguments")
        else:
            self.client.factory.queue.put((self.client, TASK_AWAYMESSAGE, self.client.username + " is now: "+COLOUR_DARKGREEN+"Back."))
            self.client.gone = 0
    
    @player_list
    def commandAway(self, parts, byuser, overriderank):
         "/away reason - Guest\nAliases: afk\nPrints out message of you going away."
         if len(parts) == 1:
             self.client.factory.queue.put((self.client, TASK_AWAYMESSAGE, self.client.username + " has gone: Away."))
             self.client.gone = 1
         else:
             self.client.factory.queue.put((self.client, TASK_AWAYMESSAGE, self.client.username + " has gone: Away"+COLOUR_WHITE+" "+(" ".join(parts[1:]))))
             self.client.gone = 1

    @player_list
    def commandMe(self, parts, byuser, overriderank):
        "/me action - Guest\nPrints * username action"
        if len(parts) == 1:
            self.client.sendServerMessage("Please type an action.")
        else:
            self.client.factory.queue.put((self.client, TASK_ACTION, (self.client.id, self.client.userColour(), self.client.username, " ".join(parts[1:]))))
    
    @mod_only
    def commandSay(self, parts, byuser, overriderank):
        "/say message - Mod\nAliases: msg\nPrints out message in the server color."
        if len(parts) == 1:
            self.client.sendServerMessage("Please type a message.")
        else:
            self.client.factory.queue.put((self.client, TASK_SERVERMESSAGE, ("[MSG] "+(" ".join(parts[1:])))))
    
    @director_only
    def commandSRB(self, parts, byuser, overriderank):
        "/srb - Director\nPrints out a reboot message."
        self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, ("[URGENT] Server Reboot - Back in a Flash")))

    @admin_only
    def commandUrgent(self, parts, byuser, overriderank):
        "/u message - Admin\nAliases: urgent\nPrints out message in the server color."
        if len(parts) == 1:
            self.client.sendServerMessage("Please type a message.")
        else:
            self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, "[URGENT] "+(" ".join(parts[1:]))))
