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
from twisted.internet import reactor
import logging
import datetime

class GreiferDetectorPlugin(ProtocolPlugin):

    hooks = {
        "blockchange": "blockChanged",
        "newworld": "newWorld",
    }
    
    def gotClient(self):
        self.var_blockchcount = 0
        self.in_publicworld = False
    
    def blockChanged(self, x, y, z, block, selected_block, byuser):
        "Hook trigger for block changes."
        world = self.client.world
        if block is BLOCK_AIR and self.in_publicworld:
            if ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x, y, z)]) != 3:
                worldname = world.id
                username = self.client.username
                def griefcheck():
                    if self.var_blockchcount >= 35:
                        self.client.factory.queue.put((self.client, TASK_STAFFMESSAGE, ("#%s%s: %s%s" % (COLOUR_DARKGREEN, 'SERVER', COLOUR_DARKGREEN, "ALERT! Possible Griefer behavior detected in"))))
                        self.client.factory.queue.put((self.client, TASK_STAFFMESSAGE, ("#%s%s: %s%s" % (COLOUR_DARKGREEN, 'SERVER', COLOUR_DARKGREEN, "'" + worldname + "'! Username: " + username))))
                        self.client.log(username + " was detected as a possible griefer in '" + worldname + "'")
                        self.client.adlog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" | STAFF | "+username + " was detected as a possible griefer in '" + worldname + "'" + "\n")
                        self.client.adlog.flush()
                    self.var_blockchcount = 0
                if self.var_blockchcount == 0:
                    reactor.callLater(5, griefcheck)
                self.var_blockchcount += 1
                
    def newWorld(self, world):
        "Hook to reset portal abilities in new worlds if not op."
        if world.id.find('public') == -1:
            self.in_publicworld = False
            self.var_blockchcount = 0
        else:
            self.in_publicworld = True
