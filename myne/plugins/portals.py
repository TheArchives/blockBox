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

class PortalPlugin(ProtocolPlugin):
    
    commands = {
        "p": "commandPortal",
        "tpbox": "commandPortal",
        "phere": "commandPortalhere",
        "pend": "commandPortalend",
        "pclear": "commandClearportals",
        "pshow": "commandShowportals",
        "tpshow": "commandShowportals",
        "pdel": "commandPortaldel",
        "deltp": "commandPortaldel",
        "pdelend": "commandPortaldelend",
        "puse": "commandUseportals",
    }
    
    hooks = {
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
    }
    
    def gotClient(self):
        self.portal_dest = None
        self.portal_remove = False
        self.portals_on = True
        self.last_block_position = None
    
    def blockChanged(self, x, y, z, block, selected_block, byuser):
        "Hook trigger for block changes."
        if self.client.world.has_teleport(x, y, z):
            if self.portal_remove:
                self.client.world.delete_teleport(x, y, z)
                self.client.sendServerMessage("You deleted a teleport block.")
            else:
                self.client.sendServerMessage("That is a teleport block, you cannot change it. (/pdel?)")
                return False # False = they weren't allowed to build
        if self.portal_dest:
            self.client.sendServerMessage("You placed a teleport block")
            self.client.world.add_teleport(x, y, z, self.portal_dest)
    
    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the player moves"
        rx = x >> 5
        ry = y >> 5
        rz = z >> 5
        try:
            world, tx, ty, tz, th = self.client.world.get_teleport(rx, ry, rz)
        except (KeyError, AssertionError):
            pass
        else:
            # Yes there is! do it.
            if self.portals_on:
                world_id = world
                if world_id not in self.client.factory.worlds:
                    self.client.sendServerMessage("Attempting to boot and join '%s'" % world_id)
                    try:
                        self.client.factory.loadWorld("worlds/%s" % world_id, world_id)
                    except AssertionError:
                        self.client.sendServerMessage("There is no world by that name.")
                        return
                    return
                world = self.client.factory.worlds[world_id]
                if not self.client.canEnter(world):
                    if (rx, ry, rz) != self.last_block_position:
                        self.client.sendServerMessage("'%s' is private; you're not allowed in." % world_id)
                else:
                    if world == self.client.world:
                        self.client.teleportTo(tx, ty, tz, th)
                    else:
                        self.client.changeToWorld(world.id, position=(tx, ty, tz, th))
        self.last_block_position = (rx, ry, rz)
    
    def newWorld(self, world):
        "Hook to reset portal abilities in new worlds if not op."
        if not self.client.isOp():
            self.portal_dest = None
            self.portal_remove = False
            self.portals_on = True
    
    @op_only
    def commandPortal(self, parts, byuser, overriderank):
        "/p worldname x y z [r] - Op\nAliases: tpbox\nMakes the next block you place a portal."
        if len(parts) < 5:
            self.client.sendServerMessage("Please enter a worldname, x, y and z.")
        else:
            try:
                x = int(parts[2])
                y = int(parts[3])
                z = int(parts[4])
            except ValueError:
                self.client.sendServerMessage("x, y and z must be integers")
            else:
                try:
                    h = int(parts[5])
                except IndexError:
                    h = 0
                except ValueError:
                    self.client.sendServerMessage("r must be an integer")
                    return
                if not (0 <= h <= 255):
                    self.client.sendServerMessage("r must be between 0 and 255")
                    return
                self.portal_dest = parts[1], x, y, z, h
                self.client.sendServerMessage("You are now placing portal blocks. /portalend to stop")
    
    @op_only
    def commandPortalhere(self, parts, byuser, overriderank):
        "/phere - Op\nEnables portal-building mode, to here."
        self.portal_dest = self.client.world.id, self.client.x>>5, self.client.y>>5, self.client.z>>5, self.client.h
        self.client.sendServerMessage("You are now placing portal blocks to here.")
    
    @op_only
    def commandPortalend(self, parts, byuser, overriderank):
        "/pend - Op\nStops placing portal blocks."
        self.portal_dest = None
        self.portal_remove = False
        self.client.sendServerMessage("You are no longer placing portal blocks.")
    
    @op_only
    def commandClearportals(self, parts, byuser, overriderank):
        "/pclear - Op\nRemoves all portals from the map."
        self.client.world.clear_teleports()
        self.client.sendServerMessage("All portals in this world removed.")
    
    @op_only
    def commandShowportals(self, parts, byuser, overriderank):
        "/pshow - Op\nAliases: tpshow\nShows all portal blocks as blue, only to you."
        for offset in self.client.world.teleports.keys():
            x, y, z = self.client.world.get_coords(offset)
            self.client.sendPacked(TYPE_BLOCKSET, x, y, z, BLOCK_BLUE)
        self.client.sendServerMessage("All portals appearing blue temporarily.")
    
    @op_only
    def commandPortaldel(self, parts, byuser, overriderank):
        "/pdel - Op\nAliases: deltp\nEnables portal-deleting mode"
        self.client.sendServerMessage("You are now able to delete portals. /pdelend to stop")
        self.portal_remove = True
    
    @op_only
    def commandPortaldelend(self, parts, byuser, overriderank):
        "/pdelend - Op\nDisables portal-deleting mode"
        self.client.sendServerMessage("Portal deletion mode ended.")
        self.portal_remove = False
    
    @on_off_command
    def commandUseportals(self, onoff, byuser, overriderank):
        "/puse on|off - Guest\nAllows you to enable or diable portal usage."
        if onoff == "on":
            self.portals_on = True
            self.client.sendServerMessage("Portals will now work for you again.")
        else:
            self.portals_on = False
            self.client.sendServerMessage("Portals will now not work for you.")
