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

from twisted.internet import reactor

from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class BlbPlugin(ProtocolPlugin):
    
    commands = {
        "blb": "commandBlb",
        "draw": "commandBlb",
        "cuboid": "commandBlb",
        "cub": "commandBlb",
        "box": "commandBlb",
        "bhb": "commandHBlb",
        "hbox": "commandHBlb",
        "bwb": "commandWBlb",
        "bcb": "commandBcb",
        "bhcb": "commandBhcb",
        "bfb": "commandFBlb",
    }
    
    @build_list
    @writer_only
    def commandBlb(self, parts, byuser, overriderank):
        "/blb blockname [x y z x2 y2 z2] - Builder\nAliases: cub, cuboid, draw, box\nSets all blocks in this area to block."
        
        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
            
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
            
            if self.client.isDirector() or overriderank:
                limit = 1073741824
            elif self.client.isAdmin():
                limit = 2097152
            elif self.client.isMod():
                limit = 262144
            elif self.client.isOp():
                limit = 110592
            elif self.client.isMember():
                limit = 55296
            else:
                limit = 4062
            # Stop them doing silly things
            if (x2 - x) * (y2 - y) * (z2 - z) > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to blb.")
                return
            
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(x, x2+1):
                    for j in range(y, y2+1):
                        for k in range(z, z2+1):
                            if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
                                return
                            try:
                                world[i, j, k] = block
                                self.client.runHook("blockchange", x, y, z, block, block, byuser)
                            except AssertionError:
                                self.client.sendServerMessage("Out of bounds blb error.")
                                return
                            self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                            self.client.sendBlock(i, j, k, block)
                            yield
            
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if byuser:
                        self.client.sendServerMessage("Your blb just completed.")
                    pass
            do_step()
        #count = ((1+(x2 - x)) * (1+(y2 - y)) * (1+(z2 - z))/3)
        #self.client.sendServerMessage("Your blb finished, with %s blocks." % count)

    @build_list
    @writer_only
    def commandHBlb(self, parts, byuser, overriderank):
        "/bhb blockname [x y z x2 y2 z2] - Builder\nAliases: hbox\nSets all blocks in this area to block, hollow."

        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a block type")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return

            # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return

            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z

            if self.client.isDirector() or overriderank:
                limit = 1073741824
            elif self.client.isAdmin():
                limit = 2097152
            elif self.client.isMod():
                limit = 262144
            elif self.client.isOp():
                limit = 110592
            elif self.client.isMember():
                limit = 55296
            else:
                limit = 4062
            # Stop them doing silly things
            if (x2 - x) * (y2 - y) * (z2 - z) > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to bhb.")
                return

            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(x, x2+1):
                    for j in range(y, y2+1):
                        for k in range(z, z2+1):
                            if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
                                return
                            if i==x or i==x2 or j==y or j==y2 or k==z or k==z2:
                                try:
                                   world[i, j, k] = block
                                   self.client.runHook("blockchange", x, y, z, block, block, byuser)
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds bhb error.")
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                self.client.sendBlock(i, j, k, block)
                                yield

            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if byuser:
                        self.client.sendServerMessage("Your bhb just completed.")
                    pass
            do_step()

    @build_list
    @writer_only
    def commandWBlb(self, parts, byuser, overriderank):
        "/bwb blockname [x y z x2 y2 z2] - Builder\nBuilds four walls between the two areas.\nHollow, with no roof or floor."

        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a block type")
        else:
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return

            # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return

            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z

            if self.client.isDirector() or overriderank:
                limit = 1073741824
            elif self.client.isAdmin():
                limit = 2097152
            elif self.client.isMod():
                limit = 262144
            elif self.client.isOp():
                limit = 110592
            elif self.client.isMember():
                limit = 55296
            else:
                limit = 4062
            # Stop them doing silly things
            if (x2 - x) * (y2 - y) * (z2 - z) > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to bwb.")
                return

            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(x, x2+1):
                    for j in range(y, y2+1):
                        for k in range(z, z2+1):
                            if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
                                return
                            if i==x or i==x2 or k==z or k==z2:
                                try:
                                   world[i, j, k] = block
                                   self.client.runHook("blockchange", x, y, z, block, block, byuser)
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds bwb error.")
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                self.client.sendBlock(i, j, k, block)
                                yield

            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
                except StopIteration:
                    if byuser:
                        self.client.sendServerMessage("Your bwb just completed.")
                    pass
            do_step()

    @build_list
    @writer_only
    def commandBcb(self, parts, byuser, overriderank):
        "/bcb blockname blockname2 [x y z x2 y2 z2] - Builder\nSets all blocks in this area to block, checkered."
        
        if len(parts) < 9 and len(parts) != 3:
            self.client.sendServerMessage("Please enter two types (and possibly two coord triples)")
        else:
            # Try getting block2 as a direct integer type.
            try:
                block2 = chr(int(parts[2]))
            except ValueError:
                # OK, try a symbolic type.
                try:
                    block2 = chr(globals()['BLOCK_%s' % parts[2].upper()])
                except KeyError:
                    self.client.sendServerMessage("'%s' is not a valid block type." % parts[2])
                    return
            # Try getting the block as a direct integer type.
            try:
                block = chr(int(parts[1]))
            except ValueError:
                # OK, try a symbolic type.
                try:
                    block = chr(globals()['BLOCK_%s' % parts[1].upper()])
                except KeyError:
                    self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
                    return
            
            # Check the block is valid
            if ord(block) > 49:
                self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
                return
				
            op_blocks = [BLOCK_SOLID, BLOCK_WATER, BLOCK_LAVA]
            if ord(block) in op_blocks and not self.client.isOp():
                self.client.sendServerMessage("Sorry, but you can't use that block.")
                return
            
            # Check that block2 is valid
            if ord(block2) > 49:
                self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
                return
            if ord(block2) == 7:
                try:
                    username = self.client.factory.usernames[self.client.username.lower()]
                except:
                    self.client.sendServerMessage("ERROR Identity could not be confirmed")
                    return
                if username.isDirector():
                    pass
                elif username.isAdmin():
                    pass
                elif username.isMod():
                    pass
                elif username.isMember():
                    pass
                elif username.isOp():
                    pass
                else:
                    self.client.sendServerMessage("Solid is op-only")
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
                    self.client.sendServerMessage("All parameters must be integers")
                    return
            
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
            

            if self.client.isDirector() or overriderank:
                limit = 1073741824
            elif self.client.isAdmin():
                limit = 2097152
            elif self.client.isMod():
                limit = 262144
            elif self.client.isOp():
                limit = 110592
            elif self.client.isMember():
                limit = 55296
            else:
                limit = 4062
            # Stop them doing silly things
            if (x2 - x) * (y2 - y) * (z2 - z) > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to bcb.")
                return
            
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                ticker = 0
                for i in range(x, x2+1):
                    for j in range(y, y2+1):
                        for k in range(z, z2+1):
                            if not self.client.AllowedToBuild(i, j, k):
                                return
                            try:
                                if (i+j+k)%2 == 0:
                                    ticker = 1
                                else:
                                    ticker = 0
                                if ticker == 0:
                                    world[i, j, k] = block
                                else:
                                    world[i, j, k] = block2
                            except AssertionError:
                                self.client.sendServerMessage("Out of bounds bcb error.")
                                return
                            if ticker == 0:
                                self.client.queueTask(TASK_BLOCKSET, (i, j, k, block2), world=world)
                                self.client.sendBlock(i, j, k, block2)
                            else:
                                self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                self.client.sendBlock(i, j, k, block)
                            yield
            
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
                except StopIteration:
                    self.client.sendServerMessage("Your bcb just completed.")
                    pass
            do_step()

    @build_list
    @writer_only
    def commandBhcb(self, parts, byuser, overriderank):
        "/bhcb blockname blockname2 [x y z x2 y2 z2] - Builder\nSets all blocks in this area to blocks, checkered hollow."

        if len(parts) < 9 and len(parts) != 3:
            self.client.sendServerMessage("Please enter two block types")
        else:
            # Try getting block2 as a direct integer type.
            try:
                block2 = chr(int(parts[2]))
            except ValueError:
                # OK, try a symbolic type.
                try:
                    block2 = chr(globals()['BLOCK_%s' % parts[2].upper()])
                except KeyError:
                    self.client.sendServerMessage("'%s' is not a valid block type." % parts[2])
                    return
                
            # Try getting the block as a direct integer type.
            try:
                block = chr(int(parts[1]))
            except ValueError:
                # OK, try a symbolic type.
                try:
                    block = chr(globals()['BLOCK_%s' % parts[1].upper()])
                except KeyError:
                    self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
                    return

            # Check the block is valid
            if ord(block) > 49:
                self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
                return
            op_blocks = [BLOCK_SOLID, BLOCK_WATER, BLOCK_LAVA]
            if ord(block) in op_blocks and not self.client.isOp():
                self.client.sendServerMessage("Sorry, but you can't use that block.")
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
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return

            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z

            if self.client.isDirector() or overriderank:
                limit = 1073741824
            elif self.client.isAdmin():
                limit = 2097152
            elif self.client.isMod():
                limit = 262144
            elif self.client.isOp():
                limit = 110592
            elif self.client.isMember():
                limit = 55296
            else:
                limit = 4062
            # Stop them doing silly things
            if (x2 - x) * (y2 - y) * (z2 - z) > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to bhcb.")
                return

            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                ticker = 0
                for i in range(x, x2+1):
                    for j in range(y, y2+1):
                        for k in range(z, z2+1):
                            if not self.client.AllowedToBuild(i, j, k):
                                return
                            if i==x or i==x2 or j==y or j==y2 or k==z or k==z2:
                                try:
                                    if (i+j+k)%2 == 0:
                                        ticker = 1
                                    else:
                                        ticker = 0
                                    if ticker == 0:
                                        world[i, j, k] = block
                                    else:
                                        world[i, j, k] = block2

                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds bhcb error.")
                                    return
                                if ticker == 0:
                                    self.client.queueTask(TASK_BLOCKSET, (i, j, k, block2), world=world)
                                    self.client.sendBlock(i, j, k, block2)
                                else:
                                    self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                    self.client.sendBlock(i, j, k, block)
                                yield

            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
                except StopIteration:
                    self.client.sendServerMessage("Your bhcb just completed.")
                    pass
            do_step()

    @build_list
    @writer_only
    def commandFBlb(self, parts, byuser, overriderank):
        "/bfb blockname [x y z x2 y2 z2] - Builder\nSets all blocks in this area to block, wireframe."

        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a block type")
        else:
            # Try getting the block as a direct integer type.
            try:
                block = chr(int(parts[1]))
            except ValueError:
                # OK, try a symbolic type.
                try:
                    block = chr(globals()['BLOCK_%s' % parts[1].upper()])
                except KeyError:
                    self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
                    return

            # Check the block is valid
            if ord(block) > 49:
                self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
                return
            op_blocks = [BLOCK_SOLID, BLOCK_WATER, BLOCK_LAVA]
            if ord(block) in op_blocks and not self.client.isOp():
                self.client.sendServerMessage("Sorry, but you can't use that block.")
                return

            # If they only provided the type argument, use the last two block places
            if len(parts) == 2:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return

            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z

            if self.client.isDirector() or overriderank:
                limit = 1073741824
            elif self.client.isAdmin():
                limit = 2097152
            elif self.client.isMod():
                limit = 262144
            elif self.client.isOp():
                limit = 110592
            elif self.client.isMember():
                limit = 55296
            else:
                limit = 4062
            # Stop them doing silly things
            if (x2 - x) * (y2 - y) * (z2 - z) > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to bfb.")
                return

            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(x, x2+1):
                    for j in range(y, y2+1):
                        for k in range(z, z2+1):
                            if not self.client.AllowedToBuild(i, j, k):
                                return
                            if (i==x and j==y) or (i==x2 and j==y2) or (j==y2 and k==z2) or (i==x2 and k==z2) or (j==y and k==z) or (i==x and k==z) or (i==x and k==z2) or (j==y and k==z2) or (i==x2 and k==z) or (j==y2 and k==z) or (i==x and j==y2) or (i==x2 and j==y):
                                try:
                                   world[i, j, k] = block

                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds bfb error.")
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                self.client.sendBlock(i, j, k, block)
                                yield

            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
                except StopIteration:
                    self.client.sendServerMessage("Your bfb just completed.")
                    pass
            do_step()
