# blockBox is copyright 2009-2011 the Arc Team, the blockBox Team and other contributors.
# blockBox is licensed under the BSD 3-Clause Modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class BuildUtilPlugin(ProtocolPlugin):
    "Commands for building utiltity functions."

    commands = {
        "ruler": "commandRuler",
        "measure": "commandRuler",
        "paint": "commandPaint",
        "bind": "commandBind",
        "material": "commandBind",
        "replace": "commandReplace",
        "brep": "commandReplace",
        "creplace": "commandCreplace",
        "crep": "commandCreplace",
        "fill": "commandFill",
        "copy": "commandCopy",
        "paste": "commandPaste",
        "rotate": "commandRotate"
    }

    hooks = {
        "preblockchange": "preBlockChanged",
        "blockchange": "blockChanged",
    }

    def gotClient(self):
        self.painting = False
        self.block_overrides = {}

    def preBlockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        if block is BLOCK_AIR and self.painting:
            return selected_block

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        if block in self.block_overrides:
            return self.block_overrides[block]

    def canBreakAdminBlocks(self):
        "Shortcut for checking permissions."
        if hasattr(self.client, "world"):
            return self.client.isOp()
        else:
            return False

    @config("category", "world")
    def commandRuler(self, parts, fromloc, overriderank):
        "/ruler - Guest\nAliases: measure\nCounts the amount of blocks between two clicks."
        # Use the last two block places
        try:
            x, y, z = self.client.last_block_changes[0]
            x2, y2, z2 = self.client.last_block_changes[1]
        except IndexError:
            self.client.sendServerMessage("You have not clicked two blocks yet.")
            return
        xRange, yRange, zRange = abs(x - x2) + 1, abs(y - y2) + 1, abs(z - z2) + 1
        self.client.sendServerMessage("X = %d, Y = %d, Z = %d" % (xRange, yRange, zRange))

    @config("category", "build")
    def commandPaint(self, parts, fromloc, overriderank):
        "/paint - Guest\nLets you break-and-build in one move. Toggle."
        if self.painting:
            self.painting = False
            self.client.sendServerMessage("Painting mode is now off.")
        else:
            self.painting = True
            self.client.sendServerMessage("Painting mode is now on.")

    @config("category", "build")
    def commandAir(self, params, fromloc, overriderank):
        "/air - Guest\nAliases: place, stand\nPuts a block under you for easier building in the air."
        self.client.sendPacked(TYPE_BLOCKSET, self.client.x >> 5, (self.client.y >> 5) - 3, (self.client.z >> 5), BLOCK_WHITE)

    @config("category", "build")
    def commandBind(self, parts, fromloc, overriderank):
        "/bind blockA blockB - Guest\nAliases: material\nBinds blockB to blockA."
        if len(parts) == 1:
            if self.block_overrides:
                temp = tuple(self.block_overrides)
                for each in temp:
                    del self.block_overrides[each]
                self.client.sendServerMessage("All blocks are back to normal.")
                del temp
                return
            self.client.sendServerMessage("Please enter two block types.")
        elif len(parts) == 2:
            try:
                old = self.client.GetBlockValue(parts[1])
            except:
                return
            if old == None:
                return
            if old in self.block_overrides:
                del self.block_overrides[old]
                self.client.sendServerMessage("%s is back to normal." % parts[1])
            else:
                self.client.sendServerMessage("Please enter two block types.")
        else:
            old = self.client.GetBlockValue(parts[1])
            new = self.client.GetBlockValue(parts[2])
            if old == None or new == None:
                return
            name = parts[2].lower()
            old_name = parts[1].lower()
            self.block_overrides[old] = new
            self.client.sendServerMessage("%s will turn into %s." % (old_name, name))

    def commandBuild(self, parts, fromloc, overrriderank):
        "/build water|watervator|lava|stilllava|grass|doublestep - Guest\nAliases: b\nLets you build special blocks."
        if self.client.isOp():
            possibles = {
                "air": (BLOCK_AIR, BLOCK_GLASS, "Glass"),
                "water": (BLOCK_WATER, BLOCK_INDIGO_CLOTH, "Dark Blue cloth"),
                "watervator": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
                "stillwater": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
                "lava": (BLOCK_LAVA, BLOCK_ORANGE_CLOTH, "Orange cloth"),
                "stilllava": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
                "lavavator": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
                "grass": (BLOCK_GRASS, BLOCK_GREEN_CLOTH, "Green cloth"),
                "doublestep": (BLOCK_DOUBLE_STAIR, BLOCK_WOOD, "Wood")
            }
        else:
            possibles = {
                "air": (BLOCK_AIR, BLOCK_GLASS, "Glass"),
                "water": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
                "watervator": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
                "stillwater": (BLOCK_STILL_WATER, BLOCK_BLUE_CLOTH, "Blue cloth"),
                "lava": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
                "stilllava": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
                "lavavator": (BLOCK_STILL_LAVA, BLOCK_RED_CLOTH, "Red cloth"),
                "grass": (BLOCK_GRASS, BLOCK_GREEN_CLOTH, "Green cloth"),
                "doublestep": (BLOCK_DOUBLE_STAIR, BLOCK_WOOD, "Wood")
            }
        if len(parts) == 1:
            self.client.sendServerMessage("Specify a type to toggle.")
        else:
            name = parts[1].lower()
            try:
                new, old, old_name = possibles[name]
            except KeyError:
                self.client.sendServerMessage("'%s' is not a special block type." % name)
            else:
                if old in self.block_overrides:
                    del self.block_overrides[old]
                    self.client.sendServerMessage("%s is back to normal." % old_name)
                else:
                    self.block_overrides[old] = new
                    self.client.sendServerMessage("%s will turn into %s." % (old_name, name))

    @config("category", "build")
    @config("rank", "builder")
    def commandPaste(self, parts, fromloc, overriderank):
        "/paste [x y z] - Builder\nRestore blocks saved earlier using /copy"
        if len(parts) < 4 and len(parts) != 1:
            self.client.sendServerMessage("Please enter a coordinate triplet.")
        else:
            if len(parts) == 1:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not placed a marker yet.")
                    return
            else:
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                    z = int(parts[3])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            # Check whether we have anything saved
            try:
                num_saved = len(self.client.bsaved_blocks)
                self.client.sendServerMessage("Loading %d blocks..." % num_saved)
            except AttributeError:
                self.client.sendServerMessage("Please /copy something first.")
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                try:
                    for i, j, k, block in self.client.bsaved_blocks:
                        if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                            return
                        rx = x + i
                        ry = y + j
                        rz = z + k
                        world[rx, ry, rz] = block
                        self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
                        self.client.sendBlock(rx, ry, rz, block)
                        self.client.total += 1
                        yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds paste error.")
                    return
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == 'user':
                        self.client.finalizeMassCMD('paste', self.client.total)
                        self.client.total = 0
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "builder")
    def commandCopy(self, parts, fromloc, overriderank):
        "/copy [x y z x2 y2 z2] - Builder\nCopy blocks using specified offsets."
        if len(parts) < 7 and len(parts) != 1:
            self.client.sendServerMessage("Please enter 2 coordinate triplets.")
        else:
            if len(parts) == 1:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                    z = int(parts[3])
                    x2 = int(parts[4])
                    y2 = int(parts[5])
                    z2 = int(parts[6])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z

            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to copy (Limit is %s)" % limit)
                    return

            self.client.bsaved_blocks = set()
            world = self.client.world
            def doBlocks():
                try:
                    for i in range(x, x2+1):
                        for j in range(y, y2+1):
                            for k in range(z, z2+1):
                                if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                                    return
                                check_offset = world.blockstore.get_offset(i, j, k)
                                block = world.blockstore.raw_blocks[check_offset]
                                self.client.bsaved_blocks.add((i - x, j - y, k - z, block))
                                self.client.total += 1
                    self.client.finalizeMassCMD("copy", self.client.total)
                    self.client.total = 0
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds copy error.")
                    return
            threading.Thread(target=doBlocks).start()

    @config("category", "build")
    @config("rank", "builder")
    def commandRotate(self, parts, fromloc, overriderank):
        "/rotate angle - Builder\nAllows you to rotate what you copied."
        if len(parts) < 2:
            self.client.sendServerMessage("You must give an angle to rotate.")
            return
        try:
            angle = int(parts[1])
        except ValueError:
            self.client.sendServerMessage("Angle must be an integer.")
            return
        if angle % 90 != 0:
            self.client.sendServerMessage("Angle must be divisible by 90.")
            return
        rotations = angle / 90
        self.client.sendServerMessage("Rotating %s degrees..." %angle)
        for rotation in range(rotations):
            tempblocks = set()
            xmax = zmax = 0
            try:
                for x, y, z, block in self.client.bsaved_blocks:
                    if x > xmax:
                        xmax = x
                    if z > zmax:
                        zmax = z
            except:
                self.client.sendServerMessage("You haven't used /copy yet.")
                return
            for x, y, z, block in self.client.bsaved_blocks:
                tempx = x
                tempz = z
                x = zmax - tempz
                z = tempx
                tempblocks.add((x, y, z, block))
                self.client.total += 1
            self.client.bsaved_blocks = tempblocks
        if fromloc == 'user':
            self.client.finalizeMassCMD('rotate', self.client.total)
            self.client.total = 0

    @config("category", "build")
    @config("rank", "builder")
    def commandReplace(self, parts, fromloc, overriderank):
        "/replace blockA blockB [x y z x2 y2 z2] - Builder\nAliases: brep\nReplaces all blocks of blockA in this area to blockB."
        if len(parts) < 9 and len(parts) != 3:
            self.client.sendServerMessage("Please enter 2 types (and possibly two coord triples)")
        else:
            blockA = self.client.GetBlockValue(parts[1])
            blockB = self.client.GetBlockValue(parts[2])
            if blockA == None or blockB == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                    x2 = int(parts[6])
                    y2 = int(parts[7])
                    z2 = int(parts[8])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to replace (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                try:
                    for i in range(x, x2+1):
                        for j in range(y, y2+1):
                            for k in range(z, z2+1):
                                if not self.client.AllowedToBuild(i, j, k) and fromloc != 'user':
                                    return
                                check_offset = world.blockstore.get_offset(i, j, k)
                                block = world.blockstore.raw_blocks[check_offset]
                                if block == blockA:
                                    world[i, j, k] = blockB
                                    self.client.runHook("blockchange", x, y, z, ord(block), ord(block), fromloc)
                                    self.client.queueTask(TASK_BLOCKSET, (i, j, k, blockB), world=world)
                                    self.client.sendBlock(i, j, k, blockB)
                                    self.client.total += 1
                                    yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds replace error.")
                    return
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 50 blocks
                try:
                    for x in range(50):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == 'user':
                        self.client.finalizeMassCMD('replace', self.client.total)
                        self.client.total = 0
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandCreplace(self, parts, fromloc, overriderank):
        "/creplace typeA typeB typeC [x y z x2 y2 z2] - Op\nAliases: crep\nReplaces all blocks of typeA in this cuboid to typeB and typeC."
        if len(parts) < 10 and len(parts) != 4:
            self.client.sendServerMessage("Please enter the type to replace and two other types")
            self.client.sendServerMessage("(and possibly two coord triples)")
        else:
            blockA = self.client.GetBlockValue(parts[1])
            blockB = self.client.GetBlockValue(parts[2])
            blockC = self.client.GetBlockValue(parts[3])
            if blockA == None or blockB == None or blockC == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[4])
                    y = int(parts[5])
                    z = int(parts[6])
                    x2 = int(parts[7])
                    y2 = int(parts[8])
                    z2 = int(parts[9])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
            limit = self.client.getBlbLimit()
            if limit != -1:
                # Stop them doing silly things
                if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
                    self.client.sendServerMessage("Sorry, that area is too big for you to creplace (Limit is %s)" % limit)
                    return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                try:
                    for i in range(x, x2+1):
                        for j in range(y, y2+1):
                            for k in range(z, z2+1):
                                blockcheck = world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)]
                                if blockcheck == blockA:
                                    if (i + j + k) % 2 == 0:
                                        var_block = blockB
                                    else:
                                        var_block = blockC
                                    world[i, j, k] = var_block
                                    self.client.queueTask(TASK_BLOCKSET, (i, j, k, var_block), world=world)
                                    self.client.sendBlock(i, j, k, var_block)
                                    self.client.total += 1
                                yield
                except AssertionError:
                    self.client.sendServerMessage("Out of bounds creplace error.")
                    return
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 50 blocks
                try:
                    for x in range(50):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if fromloc == 'user':
                        self.client.finalizeMassCMD('creplace', self.client.total)
                        self.client.total = 0
                    pass
            do_step()

    @config("category", "build")
    @config("rank", "op")
    def commandFill(self, parts, fromloc, overriderank):
        "/fill blockname repblock [x y z x2 y2 z2] - Op\nFills the area with the block."
        if len(parts) < 9 and len(parts) != 3:
            self.client.sendServerMessage("Please enter a type and a type to replace")
            self.client.sendServerMessage("(and possibly two coord triples)")
            self.client.sendServerMessage("Note that you must place two blocks to use it.")
            self.client.sendServerMessage("The first block sets where to spread from and")
            self.client.sendServerMessage("the second block sets which directions to spread.")
        else:
            block = self.client.GetBlockValue(parts[1])
            var_repblock = self.client.GetBlockValue(parts[2])
            if block == None or var_repblock == None:
                return
            # If they only provided the type argument, use the last block place
            if len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[1]
                    x2, y2, z2 = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two points yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                    x2 = int(parts[6])
                    y2 = int(parts[7])
                    z2 = int(parts[8])
                except ValueError:
                    self.client.sendServerMessage("All coordinate parameters must be integers.")
                    return
            limit = self.client.getBlbLimit()
            if limit == 0:
                self.client.sendServerMessage("You have exceeded the fill limit for your rank. (Limit is %s)" % limit)
                return
            var_locxchecklist = [(1, 0, 0), (-1, 0, 0)]
            var_locychecklist = [(0, 1, 0), (0, -1, 0)]
            var_loczchecklist = [(0, 0, 1), (0, 0, -1)]
            var_locchecklist = []
            if x != x2:
                var_locchecklist = var_locchecklist + var_locxchecklist
            if y != y2:
                var_locchecklist = var_locchecklist + var_locychecklist
            if z != z2:
                var_locchecklist = var_locchecklist + var_loczchecklist
            if var_locchecklist == []:
                self.client.sendServerMessage("Repeated points error.")
                return
            self.var_blocklist = [(x, y, z, (-20, -20, -20))]
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            try:
                if not self.client.AllowedToBuild(x, y, z) and not overriderank:
                    self.client.sendServerMessage("You do not have permission to build here.")
                    return
                world[x, y, z] = block
                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                self.client.sendBlock(x, y, z, block)
            except:
                pass
            def generate_changes():
                var_blockchanges = 0
                while self.var_blocklist != []:
                    if limit != -1:
                        # Stop them doing silly things
                        if var_blockchanges > limit:
                            self.client.sendServerMessage("You have exceeded the fill limit for your rank (Limit is %s)" % limit)
                            return
                    i,j,k,positionprevious = self.var_blocklist[0]
                    var_blockchanges += 1
                    for offsettuple in var_locchecklist:
                        ia, ja, ka = offsettuple
                        ri, rj, rk = i + ia, j + ja, k + ka
                        if (ri, rj, rk) != positionprevious:
                            try:
                                if not self.client.AllowedToBuild(ri, rj, rk) and not overriderank:
                                    self.client.sendServerMessage("You do not have permission to build here.")
                                    return
                                checkblock = world.blockstore.raw_blocks[world.blockstore.get_offset(ri, rj, rk)]
                                if checkblock == var_repblock:
                                    world[ri, rj, rk] = block
                                    self.client.queueTask(TASK_BLOCKSET, (ri, rj, rk, block), world=world)
                                    self.client.sendBlock(ri, rj, rk, block)
                                    self.var_blocklist.append((ri, rj, rk,(i, j, k)))
                                    self.client.total += 1
                            except AssertionError:
                                pass
                            yield
                    del self.var_blocklist[0]
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step) # This is how long(in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if fromloc == 'user':
                        self.client.finalizeMassCMD('fill', self.client.total)
                        self.client.total = 0
                    pass
            do_step()