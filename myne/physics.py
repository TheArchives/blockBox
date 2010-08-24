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

import logging
import time
from collections import deque
from threading import Thread, Lock
from twisted.internet import reactor
from constants import *

CHR_WATER = chr(BLOCK_WATER)
CHR_LAVA = chr(BLOCK_LAVA)
CHR_AIR = chr(BLOCK_AIR)
CHR_STILLWATER = chr(BLOCK_STILLWATER)
CHR_DIRT = chr(BLOCK_DIRT)
CHR_GLASS = chr(BLOCK_GLASS)
CHR_GRASS = chr(BLOCK_GRASS)
CHR_SPONGE = chr(BLOCK_SPONGE)
CHR_LEAVES = chr(BLOCK_LEAVES)
CHR_SAND = chr(BLOCK_SAND)
BLOCK_SPOUT = BLOCK_DARKBLUE
BLOCK_LAVA_SPOUT = BLOCK_ORANGE
BLOCK_SAND_SPOUT = BLOCK_WHITE
CHR_SPOUT = chr(BLOCK_SPOUT)
CHR_LAVA_SPOUT = chr(BLOCK_LAVA_SPOUT)
CHR_SAND_SPOUT = chr(BLOCK_SAND_SPOUT)
REQUEUE_FLUID = -1

class Physics(Thread):
    """
    Given a BlockStore, works out what needs doing (water, grass etc.)
    and send the changes back to the BlockStore.
    """
    LAG_INTERVAL = 60 # How long between "ack we're lagging" messages
    FLUID_LIMIT = 700
    AIR_LIMIT = 800
    SPONGE_LIMIT = 50
    GRASS_GROW_LIMIT = 10
    GRASS_DIE_LIMIT = 10
    SAND_FALL_LIMIT = 1000
    
    def __init__(self, blockstore):
        Thread.__init__(self)
        self.blockstore = blockstore
        self.last_lag = 0
        self.running = True
        self.was_physics = False
        self.was_unflooding = False
        self.init_queues()
    
    def stop(self):
        self.running = False
        self.join()
    
    def run(self):
        while self.running:
            if self.blockstore.physics:
                logging.log(logging.DEBUG, "Starting physics run for '%s'. (a%i, f%i, s%i, gg%i, gd%i)" % (self.blockstore.blocks_path, len(self.air_queue), len(self.fluid_queue), len(self.sponge_queue), len(self.grass_grow_queue), len(self.grass_die_queue)))
                # If this is the first of a physics run, redo the queues from scratch
                if self.was_physics == False:
                    logging.log(logging.DEBUG, "Performing queue scan for '%s'." % self.blockstore.blocks_path)
                    self.scan_blocks()
                # SCIENCE!!!
                changes, overflow = self.run_iteration()
                # Replay the changes
                for x, y, z, block in changes:
                    if block is REQUEUE_FLUID:
                        self.fluid_queue.add(self.blockstore.get_offset(x, y, z))
                    else:
                        self.blockstore[x, y, z] = chr(block)
                        self.blockstore.send_block(x, y, z)
                if overflow and (time.time() - self.last_lag > self.LAG_INTERVAL):
                    self.blockstore.admin_message("Physics is currently lagging in %(id)s.")
                    self.last_lag = time.time()
                logging.log(logging.DEBUG, "Ended physics run for '%s' (c%i, a%i, f%i, s%i, gg%i, gd%i)." % (self.blockstore.blocks_path, len(changes), len(self.air_queue), len(self.fluid_queue), len(self.sponge_queue), len(self.grass_grow_queue), len(self.grass_die_queue)))
            else:
                if self.was_physics:
                    self.init_queues()
            self.was_physics = self.blockstore.physics
            self.was_unflooding = self.blockstore.unflooding
            # Wait till next iter
            time.sleep(0.7)
    
    def init_queues(self):
        self.fluid_queue = set()
        self.grass_grow_queue = set()
        self.grass_die_queue = set()
        self.air_queue = set()
        self.sponge_queue = set()
        self.sponge_locations = set()
        self.sand_queue = set()
    
    def scan_blocks(self):
        "Scans the blockstore, looking for things to add to the queues."
        # Initialise the queues
        self.init_queues()
        # Scan
        for offset, block in enumerate(self.blockstore.raw_blocks):
            if block is CHR_LAVA or block is CHR_WATER:# or block is CHR_SPOUT or block is CHR_LAVA_SPOUT:
                self.fluid_queue.add(offset)
            elif block is CHR_GRASS:
                self.grass_grow_queue.add(offset)
            elif block is CHR_SPONGE:
                self.sponge_queue.add(offset)
            elif block is CHR_SAND:
                self.sand_queue.add(offset)
    
    def handle_change(self, offset, block):
        "Gets called when a block is changed, with its position and type."
        assert isinstance(block, str)
        if self.blockstore.physics:
            if block is CHR_LAVA or block is CHR_WATER or block is CHR_SPOUT or block is CHR_LAVA_SPOUT:
                self.fluid_queue.add(offset)
            elif block is CHR_AIR:
                self.sponge_queue.add(offset)
                self.air_queue.add(offset)
            elif block is CHR_SPONGE:
                self.sponge_queue.add(offset)
            elif block is CHR_SAND:
                self.sand_queue.add(offset)
        if block is CHR_DIRT or block is CHR_GRASS:
                self.grass_grow_queue.add(offset)
    
    def apply_ops(self, ops):
        "Immediately applies changes to the in-memory state. Returns the changes."
        for x, y, z, block in ops:
            if block is not REQUEUE_FLUID:
                self.blockstore.raw_blocks[self.blockstore.get_offset(x, y, z)] = chr(block)
            yield x, y, z, block
    
    def run_iteration(self):
        changes = []
        fluid_done = 0
        # Are we unflooding? If so, do it.
        if self.blockstore.unflooding:
            if not self.was_unflooding:
                # We've just started, do a scan to get all the fluids.
                self.scan_blocks()
            # Do n fluid removals
            try:
                while fluid_done < self.FLUID_LIMIT:
                    offset = self.fluid_queue.pop()
                    x, y, z = self.blockstore.get_coords(offset)
                    changes.append((x, y, z, BLOCK_AIR))
                    fluid_done += 1
            except KeyError:
                pass
            # Did we do nothing? Unflooding complete.
            if fluid_done == 0:
                self.blockstore.unflooding = False
                self.blockstore.world_message(COLOUR_YELLOW+"Unflooding complete.")
        else:
            # Do up to n air things
            air_done = 0
            try:
                while air_done < self.AIR_LIMIT:
                    offset = self.air_queue.pop()
                    ops = list(self.apply_ops(self.handle_air(offset)))
                    air_done += len(ops)
                    changes.extend(ops)
            except KeyError:
                pass
            # Do up to n fluid things
            try:
                while fluid_done < self.FLUID_LIMIT:
                    offset = self.fluid_queue.pop()
                    ops = list(self.apply_ops(self.handle_fluid(offset)))
                    fluid_done += len(ops)
                    changes.extend(ops)
            except KeyError:
                pass
            # Do up to n sponge things
            sponge_done = 0
            try:
                while sponge_done < self.SPONGE_LIMIT:
                    offset = self.sponge_queue.pop()
                    ops = list(self.apply_ops(self.handle_sponge(offset)))
                    sponge_done += len(ops)
                    changes.extend(ops)
            except KeyError:
                pass
            # Let's move on to grass growing. Do n of these.
            grass_grown = 0
            try:
                while grass_grown < self.GRASS_GROW_LIMIT:
                    offset = self.grass_grow_queue.pop()
                    ops = list(self.apply_ops(self.handle_grass_grow(offset)))
                    grass_grown += len(ops)
                    changes.extend(ops)
            except KeyError:
                pass
            # Let's move on to sand falling. Do n of these.
            sand_fall = 0
            try:
                while sand_fall < self.SAND_FALL_LIMIT:
                    offset = self.sand_queue.pop()
                    ops = list(self.apply_ops(self.handle_sand_fall(offset)))
                    sand_fall += len(ops)
                    changes.extend(ops)
            except KeyError:
                pass
        return changes, (fluid_done >= self.FLUID_LIMIT)
    
    def get_blocks(self, x, y, z, deltas):
        "Given a starting point and some deltas, returns all offsets which exist."
        for dx, dy, dz in deltas:
            try:
                new_offset = self.blockstore.get_offset(x+dx, y+dy, z+dz)
            except AssertionError:
                pass
            else:
                yield x+dx, y+dy, z+dz, new_offset
    
    def is_blocked(self, x, y, z):
        "Given coords, determines if the block can see the sky."
        blocked = False
        for ny in range(y+1, self.blockstore.y):
            blocker_offset = self.blockstore.get_offset(x, ny, z)
            blocker_block = self.blockstore.raw_blocks[blocker_offset]
            if not ((blocker_block is CHR_AIR) or (blocker_block is CHR_GLASS) or (blocker_block is CHR_LEAVES)):
                blocked = True
                break
        return blocked
    
    def block_radius(self, r):
        "Returns blocks within the radius"
        for x in range(-r, r+1):
            for y in range(-r, r+1):
                for z in range(-r, r+1):
                    if x or y or z:
                        yield (x, y, z)
    
    def handle_air(self, offset):
        "Handles the appearance of an air block, for fluids or growth"
        x, y, z = self.blockstore.get_coords(offset)
        block = self.blockstore.raw_blocks[offset]
        if block is not CHR_AIR:
            return
        # We're a generator, really.
        if False:
            yield
        # Is there water/lava above/beside it?
        for nx, ny, nz, new_offset in self.get_blocks(x, y, z, self.block_radius(1)):
            new_block = self.blockstore.raw_blocks[new_offset]
            if new_block is CHR_WATER or new_block is CHR_LAVA:
                self.fluid_queue.add(new_offset)
            elif new_block is CHR_SAND:
                self.sand_queue.add(new_offset)
    
    def handle_sponge(self, offset):
        "Handles simulation of sponge blocks."
        x, y, z = self.blockstore.get_coords(offset)
        block = self.blockstore.raw_blocks[offset]
        if block is CHR_SPONGE:
            # OK, it's a sponge. Add it to sponge locations.
            self.sponge_locations.add((offset))
            # Make sure all the water blocks around it go away
            for nx, ny, nz, new_offset in self.get_blocks(x, y, z, self.block_radius(5)):
                block = self.blockstore.raw_blocks[new_offset]
                if block is CHR_WATER and not self.blockstore.finite_water:
                    yield (nx, ny, nz, BLOCK_AIR)
            # If it's finite water, re-animate anything at the edges.
            if self.blockstore.finite_water:
                for nx, ny, nz, new_offset in self.get_blocks(x, y, z, self.block_radius(1)):
                    block = self.blockstore.raw_blocks[new_offset]
                    if block is CHR_WATER or block is CHR_LAVA:
                        self.fluid_queue.add(new_offset)
        if block is CHR_AIR:
            if offset in self.sponge_locations:
                self.sponge_locations.remove(offset)
                # See if there's some water or lava that needs reanimating
                for nx, ny, nz, new_offset in self.get_blocks(x, y, z, self.block_radius(3)):
                    block = self.blockstore.raw_blocks[new_offset]
                    if block is CHR_WATER or block is CHR_LAVA:
                        self.fluid_queue.add(new_offset)
    
    def sponge_within_radius(self, x, y, z, r):
        for nx, ny, nz, new_offset in self.get_blocks(x, y, z, self.block_radius(r)):
            if new_offset in self.sponge_locations:
                return True
        return False
    
    def handle_fluid(self, offset):
        "Handles simulation of fluid blocks."
        x, y, z = self.blockstore.get_coords(offset)
        block = self.blockstore.raw_blocks[offset]
        # Spouts produce water in finite mode
        if block is CHR_SPOUT or block is CHR_LAVA_SPOUT:
            # If there's a gap below, produce water
            if self.blockstore.finite_water:
                try:
                    below = self.blockstore.get_offset(x, y-1, z)
                except AssertionError:
                    pass # At bottom of map
                else:
                    if self.blockstore.raw_blocks[below] is CHR_AIR:
                        if block is CHR_SPOUT:
                            yield (x, y-1, z, BLOCK_WATER)
                        else:
                            yield (x, y-1, z, BLOCK_LAVA)
            yield (x, y, z, REQUEUE_FLUID)
        if block is not CHR_WATER and block is not CHR_LAVA:
            return
        # OK, so, can it drop?
        try:
            below = self.blockstore.get_offset(x, y-1, z)
        except AssertionError:
            pass # At bottom of map
        else:
            if self.blockstore.finite_water:
                if self.blockstore.raw_blocks[below] is CHR_AIR:
                    yield (x, y-1, z, ord(block))
                    yield (x, y, z, BLOCK_AIR)
                    return
                elif self.blockstore.raw_blocks[below] is CHR_SPONGE:
                    yield (x, y, z, BLOCK_AIR)
                    return
            else:
                if self.blockstore.raw_blocks[below] is CHR_AIR and not self.sponge_within_radius(x, y-1, z, 2):
                    yield (x, y-1, z, ord(block))
                    yield (x, y, z, BLOCK_AIR)
                    return
        # Noice. Now, can it spread?
        if self.blockstore.finite_water:
            # Finite water first tries to move downwards and straight
            for nx, ny, nz, new_offset in self.get_blocks(x, y, z, [(0, -1, 1), (0, -1, -1), (1, -1, 0), (-1, -1, 0)]):
                above_offset = self.blockstore.get_offset(nx, ny+1, nz)
                if self.blockstore.raw_blocks[above_offset] is CHR_AIR:
                    # Air? Fall.
                    if self.blockstore.raw_blocks[new_offset] is CHR_AIR:
                        yield (nx, ny, nz, ord(block))
                        yield (x, y, z, BLOCK_AIR)
                        return
                    # Sponge? Absorb.
                    if self.blockstore.raw_blocks[new_offset] is CHR_SPONGE:
                        yield (x, y, z, BLOCK_AIR)
                        return
            # Then it tries a diagonal
            for nx, ny, nz, new_offset in self.get_blocks(x, y, z, [(1, -1, 1), (1, -1, -1), (-1, -1, 1), (-1, -1, -1)]):
                above_offset = self.blockstore.get_offset(nx, ny+1, nz)
                left_offset = self.blockstore.get_offset(x, ny+1, nz)
                right_offset = self.blockstore.get_offset(nx, ny+1, z)
                if self.blockstore.raw_blocks[above_offset] is CHR_AIR and \
                   (self.blockstore.raw_blocks[left_offset] is CHR_AIR or \
                   self.blockstore.raw_blocks[right_offset] is CHR_AIR):
                    # Air? Fall.
                    if self.blockstore.raw_blocks[new_offset] is CHR_AIR:
                        yield (nx, ny, nz, ord(block))
                        yield (x, y, z, BLOCK_AIR)
                        return
                    # Sponge? Absorb.
                    if self.blockstore.raw_blocks[new_offset] is CHR_SPONGE:
                        yield (x, y, z, BLOCK_AIR)
                        return
        else:
            # Infinite water spreads in the 4 horiz directions.
            for nx, ny, nz, new_offset in self.get_blocks(x, y, z, [(0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0)]):
                if self.blockstore.raw_blocks[new_offset] is CHR_AIR and not self.sponge_within_radius(nx, ny, nz, 2):
                    yield (nx, ny, nz, ord(block))
    
    def handle_grass_grow(self, offset):
        """
        Handles grass growing. We get passed either a patch of grass that
        might spread, or a dirt tile that might grow.
        """
        x, y, z = self.blockstore.get_coords(offset)
        block = self.blockstore.raw_blocks[offset]
        if block is CHR_DIRT:
            # See if there's any grass next to us
            for nx, ny, nz, new_offset in self.get_blocks(x, y, z, [(0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0)]):
                if self.blockstore.raw_blocks[new_offset] is CHR_GRASS:
                    # Alright, can we see the sun?
                    if not self.is_blocked(x, y, z):
                        yield (x, y, z, BLOCK_GRASS)
                        self.grass_grow_queue.add(offset)
        elif block is CHR_GRASS:
            # See if there's any dirt next to us
            for nx, ny, nz, new_offset in self.get_blocks(x, y, z, [(0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0)]):
                if self.blockstore.raw_blocks[new_offset] is CHR_DIRT:
                    # Alright, can we see the sun?
                    if not self.is_blocked(nx, ny, nz):
                        yield (nx, ny, nz, BLOCK_GRASS)
                        self.grass_grow_queue.add(new_offset)
    
    def handle_sand_fall(self, offset):
        """
        Handles sand falling. Experimental.
        If there's air below it, it behaves like finite water but stacks instead of spreading.
        """
        x, y, z = self.blockstore.get_coords(offset)
        block = self.blockstore.raw_blocks[offset]
        # Spouts produce water in finite mode
        if block is CHR_SAND_SPOUT:
            # If there's a gap below, produce water
            try:
                below = self.blockstore.get_offset(x, y-1, z)
            except AssertionError:
                pass # At bottom of map
            else:
                if self.blockstore.raw_blocks[below] is CHR_AIR:
                    if block is CHR_SAND_SPOUT:
                        yield (x, y-1, z, BLOCK_SAND)      
        yield (x, y, z, REQUEUE_FLUID)
        if block is not CHR_WATER and block is not CHR_LAVA and block is not CHR_SAND:
            return
        # OK, so, can it drop?
        try:
            below = self.blockstore.get_offset(x, y-1, z)
        except AssertionError:
            pass # At bottom of map
        else:
            if self.blockstore.raw_blocks[below] is CHR_AIR:
                yield (x, y-1, z, ord(block))
                yield (x, y, z, BLOCK_AIR)
                return
            else:
                if self.blockstore.raw_blocks[below] is CHR_AIR and not self.sponge_within_radius(x, y-1, z, 2):
                    yield (x, y-1, z, ord(block))
                    yield (x, y, z, BLOCK_AIR)
                    return
        # Noice. Now, can it spread?
        if self.blockstore.finite_water:
            # Sand tries to move downwards and straight
            for nx, ny, nz, new_offset in self.get_blocks(x, y, z, [(0, -1, 1), (0, -1, -1), (1, -1, 0), (-1, -1, 0)]):
                above_offset = self.blockstore.get_offset(nx, ny+1, nz)
                if self.blockstore.raw_blocks[above_offset] is CHR_AIR:
                    # Air? Fall.
                    if self.blockstore.raw_blocks[new_offset] is CHR_AIR:
                        yield (nx, ny, nz, ord(block))
                        yield (x, y, z, BLOCK_AIR)
                        return
