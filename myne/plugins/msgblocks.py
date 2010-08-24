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

class MsgblockPlugin(ProtocolPlugin):
    
    commands = {
        "mb": "commandMsgblock",
        "mbox": "commandMsgblock",
        "mbend": "commandMsgblockend",
        "mbshow": "commandShowmsgblocks",
        "mbdel": "commandMsgblockdel",
        "mdel": "commandMsgblockdel",
        "mbdelend": "commandMsgblockdelend",
    }
    
    hooks = {
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
    }
    
    def gotClient(self):
        self.msgblock_message = None
        self.msgblock_remove = False
        self.last_block_position = None
    
    def newWorld(self, world):
        "Hook to reset portal abilities in new worlds if not op."
        if not self.client.isOp():
            self.msgblock_message = None
    
    def blockChanged(self, x, y, z, block, selected_block, byuser):
        "Hook trigger for block changes."
        if self.client.world.has_message(x, y, z):
            if self.msgblock_remove:
                self.client.world.delete_message(x, y, z)
                self.client.sendServerMessage("You deleted a message block.")
            else:
                self.client.sendServerMessage("That is a message block, you cannot change it. (/mbdel?)")
                return False # False = they weren't allowed to build
        if self.msgblock_message:
            self.client.sendServerMessage("You placed a message block")
            self.client.world.add_message(x, y, z, self.msgblock_message)
    
    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the player moves"
        rx = x >> 5
        ry = y >> 5
        rz = z >> 5
        # Or a message?
        try:
            if self.client.world.has_message(rx, ry, rz) and (rx, ry, rz) != self.last_block_position:
                self.client._sendMessage(COLOUR_GREEN, self.client.world.get_message(rx, ry, rz))
        except AssertionError:
            pass
        self.last_block_position = (rx, ry, rz)
    
    @member_only
    def commandMsgblock(self, parts, byuser, overriderank):
        "/mb message - Member\nAliases: mbox\nMakes the next block you place a message block."
        msg_part = (" ".join(parts[1:])).strip()
        if not msg_part:
            self.client.sendServerMessage("Please enter a message.")
            return
        new_message = False
        if not self.msgblock_message:
            self.msgblock_message = ""
            self.client.sendServerMessage("You are now placing message blocks.")
            new_message = True
        if msg_part[-1] == "\\":
            self.msgblock_message += msg_part[:-1] + " "
        else:
            self.msgblock_message += msg_part + "\n"
        if len(self.msgblock_message) > 200:
            self.msgblock_message = self.msgblock_message[:200]
            self.client.sendServerMessage("Your message ended up longer than 200 chars, and was truncated.")
        elif not new_message:
            self.client.sendServerMessage("Message extended; you've used %i characters." % len(self.msgblock_message))
    
    @member_only
    def commandMsgblockend(self, parts, byuser, overriderank):
        "/mbend - Member\nStops placing message blocks."
        self.msgblock_message = None
        self.client.sendServerMessage("You are no longer placing message blocks.")
    
    @member_only
    def commandShowmsgblocks(self, parts, byuser, overriderank):
        "/mbshow - Member\nShows all message blocks as purple, only to you."
        for offset in self.client.world.messages.keys():
            x, y, z = self.client.world.get_coords(offset)
            self.client.sendPacked(TYPE_BLOCKSET, x, y, z, BLOCK_PURPLE)
        self.client.sendServerMessage("All messages appearing purple temporarily.")
    
    @member_only
    def commandMsgblockdel(self, parts, byuser, overriderank):
        "/mbdel - Member\nAliases: mdel\nEnables msgblock-deleting mode"
        self.client.sendServerMessage("You are now able to delete msgblocks. /mbdelend to stop")
        self.msgblock_remove = True
    
    @member_only
    def commandMsgblockdelend(self, parts, byuser, overriderank):
        "/mbdelend - Member\nDisables msgblock-deleting mode"
        self.client.sendServerMessage("Msgblock deletion mode ended.")
        self.msgblock_remove = False
