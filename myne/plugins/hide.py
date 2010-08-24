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

class HidePlugin(ProtocolPlugin):
    
    commands = {
        "hide": "commandHide",
    }
    
    hooks = {
        "playerpos": "playerMoved",
    }
    
    def gotClient(self):
        self.hidden = False
    
    def playerMoved(self, x, y, z, h, p):
        "Stops transmission of player positions if hide is on."
        if self.hidden:
            return False
    
    @player_list
    @op_only
    def commandHide(self, params, byuser, overriderank):
        "/hide - Op\nHides you so no other players can see you. Toggle."
        if not self.hidden:
            self.client.sendServerMessage("You have vanished.")
            self.hidden = True
            # Send the "player has disconnected" command to people
            self.client.queueTask(TASK_PLAYERLEAVE, [self.client.id])
        else:
            self.client.sendServerMessage("That was Magic!")
            self.hidden = False
            #Imagine that! They've mysteriously appeared.
            self.client.queueTask(TASK_NEWPLAYER, [self.client.id, self.client.username, self.client.x, self.client.y, self.client.z, self.client.h, self.client.p])
            #self.client.queueTask(TASK_PLAYERCONNECT, [self.client.id, self.client.username, self.client.x, self.client.y, self.client.z, self.client.h, self.client.p])
