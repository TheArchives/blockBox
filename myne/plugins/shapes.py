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

class ShapesPlugin(ProtocolPlugin):
    
    commands = {
        "sphere": "commandSphere",
        "hsphere": "commandHSphere",
        "curve": "commandCurve",
        "line": "commandLine",
        "pyramid": "commandPyramid",
        "csphere": "commandCsphere",
        "circle": "commandCircle",
        "dome": "commandDome",
        "ellipsoid": "commandEllipsoid",
        "ell": "commandEllipsoid",
        "polytri": "commandPolytri"
    }
    
    @build_list
    @writer_only
    def commandSphere(self, parts, byuser, overriderank):
        "/sphere blocktype [x y z] radius - Builder\nPlace/delete a block and /sphere block radius"
        if len(parts) < 6 and len(parts) != 3:
            self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
        else:
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be a Number.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
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
            if (radius*2)**3>limit:
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(-radius-1, radius):
                    for j in range(-radius-1, radius):
                        for k in range(-radius-1, radius):
                            if (i**2 + j**2 + k**2)**0.5 < radius:
                                if not self.client.AllowedToBuild(x+i, y+j, z+k):
                                    return
                                try:
                                    world[x+i, y+j, z+k] = block
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds sphere error.")
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                self.client.sendBlock(x+i, y+j, z+k, block)
                                yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    self.client.sendServerMessage("Your sphere just completed.")
                    pass
            do_step()

    @build_list
    @writer_only
    def commandHSphere(self, parts, byuser, permissionoverride):
        "/hsphere blocktype [x y z] radius - Builder\nPlace/delete a block, makes a hollow /sphere"
        if len(parts) < 6 and len(parts) != 3:
            self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
        else:
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be a Number.")
                return
            block = self.client.GetBlockValue(parts[1])
            if block == None:
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
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
            if (radius*2)**3>limit:
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(-radius-1, radius):
                    for j in range(-radius-1, radius):
                        for k in range(-radius-1, radius):
                            if (i**2 + j**2 + k**2)**0.5 < radius and (i**2 + j**2 + k**2)**0.5 > radius-1.49:
                                if not self.client.AllowedToBuild(x+i, y+j, z+k) and not permissionoverride:
                                    return
                                try:
                                    world[x+i, y+j, z+k] = block
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds sphere error.")
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                self.client.sendBlock(x+i, y+j, z+k, block)
                                yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if byuser:    
                        self.client.sendServerMessage("Your hsphere just completed.")
                    pass
            do_step()

    @build_list
    @member_only
    def commandCurve(self, parts, byuser, overriderank):
        "/curve blockname [x y z x2 y2 z2 x3 y3 z3] - Member\nSets a line of blocks along three points to block."
        if len(parts) < 11 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly three coord triples)")
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
                    x3, y3, z3 = self.client.thirdcoord
                except:
                    self.client.sendServerMessage("You have not recorded three points yet (use /recthird).")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                    x3 = int(parts[8])
                    y3 = int(parts[9])
                    z3 = int(parts[10])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
            if (x==x2 and y==y2 and z==z2) or (x==x3 and y==y3 and z==z3) or (x3==x2 and y3==y2 and z3==z2):
                self.client.sendServerMessage("Repeated points error.")
                return
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
            if 2*((x-x2)**2+(y-y2)**2+(z-z2)**2)**0.5+2*((x2-x3)**2+(y2-y3)**2+(z2-z3)**2)**0.5 > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to curve.")
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():                
                #curve list
                steps1 = float(2*((x3-x)**2+(y3-y)**2+(z3-z)**2)**0.5)
                steps2 = float(2*((x2-x3)**2+(y2-y3)**2+(z2-z3)**2)**0.5) + steps1
                coordinatelist = []
                for i in range(steps2+1):
                    t = float(i)
                    var_x = (x3-x)*((t)/(steps1) * (t-steps2)/(steps1-steps2)) + (x2-x)*((t)/(steps2) * (t-steps1)/(steps2-steps1))
                    var_y = (y3-y)*((t)/(steps1) * (t-steps2)/(steps1-steps2)) + (y2-y)*((t)/(steps2) * (t-steps1)/(steps2-steps1))
                    var_z = (z3-z)*((t)/(steps1) * (t-steps2)/(steps1-steps2)) + (z2-z)*((t)/(steps2) * (t-steps1)/(steps2-steps1))
                    coordinatelist.append((int(var_x)+x,int(var_y)+y,int(var_z)+z))
                finalcoordinatelist = []
                finalcoordinatelist = [coordtuple for coordtuple in coordinatelist if coordtuple not in finalcoordinatelist]
                for coordtuple in finalcoordinatelist:
                    i = coordtuple[0]
                    j = coordtuple[1]
                    k = coordtuple[2]
                    if not self.client.AllowedToBuild(i, j, k):
                        return
                    try:
                        world[i, j, k] = block
                    except AssertionError:
                        self.client.sendServerMessage("Out of bounds curve error.")
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
                    self.client.sendServerMessage("Your curve just completed.")
                    pass
            do_step()

    @build_list
    @member_only
    def commandPyramid(self, parts, byuser, overriderank):
        "/pyramid blockname height [x y z] - Member\nSets all blocks in this area to be a pyramid."
        if len(parts) < 7 and len(parts) != 4:
            self.client.sendServerMessage("Please enter a block type height and fill?")
        else:
            # Try getting the fill
            fill = parts[3]
            if fill=='true' or fill=='false':
                pass
            else:
                self.client.sendServerMessage("fill must be true or false")
                return
            # Try getting the height
            try:
                height = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Height must be a Number.")
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
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[4])
                    y = int(parts[5])
                    z = int(parts[6])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
            pointlist = []
            for i in range(abs(height)):
                if height>0:
                    point1 = [x-i, y+height-i-1,z-i]
                    point2 = [x+i, y+height-i-1,z+i]
                else:
                    point1 = [x-i, y+height+i+1,z-i]
                    point2 = [x+i, y+height+i+1,z+i]
                pointlist = pointlist+[(point1,point2)]
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
            if (x) * (y) * (z)/2 > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to pyramid.")
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for pointtouple in pointlist:
                    x,y,z = pointtouple[0]
                    x2,y2,z2 = pointtouple[1]
                    for i in range(x, x2+1):
                        for j in range(y, y2+1):
                            for k in range(z, z2+1):
                                if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
                                    return
                                if fill == 'true' or (i==x and j==y) or (i==x2 and j==y2) or (j==y2 and k==z2) or (i==x2 and k==z2) or (j==y and k==z) or (i==x and k==z) or (i==x and k==z2) or (j==y and k==z2) or (i==x2 and k==z) or (j==y2 and k==z) or (i==x and j==y2) or (i==x2 and j==y):
                                    try:
                                       world[i, j, k] = block
                                    except AssertionError:
                                        self.client.sendServerMessage("Out of bounds pyramid error.")
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
                    self.client.sendServerMessage("Your pyramid just completed.")
                    pass
            do_step()

    @build_list
    @writer_only
    def commandLine(self, parts, byuser, overriderank):
        "/line blockname [x y z x2 y2 z2] - Builder\nSets all blocks between two points to be a line."
        if len(parts) < 8 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
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
            steps = int(((x2-x)**2+(y2-y)**2+(z2-z)**2)**0.5)
            mx = float(x2-x)/steps
            my = float(y2-y)/steps
            mz = float(z2-z)/steps
            coordinatelist1 = []
            for t in range(steps+1):
                coordinatelist1.append((int(round(mx*t+x)),int(round(my*t+y)),int(round(mz*t+z))))
            coordinatelist2 = []
            coordinatelist2 = [coordtuple for coordtuple in coordinatelist1 if coordtuple not in coordinatelist2]
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
            if len(coordinatelist2) > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to line.")
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for coordtuple in coordinatelist2:
                    i = coordtuple[0]
                    j = coordtuple[1]
                    k = coordtuple[2]
                    if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
                        return
                    try:
                        world[i, j, k] = block
                    except AssertionError:
                        self.client.sendServerMessage("Out of bounds line error.")
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
                    self.client.sendServerMessage("Your line just completed.")
                    pass
            do_step()

    @build_list
    @op_only
    def commandCsphere(self, parts, byuser, overriderank):
        "/csphere blocktype blocktype x y z radius - Op\nPlace/delete a block and /csphere block radius"
        if len(parts) < 7 and len(parts) != 4:
            self.client.sendServerMessage("Please enter two types a radius(and possibly a coord triple)")
        else:
            # Try getting the radius
            try:
                radius = int(parts[3])
            except ValueError:
                self.client.sendServerMessage("Radius must be a Number.")
                return
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
            # Check that block2 is valid
            if ord(block2) > 49:
                self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
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
            if (radius*2)**3>limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to csphere.")
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                ticker = 0
                for i in range(-radius-1, radius):
                    for j in range(-radius-1, radius):
                        for k in range(-radius-1, radius):
                            if (i**2 + j**2 + k**2)**0.5 + 0.691 < radius:
                                if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                    self.client.sendServerMessage("You do not have permision to build here.")
                                    return
                                try:
                                    if (i+j+k)%2 == 0:
                                        ticker = 1
                                    else:
                                        ticker = 0
                                    if ticker == 0:
                                        world[x+i, y+j, z+k] = block
                                    else:
                                        world[x+i, y+j, z+k] = block2
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds sphere error.")
                                    return
                                if ticker == 0:
                                    self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block2), world=world)
                                    self.client.sendBlock(x+i, y+j, z+k, block2)
                                else:
                                    self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                    self.client.sendBlock(x+i, y+j, z+k, block)
                                yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if byuser:
                        self.client.sendServerMessage("Your csphere just completed.")
                    pass
            do_step()
            
    @build_list
    @op_only
    def commandCircle(self, parts, byuser, overriderank):
        "/circle blocktype x y z radius axis - Op\nPlace/delete a block and /circle block radius axis"
        if len(parts) < 7 and len(parts) != 4: #bugfix 5/22/10
            self.client.sendServerMessage("Please enter a type, radius, axis(and possibly a coord triple)")
        else:
            # Try getting the normal axis
            normalAxis = parts[3]
            if normalAxis == 'x' or normalAxis == 'y' or normalAxis == 'z':
                pass
            else:
                self.client.sendServerMessage("Normal axis must be x,y, or z.")
                return
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be a Number.")
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
            # If they only provided the type argument, use the last two block places
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[4])
                    y = int(parts[5])
                    z = int(parts[6])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
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
            if 2*3.14*(radius)**2>limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to circle.")
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(-radius-1, radius):
                    for j in range(-radius-1, radius):
                        for k in range(-radius-1, radius):
                            if (i**2 + j**2 + k**2)**0.5 + 0.604 < radius:
                                #Test for axis
                                var_placeblock = 1
                                if i != 0 and normalAxis == 'x':
                                    var_placeblock = 0
                                if j != 0 and normalAxis == 'y':
                                    var_placeblock = 0
                                if k != 0 and normalAxis == 'z':
                                    var_placeblock = 0
                                if var_placeblock == 1:
                                    if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                        self.client.sendServerMessage("You do not have permission to build here.")
                                        return
                                    try:
                                        world[x+i, y+j, z+k] = block
                                    except AssertionError:
                                        self.client.sendServerMessage("Out of bounds circle error.")
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                    self.client.sendBlock(x+i, y+j, z+k, block)
                                    yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if byuser:
                        self.client.sendServerMessage("Your circle just completed.")
                    pass
            do_step()

    @build_list
    @op_only
    def commandDome(self, parts, byuser, overriderank):
        "/dome blocktype x y z radius - Op\nPlace/delete a block and /sphere block radius"
        if len(parts) < 7 and len(parts) != 4:
            self.client.sendServerMessage("Please enter a type radius fill?(and possibly a coord triple)")
        else:
            # Try getting the fill
            fill = parts[3]
            if fill=='true' or fill=='false':
                pass
            else:
                self.client.sendServerMessage("fill must be true or false")
                return
            # Try getting the radius
            try:
                radius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Radius must be a Number.")
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
            # If they only provided the type argument, use the last two block places
            if len(parts) == 4:
                try:
                    x, y, z = self.client.last_block_changes[0]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked for a center yet.")
                    return
            else:
                try:
                    x = int(parts[4])
                    y = int(parts[5])
                    z = int(parts[6])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
            absradius = abs(radius)
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
            if (radius*2)**3/2>limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to dome.")
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(-absradius-1, absradius):
                    for j in range(-absradius-1, absradius):
                        for k in range(-absradius-1, absradius):
                            if ((i**2 + j**2 + k**2)**0.5 + 0.691 < absradius and ((j >= 0 and radius > 0) or (j <= 0 and radius < 0)) and fill=='true') or (absradius-1 < (i**2 + j**2 + k**2)**0.5 + 0.691 < absradius and ((j >= 0 and radius > 0) or (j <= 0 and radius < 0)) and fill=='false'):
                                if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                    self.client.sendServerMessage("You do not have permision to build here.")
                                    return
                                try:
                                    world[x+i, y+j, z+k] = block
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds dome error.")
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
                                self.client.sendBlock(x+i, y+j, z+k, block)
                                yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if byuser:
                        self.client.sendServerMessage("Your dome just completed.")
                    pass
            do_step()

    @build_list
    @op_only
    def commandEllipsoid(self, parts, byuser, overriderank):
        "/ellipsoid blocktype x y z x2 y2 z2 endradius - Op\nAliases: ell\nPlace/delete two blocks and block endradius"
        if len(parts) < 9 and len(parts) != 3:
            self.client.sendServerMessage("Please enter a type endradius (and possibly two coord triples)")
        else:
            # Try getting the radius
            try:
                endradius = int(parts[2])
            except ValueError:
                self.client.sendServerMessage("Endradius must be a Number.")
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
            # If they only provided the type argument, use the last two block places
            if len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
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
                    self.client.sendServerMessage("All parameters must be integers")
                    return
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
            radius = int(round(endradius*2 + ((x2-x)**2+(y2-y)**2+(z2-z)**2)**0.5)/2 + 1)
            var_x = int(round(float(x+x2)/2))
            var_y = int(round(float(y+y2)/2))
            var_z = int(round(float(z+z2)/2))
            if int(4/3*3.14*radius**2*endradius)>limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to ellipsoid.")
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(-radius-2, radius+1):
                    for j in range(-radius-2, radius+1):
                        for k in range(-radius-2, radius+1):
                            if (((i+var_x-x)**2 + (j+var_y-y)**2 + (k+var_z-z)**2)**0.5 + ((i+var_x-x2)**2 + (j+var_y-y2)**2 + (k+var_z-z2)**2)**0.5)/2 + 0.691 < radius: #bugfix by Nick Tolrud: offset was omitted
                                if not self.client.AllowedToBuild(x+i, y+j, z+k) and not overriderank:
                                    self.client.sendServerMessage("You do not have permision to build here.")
                                    return
                                try:
                                    world[var_x+i, var_y+j, var_z+k] = block
                                except AssertionError:
                                    self.client.sendServerMessage("Out of bounds ellipsoid error.")
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (var_x+i, var_y+j, var_z+k, block), world=world)
                                self.client.sendBlock(var_x+i, var_y+j, var_z+k, block)
                                yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):
                        block_iter.next()
                    reactor.callLater(0.01, do_step)
                except StopIteration:
                    if byuser:
                        self.client.sendServerMessage("Your ellipsoid just completed.")
                    pass
            do_step()

    @build_list
    @op_only
    def commandPolytri(self, parts, byuser, overriderank):
        "/Polytri blockname [x y z x2 y2 z2 x3 y3 z3] - Op\nSets all blocks between three points to block."
        if len(parts) < 11 and len(parts) != 2:
            self.client.sendServerMessage("Please enter a type (and possibly three coord triples)")
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
                    x3, y3, z3 = self.client.thirdcoord
                except:
                    self.client.sendServerMessage("You have not recorded three corners yet (use /recthird).")
                    return
            else:
                try:
                    x = int(parts[2])
                    y = int(parts[3])
                    z = int(parts[4])
                    x2 = int(parts[5])
                    y2 = int(parts[6])
                    z2 = int(parts[7])
                    x3 = int(parts[8])
                    y3 = int(parts[9])
                    z3 = int(parts[10])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
            if (x==x2 and y==y2 and z==z2) or (x==x3 and y==y3 and z==z3) or (x3==x2 and y3==y2 and z3==z2):
                self.client.sendServerMessage("Repeated corners error.")
                return
            #line 1 list
            steps = int(((x2-x)**2+(y2-y)**2+(z2-z)**2)**0.5/0.75)
            mx = float(x2-x)/steps
            my = float(y2-y)/steps
            mz = float(z2-z)/steps
            coordinatelist2 = []
            for t in range(steps+1):
                coordinatelist2.append((mx*t+x,my*t+y,mz*t+z))
            #line 2 list
            steps = int(((x3-x)**2+(y3-y)**2+(z3-z)**2)**0.5/0.75)
            mx = float(x3-x)/steps
            my = float(y3-y)/steps
            mz = float(z3-z)/steps
            coordinatelist3 = []
            for t in range(steps+1):
                coordinatelist3.append((mx*t+x,my*t+y,mz*t+z))
            #final coordinate list
            if len(coordinatelist2) > len(coordinatelist3):
                coordinatelistA = coordinatelist2
                coordinatelistB = coordinatelist3
            else:
                coordinatelistA = coordinatelist3
                coordinatelistB = coordinatelist2
            lenofA = len(coordinatelistA)
            listlenRatio = float(len(coordinatelistB))/lenofA
            finalcoordinatelist = []
            for i in range(lenofA):
                point1 = coordinatelistA[i]
                point2 = coordinatelistB[int(i*listlenRatio)]
                var_x = point1[0]
                var_y = point1[1]
                var_z = point1[2]
                var_x2 = point2[0]
                var_y2 = point2[1]
                var_z2 = point2[2]
                steps = int(((var_x2-var_x)**2+(var_y2-var_y)**2+(var_z2-var_z)**2)**0.5/0.75)
                if steps != 0:
                    mx = float(var_x2-var_x)/steps
                    my = float(var_y2-var_y)/steps
                    mz = float(var_z2-var_z)/steps
                    coordinatelist = []
                    for t in range(steps+1):
                        coordinatelist.append((int(round(mx*t+var_x)),int(round(my*t+var_y)),int(round(mz*t+var_z))))
                    for coordtuple in coordinatelist:
                        if coordtuple not in finalcoordinatelist:
                            finalcoordinatelist.append(coordtuple)
                elif point1 not in finalcoordinatelist:
                    finalcoordinatelist.append(point1)
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
            if ((x-x2)**2+(y-y2)**2+(z-z2)**2)**0.5*((x-x3)**2+(y-y3)**2+(z-z3)**2)**0.5 > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to polytri.")
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for coordtuple in finalcoordinatelist:
                    i = int(coordtuple[0])
                    j = int(coordtuple[1])
                    k = int(coordtuple[2])
                    if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                        self.client.sendServerMessage("You do not have permision to build here.")
                        return
                    try:
                        world[i, j, k] = block
                    except AssertionError:
                        self.client.sendServerMessage("Out of bounds polytri error.")
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
                        self.client.sendServerMessage("Your polytri just completed.")
                    pass
            do_step()
