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

class AdminBlocksPlugin(ProtocolPlugin):
    
    commands = {
        "solid": "commandSolid",
        "solids": "commandAdminblocks",
    }
    
    hooks = {
        "blockchange": "blockChanged",
        "rankchange": "sendAdminBlockUpdate",
        "canbreakadmin": "canBreakAdminBlocks",
    }
    
    def gotClient(self):
        self.building_solid = False
    
    def blockChanged(self, x, y, z, block, selected_block, byuser):
        "Hook trigger for block changes."
        # Admincrete hack check
        if not self.canBreakAdminBlocks():
            def check_block(block):
                if ord(block) == BLOCK_GROUND_ROCK:
                    self.client.sendError("Don't build admincrete!")
                    self.client.world[x, y, z] = chr(BLOCK_AIR)
            self.client.world[x,y,z].addCallback(check_block)
        # See if they are in solid-building mode
        if self.building_solid and block == BLOCK_ROCK:
            return BLOCK_GROUND_ROCK
    
    def canBreakAdminBlocks(self):
        "Shortcut for checking permissions."
        if hasattr(self.client, "world"):
            return (not self.client.world.admin_blocks) or self.client.isOp()
        else:
            return False
    
    def sendAdminBlockUpdate(self):
        "Sends a packet that updates the client's admin-building ability"
        self.client.sendPacked(TYPE_INITIAL, 6, "Admincrete Update", "If you see this, it's a bug", self.canBreakAdminBlocks() and 100 or 0)
    
    @world_list
    @op_only
    @on_off_command
    def commandAdminblocks(self, onoff, byuser, overriderank):
        "/solids on|off - Op\nTurns on/off unbreakable admin/op blocks."
        if onoff == "on":
            self.client.world.admin_blocks = True
            self.client.sendWorldMessage("Admin blocks are now enabled here.")
            self.client.sendServerMessage("Admin Blocks on in %s" % self.client.world.id)
        else:
            self.client.world.admin_blocks = False
            self.client.sendWorldMessage("Admin blocks are now disabled here.")
            self.client.sendServerMessage("Admin Blocks off in %s" % self.client.world.id)
        for client in self.client.world.clients:
            client.sendAdminBlockUpdate()
    
    @build_list
    @op_only
    def commandSolid(self, parts, byuser, overriderank):
        "/solid - Op\nToggles admincrete creation."
        if self.building_solid:
            self.client.sendServerMessage("You are now placing normal rock.")
        else:
            self.client.sendServerMessage("You are now placing admin rock.")
        self.building_solid = not self.building_solid
    
