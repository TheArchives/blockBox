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

class DynamitePlugin(ProtocolPlugin):

    commands = {
        "tnt": "commandDynamite",
        "dynamite": "commandDynamite",
    }

    hooks = {
        "blockchange": "blockChanged",
        "newworld": "newWorld",
    }

    def gotClient(self):
        self.build_dynamite = False
        self.explosion_radius = 4
        self.delay = 2

    def newWorld(self, world):
        "Hook to reset dynamiting abilities in new worlds if not op."
        if not self.client.isOp():
            self.build_dynamite = False

    def blockChanged(self, x, y, z, block, selected_block, byuser):
        "Hook trigger for block changes."
        tobuild = []
        world = self.client.world
        # Randomise the variables
        fanout = self.explosion_radius
        if self.build_dynamite and block == BLOCK_TNT:
            def explode():
                # Clear the explosion radius
                for i in range(-fanout, fanout+1):
                    for j in range(-fanout, fanout+1):
                        for k in range(-fanout, fanout+1):
                            if (i**2+j**2+k**2)**0.5 + 0.691 < fanout:
                                try:
                                    if not self.client.AllowedToBuild(x+i, y+j, z+k):
                                        return
                                    check_offset = world.blockstore.get_offset(x+i, y+j, z+k)
                                    blocktype = world.blockstore.raw_blocks[check_offset]
                                    unbreakables = [chr(BLOCK_SOLID), chr(BLOCK_IRON), chr(BLOCK_GOLD), chr(BLOCK_TNT)]
                                    strongblocks = [chr(BLOCK_ROCK), chr(BLOCK_STONE), chr(BLOCK_OBSIDIAN), chr(BLOCK_WATER), chr(BLOCK_STILLWATER), chr(BLOCK_LAVA), chr(BLOCK_STILLLAVA), chr(BLOCK_BRICK), chr(BLOCK_GOLDORE), chr(BLOCK_IRONORE), chr(BLOCK_COAL), chr(BLOCK_SPONGE)]
                                    if blocktype not in unbreakables and blocktype not in strongblocks:
                                        if not world.has_mine(x+i, y+j, z+k):
                                            tobuild.append((i, j, k, BLOCK_STILLLAVA))
                                    if (i**2+j**2+k**2)**0.5 + 0.691 < fanout-1:
                                        if blocktype not in unbreakables:
                                            if not world.has_mine(x+i, y+j, z+k):
                                                tobuild.append((i, j, k, BLOCK_STILLLAVA))
                                except AssertionError: # OOB
                                    pass
                # OK, send the build changes
                for dx, dy, dz, block in tobuild:
                    try:
                        world[x+dx, y+dy, z+dz] = chr(block)
                        self.client.sendBlock(x+dx, y+dy, z+dz, block)
                        self.client.factory.queue.put((self.client, TASK_BLOCKSET, (x+dx, y+dy, z+dz, block)))
                    except AssertionError: # OOB
                        pass
            def explode2():
                # Clear the explosion radius
                for i in range(-fanout, fanout+1):
                    for j in range(-fanout, fanout+1):
                        for k in range(-fanout, fanout+1):
                            if (i**2+j**2+k**2)**0.5 + 0.691 < fanout:
                                try:
                                    if not self.client.AllowedToBuild(x+i, y+j, z+k):
                                        return
                                    check_offset = world.blockstore.get_offset(x+i, y+j, z+k)
                                    blocktype = world.blockstore.raw_blocks[check_offset]
                                    unbreakables = [chr(BLOCK_SOLID), chr(BLOCK_IRON), chr(BLOCK_GOLD)]
                                    strongblocks = [chr(BLOCK_ROCK), chr(BLOCK_STONE), chr(BLOCK_OBSIDIAN), chr(BLOCK_WATER), chr(BLOCK_STILLWATER), chr(BLOCK_LAVA), chr(BLOCK_BRICK), chr(BLOCK_GOLDORE), chr(BLOCK_IRONORE), chr(BLOCK_COAL), chr(BLOCK_SPONGE)]
                                    if blocktype not in unbreakables and blocktype not in strongblocks:
                                        if not world.has_mine(x+i, y+j, z+k):
                                            tobuild.append((i, j, k, BLOCK_AIR))
                                    if (i**2+j**2+k**2)**0.5 + 0.691 < fanout-1:
                                        if blocktype not in unbreakables:
                                            if not world.has_mine(x+i, y+j, z+k):
                                                tobuild.append((i, j, k, BLOCK_AIR))
                                except AssertionError: # OOB
                                    pass
                # OK, send the build changes
                for dx, dy, dz, block in tobuild:
                    try:
                        world[x+dx, y+dy, z+dz] = chr(block)
                        self.client.sendBlock(x+dx, y+dy, z+dz, block)
                        self.client.factory.queue.put((self.client, TASK_BLOCKSET, (x+dx, y+dy, z+dz, block)))
                    except AssertionError: # OOB
                        pass
            # Explode in 2 seconds
            reactor.callLater(self.delay, explode)
            # Explode2 in 3 seconds
            reactor.callLater(self.delay+0.5, explode2)

    @build_list
    @op_only
    @on_off_command
    def commandDynamite(self, onoff, byuser, overriderank):
        "/tnt on|off - Op\nAliases: dynamite\nExplodes a radius around the TNT."
        if onoff == "on":
            self.build_dynamite = True
            self.client.sendServerMessage("You have activated TNT; place a TNT block!")
        else:
            self.build_dynamite = False
            self.client.sendServerMessage("You have deactivated TNT.")
