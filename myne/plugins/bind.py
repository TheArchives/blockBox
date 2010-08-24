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

class BindPlugin(ProtocolPlugin):
    
    commands = {
        "bind": "commandBind",
        "build": "commandBind",
        "material": "commandBind",
        "air": "commandAir",
        "stand": "commandAir",
        "place": "commandAir",
    }
    
    hooks = {
        "blockchange": "blockChanged",
    }
    
    def gotClient(self):
        self.block_overrides = {}
    
    def blockChanged(self, x, y, z, block, selected_block, byuser):
        "Hook trigger for block changes."
        if block in self.block_overrides:
            return self.block_overrides[block]

    @build_list
    def commandBind(self, parts, byuser, overriderank):
        "/bind blockA blockB - Guest\nAliases: build, material\nBinds blockB to blockA."
        if len(parts) == 1:
            if self.block_overrides:
                temp = tuple(self.block_overrides)
                for each in temp:
                    del self.block_overrides[each]
                self.client.sendServerMessage("All blocks are back to normal")
                del temp
                return
            self.client.sendServerMessage("Please enter two block types.")
        elif len(parts) == 2:
            old = ord(self.client.GetBlockValue(parts[1]))
            if old == None:
                return
            if old in self.block_overrides:
                del self.block_overrides[old]
                self.client.sendServerMessage("%s is back to normal." % parts[1])
            else:
                self.client.sendServerMessage("Please enter two block types.")
        else:
            old = self.client.GetBlockValue(parts[1])
            if old == None:
                return
            old = ord(old)
            new = self.client.GetBlockValue(parts[2])
            if new == None:
                return
            new = ord(new)
            name = parts[2].lower()
            old_name = parts[1].lower()
            self.block_overrides[old] = new
            self.client.sendServerMessage("%s will turn into %s." % (old_name, name))

    @build_list
    def commandAir(self, params, byuser, overriderank):
        "/air - Guest\nAliases: stand, place\nPuts a block under you for easier building in the air."
        self.client.sendPacked(TYPE_BLOCKSET, self.client.x>>5, (self.client.y>>5)-3, (self.client.z>>5), BLOCK_WHITE)
