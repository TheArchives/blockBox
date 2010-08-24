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

import os
import gzip
import struct
import mmap
from threading import Thread
from Queue import Queue
import logging
import time
from array import array
from physics import Physics
from constants import *

class BlockStore(Thread):
    """
    A class which deals with storing the block maps, flushing them, etc.
    """
    
    def __init__(self, blocks_path,  sx, sy, sz):
        Thread.__init__(self)
        self.x, self.y, self.z = sx, sy, sz
        self.blocks_path = blocks_path
        self.in_queue = Queue()
        self.out_queue = Queue()
    
    def run(self):
        # Initialise variables
        self.physics = False
        self.physics_engine = Physics(self)
        self.raw_blocks = None
        self.running = True
        self.unflooding = False
        self.finite_water = False
        self.queued_blocks = {} # Blocks which need to be flushed into the file.
        self.create_raw_blocks()
        # Start physics engine
        self.physics_engine.start()
        # Main eval loop
        while self.running:
            try:
                # Pop something off the queue
                task = self.in_queue.get()
                # If we've been asked to flush, do so, and say we did.
                if task[0] is TASK_FLUSH:
                    self.flush()
                    self.out_queue.put([TASK_FLUSH])
                # New block?
                elif task[0] is TASK_BLOCKSET:
                    try:
                        self[task[1]] = task[2]
                    except AssertionError:
                        logging.log("Tried to set a block at %s in %s!" % (task[1], self.blocks_path), logging.WARN)
                # Asking for a block?
                elif task[0] is TASK_BLOCKGET:
                    self.out_queue.put([TASK_BLOCKGET, task[1], self[task[1]]])
                # Perhaps physics was enabled?
                elif task[0] is TASK_PHYSICSOFF:
                    logging.log(logging.DEBUG, "Disabling physics on '%s'..." % self.blocks_path)
                    self.disable_physics()
                # Or disabled?
                elif task[0] is TASK_PHYSICSON:
                    logging.log(logging.DEBUG, "Enabling physics on '%s'..." % self.blocks_path)
                    self.enable_physics()
                # I can haz finite water tiem?
                elif task[0] is TASK_FWATERON:
                    logging.log(logging.DEBUG, "Enabling finite water on '%s'..." % self.blocks_path)
                    self.finite_water = True
                # Noes, no more finite water.
                elif task[0] is TASK_FWATEROFF:
                    logging.log(logging.DEBUG, "Disabling finite water on '%s'..." % self.blocks_path)
                    self.finite_water = False
                # Do they need to do a Moses?
                elif task[0] is TASK_UNFLOOD:
                    logging.log(logging.DEBUG, "Unflood started on '%s'..." % self.blocks_path)
                    self.unflooding = True
                # Perhaps that's it, and we need to stop?
                elif task[0] is TASK_STOP:
                    logging.log(logging.DEBUG, "Stopping block store '%s'..." % self.blocks_path)
                    self.physics_engine.stop()
                    self.flush()
                    logging.log(logging.DEBUG, "Stopped block store '%s'." % self.blocks_path)
                    return
                # ???
                else:
                    raise ValueError("Unknown BlockStore task: %s" % task)
            except (KeyboardInterrupt, IOError):
                pass
    
    def enable_physics(self):
        "Turns on physics"
        self.flush()
        self.physics = True
    
    def disable_physics(self):
        "Disables physics, and clears the in-memory store."
        self.physics = False
    
    def create_raw_blocks(self):
        "Reads in the gzipped data into a raw array"
        # Open the blocks file
        fh = gzip.GzipFile(self.blocks_path)
        self.raw_blocks = array('c')
        # Read off the size header
        fh.read(4)
        # Copy into the array in chunks
        chunk = fh.read(2048)
        while chunk:
            self.raw_blocks.extend(chunk)
            chunk = fh.read(2048)
        fh.close()
    
    def get_offset(self, x, y, z):
        "Turns block coordinates into a data offset"
        assert 0 <= x < self.x
        assert 0 <= y < self.y
        assert 0 <= z < self.z
        return y*(self.x*self.z) + z*(self.x) + x

    def get_coords(self, offset):
        "Turns a data offset into coordinates"
        x = offset % self.x
        z = (offset // self.x) % self.z
        y = offset // (self.x * self.z)
        return x, y, z

    def world_message(self, message):
        "Sends a message out to users about this World."
        self.out_queue.put([TASK_WORLDMESSAGE, message])
    
    def admin_message(self, message):
        "Sends a message out to admins about this World."
        self.out_queue.put([TASK_ADMINMESSAGE, message])

    def send_block(self, x, y, z):
        "Tells the server to update the given block for clients."
        self.out_queue.put([TASK_BLOCKSET, (x, y, z, self[x, y, z])])
    
    def __setitem__(self, (x, y, z), block):
        "Set a block in this level to the given value."
        assert isinstance(block, str) and len(block) == 1
        # Save to queued blocks
        offset = self.get_offset(x, y, z)
        self.queued_blocks[offset] = block
        # And directly to raw blocks, if we must
        if self.raw_blocks:
            self.raw_blocks[offset] = block
        # Ask the physics engine if they'd like a look at that
        self.physics_engine.handle_change(offset, block)
    
    def __getitem__(self, (x, y, z)):
        "Return the value at position x, y, z - possibly not efficiently."
        offset = self.get_offset(x, y, z)
        try:
            return self.raw_blocks[offset]
        except (TypeError,):
            try:
                return self.queued_blocks[offset]
            except (IndexError, KeyError):
                # Expensive! Open the gzip and read the byte.
                gz = gzip.GzipFile(self.blocks_path)
                gz.seek(offset + 4)
                block = gz.read(1)
                gz.close()
                return block
    
    def flush(self):
        """
        Flushes queued blocks into the .gz file.
        Needed before sending gzipped block data to clients.
        """
        # Don't flush if there's nothing to do
        if not self.queued_blocks:
            return
        logging.log(logging.DEBUG, "Flushing %s..." % self.blocks_path)
        # Open the old and the new file
        gz = gzip.GzipFile(self.blocks_path)
        new_gz = gzip.GzipFile(self.blocks_path + ".new", 'wb', compresslevel=4)
        # Copy over the size header
        new_gz.write(gz.read(4))
        # Order the blocks we're going to write
        ordered_blocks = sorted(self.queued_blocks.items())
        # Start writing out the blocks in chunks, replacing as we go.
        chunk_size = 1024
        chunk = list(gz.read(chunk_size))
        pos = 0
        blocks_pos = 0
        chunk_end = len(chunk)
        while chunk:
            while blocks_pos < len(ordered_blocks) and ordered_blocks[blocks_pos][0] < chunk_end:
                offset, value = ordered_blocks[blocks_pos]
                chunk[offset - pos] = value
                blocks_pos += 1
            chunk_str = "".join(chunk)
            new_gz.write(chunk_str)
            pos += len(chunk)
            chunk = list(gz.read(chunk_size))
            chunk_end = pos + len(chunk)
        # Safety first. If this isn't true, there's a bug.
        assert blocks_pos == len(ordered_blocks)
        # OK, close up shop.
        gz.close()
        new_gz.close()
        self.queued_blocks = {}
        # Copy the new level over the old.
        os.remove(self.blocks_path)
        os.rename(self.blocks_path + ".new", self.blocks_path)
    
    @classmethod
    def create_new(cls, blocks_path, sx, sy, sz, levels):
        """
        Creates a new blocks file, where levels contains one character for each
        level, signifying its block type.
        """
        assert len(levels) == sy
        # Open the gzip
        fh = gzip.GzipFile(blocks_path, mode="wb")
        # Write a size header
        fh.write(struct.pack("!i", sx*sy*sz))
        # Write each level
        for level in levels:
            fh.write(chr(level)*(sx*sz))
        fh.close()
