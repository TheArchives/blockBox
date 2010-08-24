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

import gzip
import struct
import os
import traceback
import logging
from Queue import Empty
from ConfigParser import RawConfigParser as ConfigParser
from array import array
from deferred import Deferred
from blockstore import BlockStore
from constants import *

class World(object):
    """
    Represents... well, a World.
    This is the new, efficient version, that uses the disk as the main backing
    store. Any changes are stored in self.queued_blocks (and that is looked in
    for specfic blook lookups first) until the level is flushed, at which point
    the gzip on disk is updated with the new blocks.
    """

    def __init__(self, basename, load=True):
        self.WorldVars = dict()
        self.basename = basename
        self.blocks_path = os.path.join(basename, "blocks.gz")
        self.meta_path = os.path.join(basename, "world.meta")
        # Other settings
        self.owner = "N/A"
        self.ops = set()
        self.writers = set()
        self.all_write = True
        self.admin_blocks = True
        self.private = False
        self.highlight_ops = True
        self._physics = False
        self._finite_water = False
        self.is_archive = False
        self.teleports = {}
        self.messages = {}
        self.commands = {}
        self.mines = {}
        self.id = None
        self.factory = None
        self.autoshutdown = True
        self.saving = False
        self.users = {}
        self.rpg = False
        self.global_chat = True
        self.zoned = False
        self.userzones = {}
        self.rankzones = {}
        # Dict of deferreds to call when a block is gotten.
        self.blockgets = {}
        self.ASD = None
        # Current deferred to call after a flush is complete
        self.flush_deferred = None
        if load:
            assert os.path.isfile(self.blocks_path), "No blocks file: %s" % self.blocks_path
            self.load_meta()

    def start(self):
        "Starts up this World; we spawn a BlockStore, and run it."
        self.blockstore = BlockStore(self.blocks_path, self.x, self.y, self.z)
        self.blockstore.start()
        # If physics is on, turn it on
        if self._physics:
            self.blockstore.in_queue.put([TASK_PHYSICSON])
        if self._finite_water:
            self.blockstore.in_queue.put([TASK_FWATERON])
            
    def stop(self):
        "Signals the BlockStore to stop."
        self.blockstore.in_queue.put([TASK_STOP])
        self.save_meta()

    def unload(self):
        self.factory.unloadWorld(self.id,True)

    def read_queue(self):
        "Reads messages from the BlockStore and acts on them."
        try:
            for i in range(1000):
                task = self.blockstore.out_queue.get_nowait()
                try:
                    # We might have been told a flush is complete!
                    if task[0] is TASK_FLUSH:
                        if self.flush_deferred:
                            self.flush_deferred.callback(None)
                            self.flush_deferred = None
                    # Or got a response to a BLOCKGET
                    elif task[0] is TASK_BLOCKGET:
                        try:
                            self.blockgets[task[1]].callback(task[2])
                            del self.blockgets[task[1]]
                        except KeyError:
                            pass # We already sent this one.
                    # Or the physics changes a block
                    elif task[0] is TASK_BLOCKSET:
                        self.factory.queue.put((self, TASK_BLOCKSET, task[1]))
                    # Or there's a world message
                    elif task[0] is TASK_WORLDMESSAGE:
                        self.factory.queue.put((self, TASK_WORLDMESSAGE, (255, self, task[1])))
                    # Or a message for the admins
                    elif task[0] is TASK_ADMINMESSAGE:
                        self.factory.queue.put((self, TASK_ADMINMESSAGE, (task[1] % {"id": self.id},)))
                    # ???
                    else:
                        raise ValueError("Unknown World task: %s" % task)
                except:
                    logging.log(logging.ERROR, traceback.format_exc())
        except Empty:
            pass

    def get_physics(self):
        return self._physics

    def set_physics(self, value):
        self._physics = value
        if hasattr(self, "blockstore"):
            if value:
                self.blockstore.in_queue.put([TASK_PHYSICSON])
            else:
                self.blockstore.in_queue.put([TASK_PHYSICSOFF])
    physics = property(get_physics, set_physics)

    def get_finite_water(self):
        return self._finite_water

    def set_finite_water(self, value):
        self._finite_water = value
        if hasattr(self, "blockstore"):
            if value:
                self.blockstore.in_queue.put([TASK_FWATERON])
            else:
                self.blockstore.in_queue.put([TASK_FWATEROFF])
    finite_water = property(get_finite_water, set_finite_water)

    def start_unflooding(self):
        self.blockstore.in_queue.put([TASK_UNFLOOD])

    def load_meta(self):
        config = ConfigParser()
        config.read(self.meta_path)
        self.x = config.getint("size", "x")
        self.y = config.getint("size", "y")
        self.z = config.getint("size", "z")
        self.spawn = (
            config.getint("spawn", "x"),
            config.getint("spawn", "y"),
            config.getint("spawn", "z"),
            config.getint("spawn", "h"),
        )
        if config.has_section("autoshutdown"):
            self.autoshutdown = config.get("autoshutdown", "autoshutdown")
        if config.has_section("owner"):
            self.owner = config.get("owner", "owner")
        if config.has_section("ops"):
            self.ops = set(x.lower() for x in config.options("ops"))
        else:
            self.ops = set()
        if config.has_section("writers"):
            self.writers = set(x.lower() for x in config.options("writers"))
        else:
            self.writers = set()
        if config.has_section("permissions"):
            if config.has_option("permissions", "all_write"):
                self.all_write = config.getboolean("permissions", "all_write")
            else:
                self.all_write = True
            if config.has_option("permissions", "admin_blocks"):
                self.admin_blocks = config.getboolean("permissions", "admin_blocks")
            else:
                self.admin_blocks = True
            if config.has_option("permissions", "private"):
                self.private = config.getboolean("permissions", "private")
            else:
                self.private = False
            if config.has_option("permissions", "zoned"):
                self.zoned = config.getboolean("permissions", "zoned")
            else:
                self.zoned = True
        if config.has_section("display"):
            if config.has_option("display", "highlight_ops"):
                self.highlight_ops = config.getboolean("display", "highlight_ops")
            else:
                self.highlight_ops = True
            if config.has_option("display", "physics"):
                self.physics = config.getboolean("display", "physics")
            else:
                self.physics = False
            if config.has_option("display", "finite_water"):
                self.finite_water = config.getboolean("display", "finite_water")
            else:
                self.finite_water = False
        if config.has_section("chat"):
            if config.has_option("chat", "global_chat"):
                self.global_chat = config.getboolean("chat", "global_chat")
            else:
                self.global_chat = True
        self.teleports = {}
        if config.has_section("teleports"):
            for option in config.options("teleports"):
                offset = int(option)
                destination = [x.strip() for x in config.get("teleports", option).split(",")]
                coords = map(int, destination[1:])
                if len(coords) == 3:
                    coords = coords + [0]
                if not (0 <= coords[3] <= 255):
                    coords[3] = 0
                self.teleports[offset] = destination[:1] + coords
        self.messages = {}
        if config.has_section("messages"):
            for option in config.options("messages"):
                self.messages[int(option)] = config.get("messages", option)
        self.commands = {}
        if config.has_section("commands"):
            for option in config.options("commands"):
                cmd = config.get("commands", option)
                listofcmd = cmd.split("&n")
                for x in listofcmd:
                    x = x.replace("&n", "")
                    if x == "":
                        listofcmd.remove(x)
                self.commands[int(option)] = listofcmd
        self.mines = list([])
        if config.has_section("mines"):
            for option in config.options("mines"):
                self.mines.append(int(option))
        self.userzones = {}
        if config.has_section("userzones"):
            for option in config.options("userzones"):
                destination = [x.strip() for x in config.get("userzones", option).split(",")]
                coords = map(int, destination[1:7])
                users = map(str, destination[7:])
                i=1
                while True:
                    if not i in self.userzones:
                        self.userzones[i] = destination[:1] + coords + users
                        break
                    else:
                        i+=1
        self.rankzones = {}
        if config.has_section("rankzones"):
            for option in config.options("rankzones"):
                user = option
                destination = [x.strip() for x in config.get("rankzones", option).split(",")]
                coords = map(int, destination[1:7])
                i=1
                while True:
                    if not i in self.rankzones:
                        self.rankzones[i] = destination[:1] + coords + destination[7:]
                        break
                    else:
                        i+=1

    @property
    def store_raw_blocks(self):
        return self.physics

    def saved(self):
        self.factory.saving = False

    def flush(self):
        self.blockstore.in_queue.put([TASK_FLUSH,self.saved])

    def save_meta(self):
        config = ConfigParser()
        config.add_section("plus")
        config.add_section("size")
        config.add_section("spawn")
        config.add_section("owner")
        config.add_section("ops")
        config.add_section("writers")
        config.add_section("permissions")
        config.add_section("display")
        config.add_section("teleports")
        config.add_section("messages")
        config.add_section("commands")
        config.add_section("mines")
        config.add_section("autoshutdown")
        config.add_section("userzones")
        config.add_section("rankzones")
        config.add_section("chat")
        config.set("size", "x", str(self.x))
        config.set("size", "y", str(self.y))
        config.set("size", "z", str(self.z))
        config.set("spawn", "x", str(self.spawn[0]))
        config.set("spawn", "y", str(self.spawn[1]))
        config.set("spawn", "z", str(self.spawn[2]))
        config.set("spawn", "h", str(self.spawn[3]))
        # Store Autoshutdown
        config.set("autoshutdown", "autoshutdown", str(self.autoshutdown))
        # Store owner
        config.set("owner", "owner", str(self.owner))
        # Store ops
        for op in self.ops:
            config.set("ops", op, "true")
        # Store writers
        for writer in self.writers:
            config.set("writers", writer, "true")
        # Store permissions
        config.set("permissions", "all_write", str(self.all_write))
        config.set("permissions", "admin_blocks", str(self.admin_blocks))
        config.set("permissions", "private", str(self.private))
        config.set("permissions", "zoned", str(self.zoned))
        # Store display settings
        config.set("display", "highlight_ops", str(self.highlight_ops))
        config.set("display", "physics", str(self.physics))
        config.set("display", "finite_water", str(self.finite_water))
        # Store teleports
        for offset, dest in self.teleports.items():
            config.set("teleports", str(offset), ", ".join(map(str, dest)))
        # Store chat settings
        config.set("chat", "global_chat", str(self.global_chat))
        # Store messages
        for offset, msg in self.messages.items():
            config.set("messages", str(offset), msg)
        # Store commands
        for offset, cmd in self.commands.items():
            cmdstr = ""
            for x in cmd:
                cmdstr = cmdstr + x + "&n"
            config.set("commands", str(offset), cmdstr)
        #store mines
        for offset in self.mines:
            config.set("mines", str(offset), "True")
        # Store user zones
        for name, zone in self.userzones.items():
            config.set("userzones", str(name), ", ".join(map(str, zone)))
        # Store rank zones
        for name, zone in self.rankzones.items():
            config.set("rankzones", str(name), ", ".join(map(str, zone)))
        fp = open(self.meta_path, "w")
        config.write(fp)
        fp.close()

    @classmethod
    def create(cls, basename, x, y, z, sx, sy, sz, sh, levels):
        "Creates a new World file set"
        os.mkdir(basename)
        world = cls(basename, load=False)
        BlockStore.create_new(world.blocks_path, x, y, z, levels)
        world.x = x
        world.y = y
        world.z = z
        world.spawn = (sx, sy, sz, sh)
        world.save_meta()
        world.load_meta()
        return world

    def add_teleport(self, x, y, z, to):
        offset = self.get_offset(x, y, z)
        self.teleports[offset] = to

    def delete_teleport(self, x, y, z):
        offset = self.get_offset(x, y, z)
        try:
            del self.teleports[offset]
            return True
        except KeyError:
            return False

    def get_teleport(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return self.teleports[offset]

    def has_teleport(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return offset in self.teleports

    def add_message(self, x, y, z, msg):
        offset = self.get_offset(x, y, z)
        self.messages[offset] = msg

    def delete_message(self, x, y, z):
        offset = self.get_offset(x, y, z)
        try:
            del self.messages[offset]
            return True
        except KeyError:
            return False

    def get_message(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return self.messages[offset]

    def has_message(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return offset in self.messages
        
    def add_command(self, x, y, z, cmd):
        offset = self.get_offset(x, y, z)
        self.commands[offset] = cmd

    def delete_command(self, x, y, z):
        offset = self.get_offset(x, y, z)
        try:
            del self.commands[offset]
            return True
        except KeyError:
            return False

    def get_command(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return self.commands[offset]

    def has_command(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return offset in self.commands

    def clear_teleports(self):
        self.teleports = {}

    def add_mine(self, x, y, z):
        offset = self.get_offset(x, y, z)
        self.mines.append(offset)

    def delete_mine(self, x, y, z):
        offset = self.get_offset(x, y, z)
        try:
            self.mines.remove(offset)
            return True
        except KeyError:
            return False

    def has_mine(self, x, y, z):
        offset = self.get_offset(x, y, z)
        return offset in self.mines    
        
    def clear_mines(self):
        self.mines = list([])

    def __getitem__(self, (x, y, z)):
        "Gets the value of a block. Returns a Deferred."
        self.blockstore.in_queue.put([TASK_BLOCKGET, (x, y, z)])
        if (x, y, z) not in self.blockgets:
            self.blockgets[x, y, z] = Deferred()
        return self.blockgets[x, y, z]

    def __setitem__(self, (x, y, z), block):
        "Sets the value of a block."
        assert isinstance(block, str) and len(block) == 1
        # Make sure this is inside boundaries
        self.get_offset(x, y, z)
        self.blockstore.in_queue.put([TASK_BLOCKSET, (x, y, z), block])

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

    def get_gzip_handle(self):
        """
        Returns a Deferred that will eventually yield a handle to this world's
        gzip blocks file (gzipped, not the contents).
        """
        # First, queue it
        self.blockstore.in_queue.put([TASK_FLUSH,self.saved])
        # Now, make the flush deferred if we haven't.
        if not self.flush_deferred:
            self.flush_deferred = Deferred()
        # Next, make a deferred for us to return
        handle_deferred = Deferred()
        # Now, make a function that will call that on the first one
        def on_flush(result):
            handle_deferred.callback((
                open(self.blocks_path, "rb"),
                os.stat(self.blocks_path).st_size,
            ))
        self.flush_deferred.addCallback(on_flush)
        return handle_deferred
