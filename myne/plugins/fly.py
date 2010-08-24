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

class FlyPlugin(ProtocolPlugin):
    
    commands = {
        "fly": "commandFly",
    }
    
    hooks = {
        "poschange": "posChanged",
        "newworld": "newWorld",
    }
    
    def gotClient(self):
        self.flying = False
        self.last_flying_block = None
    
    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the player moves"
        # Are we fake-flying them?
        if self.flying:
            fly_block_loc = ((x>>5),((y-48)>>5)-1,(z>>5))
            if not self.last_flying_block:
                # OK, send the first flying blocks
                self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0], fly_block_loc[1] - 1, fly_block_loc[2], BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
            else:
                # Have we moved at all?
                if fly_block_loc != self.last_flying_block:
                    self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1] - 1, self.last_flying_block[2], BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
                    self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
                    self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0], fly_block_loc[1] - 1, fly_block_loc[2], BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2], BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0], fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] - 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] - 1, BLOCK_GLASS)
                    self.setCsBlock(fly_block_loc[0] + 1, fly_block_loc[1], fly_block_loc[2] + 1, BLOCK_GLASS)
            self.last_flying_block = fly_block_loc
        else:
            if self.last_flying_block:
                self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1] - 1, self.last_flying_block[2], BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2], BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0], self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] - 1, self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2] - 1, BLOCK_AIR)
                self.setCsBlock(self.last_flying_block[0] + 1, self.last_flying_block[1], self.last_flying_block[2] + 1, BLOCK_AIR)
                self.last_flying_block = None
    
    def newWorld(self, world):
        "Hook to reset flying abilities in new worlds if not op."
        if self.client.isSpectator():
            self.flying = False
    
    @player_list
    @on_off_command
    def commandFly(self, onoff, byuser, overriderank):
        "/fly on|off - Guest\nEnables or disables bad server-side flying"
        if onoff == "on":
            self.flying = True
            self.client.sendServerMessage("You are now flying")
        else:
            self.flying = False
            self.client.sendServerMessage("You are no longer flying")

    def setCsBlock(self, x, y, z, type):
        if y > -1 and x > -1 and z > -1:
            if y < self.client.world.y and x < self.client.world.x and z < self.client.world.z:
                if ord(self.client.world.blockstore.raw_blocks[self.client.world.blockstore.get_offset(x, y, z)]) is 0:
                    self.client.sendPacked(TYPE_BLOCKSET, x, y, z, type)
