# blockBox is Copyright 2009-2010 of the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import cmath, random

from lib.twisted.internet import reactor

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class BuildLibPlugin(ProtocolPlugin):
	"Collections of things that users can build."
	commands = {
		"dune": "commandDune",
		"hill": "commandHill",
		"hole": "commandHole",
		"lake": "commandLake",
		"mountain": "commandMountain",
		"pit": "commandPit",
		"tree": "commandTree",		"sphere": "commandSphere",
		"hsphere": "commandHSphere",
		"curve": "commandCurve",
		"line": "commandLine",
		"pyramid": "commandPyramid",
		"csphere": "commandCsphere",
		"circle": "commandCircle",
		"dome": "commandDome",
		"ellipsoid": "commandEllipsoid",
		"ell": "commandEllipsoid",
		"polytri": "commandPolytri",		"stairs": "commandStairs",
	}

	hooks = {
		"blockchange": "blockChanged",
		"newworld": "newWorld",
	}

	def gotClient(self):
		self.build_trees = False
		self.trunk_height = 5, 9
		self.fanout = 2, 4

	def newWorld(self, world):
		"Hook to reset dynamiting abilities in new worlds if not op."
		if not self.client.isWriter():
			self.build_trees = False

	def blockChanged(self, x, y, z, block, selected_block, fromloc):
		"Hook trigger for block changes."
		tobuild = []
		# Randomise the variables
		trunk_height = random.randint(*self.trunk_height)
		fanout = random.randint(*self.fanout)
		if self.build_trees and block == BLOCK_PLANT:
			# Build the main tree bit
			for i in range(-fanout-1, fanout):
				for j in range(-fanout-1, fanout):
					for k in range(-fanout-1, fanout):
						if not self.client.AllowedToBuild(x+i, y+j, z+k):
							return
						if (i**2 + j**2 + k**2)**0.5 < fanout:
							tobuild.append((i, j+trunk_height, k, BLOCK_LEAVES))
			# Build the trunk
			for i in range(trunk_height):
				tobuild.append((0, i, 0, BLOCK_LOG))
			# OK, send the build changes
			for dx, dy, dz, block in tobuild:
				try:
					self.client.world[x+dx, y+dy, z+dz] = chr(block)
					self.client.sendBlock(x+dx, y+dy, z+dz, block)
					self.client.factory.queue.put((self.client, TASK_BLOCKSET, (x+dx, y+dy, z+dz, block)))
				except AssertionError:
					pass
			return True

	@build_list
	@op_only
	@on_off_command
	def commandTree(self, onoff, fromloc, overriderank):
		"/tree on|off - Builder\nBuilds trees, save the earth!"
		if onoff == "on":
			self.build_trees = True
			self.client.sendServerMessage("You are now building trees; place a plant!")
		else:
			self.build_trees = False
			self.client.sendServerMessage("You are no longer building trees.")

	@build_list
	@advbuilder_only
	def commandDune(self, parts, fromloc, overriderank):
		"/dune - Member\nCreates a sand dune between the two blocks you touched last."
		# Use the last two block places
		try:
			x, y, z = self.client.last_block_changes[0]
			x2, y2, z2 = self.client.last_block_changes[1]
		except IndexError:
			self.client.sendServerMessage("You have not clicked two corners yet.")
			return
		if x > x2:
			x, x2 = x2, x
		if y > y2:
			y, y2 = y2, y
		if z > z2:
			z, z2 = z2, z
		x_range = x2 - x
		z_range = z2 - z
		# Draw all the blocks on, I guess
		# We use a generator so we can slowly release the blocks
		# We also keep world as a local so they can't change worlds and affect the new one
		world = self.client.world
		def generate_changes():
			for i in range(x, x2+1):
				for k in range(z, z2+1):
					# Work out the height at this place
					dx = (x_range / 2.0) - abs((x_range / 2.0) - (i - x))
					dz = (z_range / 2.0) - abs((z_range / 2.0) - (k - z))
					dy = int((dx**2 * dz**2) ** 0.2)
					for j in range(y, y+dy+1):
						if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
							return
						block = BLOCK_SAND if j == y+dy else BLOCK_SAND
						try:
							world[i, j, k] = chr(block)
						except AssertionError:
							pass
						self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
						self.client.sendBlock(i, j, k, block)
						self.client.total += 1 # This is how you increase a number in python.... - Stacy
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
				if fromloc == 'user':
					self.client.finalizeMassCMD('dune', self.client.total)
					#Flush after use
					self.client.total = 0
				pass
		do_step()

	@build_list
	@advbuilder_only
	def commandHill(self, parts, fromloc, overriderank):
		"/hill - Member\nCreates a hill between the two blocks you touched last."
		# Use the last two block places
		try:
			x, y, z = self.client.last_block_changes[0]
			x2, y2, z2 = self.client.last_block_changes[1]
		except IndexError:
			self.client.sendServerMessage("You have not clicked two corners yet.")
			return
		if x > x2:
			x, x2 = x2, x
		if y > y2:
			y, y2 = y2, y
		if z > z2:
			z, z2 = z2, z
		x_range = x2 - x
		z_range = z2 - z
		# Draw all the blocks on, I guess
		# We use a generator so we can slowly release the blocks
		# We also keep world as a local so they can't change worlds and affect the new one
		world = self.client.world
		def generate_changes():
			for i in range(x, x2+1):
				for k in range(z, z2+1):
					# Work out the height at this place
					dx = (x_range / 2.0) - abs((x_range / 2.0) - (i - x))
					dz = (z_range / 2.0) - abs((z_range / 2.0) - (k - z))
					dy = int((dx**2 * dz**2) ** 0.2)
					for j in range(y, y+dy+1):
						if not self.client.AllowedToBuild(x, y, z) and overriderank==False:
							return
						block = BLOCK_GRASS if j == y+dy else BLOCK_DIRT
						try:
							world[i, j, k] = chr(block)
						except AssertionError:
							pass
						self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
						self.client.sendBlock(i, j, k, block)
						self.client.total += 1 # This is how you increase a number in python.... - Stacy
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
				if fromloc == 'user':
					self.client.finalizeMassCMD('hill', self.client.total)
					#Flush after use
					self.client.total = 0
				pass
		do_step()

	@build_list
	@advbuilder_only
	def commandHole(self, parts, fromloc, overriderank):
		"/hole - Member\ncreates a hole between two blocks"
		#Use the last two block places
		try:
			x1, y1, z1 = self.client.last_block_changes[0]
			x2, y2, z2 = self.client.last_block_changes[1]
		except IndexError:
				self.client.sendServerMessage("You have not clicked two corners yet")
				return
		if x1 > x2:
			x1, x2 = x2, x1
		if y1 > y2:
			y1, y2 = y2, y1
		if z1 > z2:
			z1, z2 = z2, z1
		x_range = x2 - x1
		z_range = z2 - z1
		block = BLOCK_AIR
		world = self.client.world
		def generate_changes():
			for x in range(x1, x2+1):
				for z in range(z1, z2+1):
					# Work out the height at this place
					dx = (x_range / 2.0) - abs((x_range / 2.0) - (x - x1))
					dz = (z_range / 2.0) - abs((z_range / 2.0) - (z - z1))
					dy = int((dx**2 * dz**2) ** 0.3)
					for y in range(y1-dy-1, y1+1):
						if not self.client.AllowedToBuild(x, y, z) and overriderank==False:
							return
						if y < 0:
							continue
						try:
							world[x, y, z] = chr(block)
						except AssertionError:
							pass
						self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world = world)
						self.client.sendBlock(x, y, z, block)
						self.client.total += 1 # This is how you increase a number in python.... - Stacy
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
				if fromloc == 'user':
					self.client.finalizeMassCMD('hole', self.client.total)
					self.client.total = 0
				pass
		do_step()

	@build_list
	@advbuilder_only
	def commandLake(self, parts, fromloc, overriderank):
		"/lake - Member\ncreates a lake between two blocks"
		#Use the last two block places
		try:
			x1, y1, z1 = self.client.last_block_changes[0]
			x2, y2, z2 = self.client.last_block_changes[1]
		except IndexError:
				self.client.sendServerMessage("You have not clicked two corners yet")
				return
		if x1 > x2:
			x1, x2 = x2, x1
		if y1 > y2:
			y1, y2 = y2, y1
		if z1 > z2:
			z1, z2 = z2, z1
		x_range = x2 - x1
		z_range = z2 - z1
		block = BLOCK_WATER
		world = self.client.world
		def generate_changes():
			for x in range(x1, x2+1):
				for z in range(z1, z2+1):
					# Work out the height at this place
					dx = (x_range / 2.0) - abs((x_range / 2.0) - (x - x1))
					dz = (z_range / 2.0) - abs((z_range / 2.0) - (z - z1))
					dy = int((dx**2 * dz**2) ** 0.3)
					for y in range(y1-dy-1, y1):
						if not self.client.AllowedToBuild(x, y, z) and overriderank==False:
							return
						try:
							world[x, y, z] = chr(block)
						except AssertionError:
							pass
						self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world = world)
						self.client.sendBlock(x, y, z, block)
						self.client.total += 1 # This is how you increase a number in python.... - Stacy
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
				if fromloc == 'user':
					self.client.finalizeMassCMD('lake', self.client.total)
					#Flush after use
					self.client.total = 0
				pass
		do_step()

	@build_list
	@advbuilder_only
	def commandMountain(self, parts, fromloc, overriderank):
		"/mountain blockname - Member\nCreates a mountain between the two blocks you touched last."
		if len(parts) < 8 and len(parts) != 2:
			self.client.sendServerMessage("Please enter a type.")
			return
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
		x_range = x2 - x
		z_range = z2 - z
		# Draw all the blocks on, I guess
		# We use a generator so we can slowly release the blocks
		# We also keep world as a local so they can't change worlds and affect the new one
		world = self.client.world
		def generate_changes():
			for i in range(x, x2+1):
				for k in range(z, z2+1):
					# Work out the height at this place
					dx = (x_range / 2.0) - abs((x_range / 2.0) - (i - x))
					dz = (z_range / 2.0) - abs((z_range / 2.0) - (k - z))
					dy = int((dx**2 * dz**2) ** 0.3)
					for j in range(y, y+dy+1):
						if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
							return
						try:
							world[i, j, k] = block
						except AssertionError:
							pass
						self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
						self.client.sendBlock(i, j, k, block)
						self.client.total += 1 # This is how you increase a number in python.... - Stacy
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
				if fromloc == 'user':
					self.client.finalizeMassCMD('mountain', self.client.total)
					self.client.total = 0
				pass
		do_step()

	@build_list
	@advbuilder_only
	def commandPit(self, parts, fromloc, overriderank):
		"/pit - Member\ncreates a lava pit between two blocks"
		#Use the last two block places
		try:
			x1, y1, z1 = self.client.last_block_changes[0]
			x2, y2, z2 = self.client.last_block_changes[1]
		except IndexError:
				self.client.sendServerMessage("You have not clicked two corners yet")
				return
		if x1 > x2:
			x1, x2 = x2, x1
		if y1 > y2:
			y1, y2 = y2, y1
		if z1 > z2:
			z1, z2 = z2, z1
		x_range = x2 - x1
		z_range = z2 - z1
		block = BLOCK_LAVA
		world = self.client.world
		def generate_changes():
			for x in range(x1, x2+1):
				for z in range(z1, z2+1):
					# Work out the height at this place
					dx = (x_range / 2.0) - abs((x_range / 2.0) - (x - x1))
					dz = (z_range / 2.0) - abs((z_range / 2.0) - (z - z1))
					dy = int((dx**2 * dz**2) ** 0.3)
					for y in range(y1-dy-1, y1):
						if not self.client.AllowedToBuild(x, y, z) and overriderank==False:
							return
						try:
							world[x, y, z] = chr(block)
						except AssertionError:
							pass
						self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world = world)
						self.client.sendBlock(x, y, z, block)
						self.client.total += 1
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
				if fromloc == 'user':
					self.client.finalizeMassCMD('pit', self.client.total)
					self.client.total = 0
				pass
		do_step()
	@build_list
	@writer_only
	def commandSphere(self, parts, fromloc, overriderank):
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
			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((radius*2)**3 > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to sphere (Limit is %s)" % limit)
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
								self.client.total += 1
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
					if fromloc == 'user':
						self.client.finalizeMassCMD('sphere', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@writer_only
	def commandHSphere(self, parts, fromloc, overriderank):
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
			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((radius*2)**3 > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to hsphere (Limit is %s)" % limit)
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
									self.client.sendServerMessage("You are not allowed to build here.")
									return
								try:
									world[x+i, y+j, z+k] = block
								except AssertionError:
									self.client.sendServerMessage("Out of bounds hsphere error.")
									return
								self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
								self.client.sendBlock(x+i, y+j, z+k, block)
								self.client.total += 1
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
					if fromloc == 'user':
						self.client.finalizeMassCMD('hsphere', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@advbuilder_only
	def commandCurve(self, parts, fromloc, overriderank):
		"/curve blockname [x y z x2 y2 z2 x3 y3 z3] - Advaced Builder\nSets a line of blocks along three points to block."
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
					x3, y3, z3 = self.client.last_block_changes[2]
				except:
					self.client.sendServerMessage("You have not clicked 3 points yet.")
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
			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((2*((x-x2)**2+(y-y2)**2+(z-z2)**2)**0.5+2*((x2-x3)**2+(y2-y3)**2+(z2-z3)**2)**0.5) > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to curve (Limit is %s)" % limit)
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
					self.client.total += 1
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
					if fromloc == 'user':
						self.client.finalizeMassCMD('curve', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@advbuilder_only
	def commandPyramid(self, parts, fromloc, overriderank):
		"/pyramid blockname height fill(true|false) [x y z] - Advanced Builder\nSets all blocks in this area to be a pyramid."
		if len(parts) < 7 and len(parts) != 4:
			self.client.sendServerMessage("Please enter a block type, height and fill (hollow)")
		else:
			# Try getting the fill
			fill = parts[3]
			if fill=='true' or fill=='false':
				pass
			else:
				self.client.sendServerMessage("Fill must be true or false.")
				return
			# Try getting the height
			try:
				height = int(parts[2])
			except ValueError:
				self.client.sendServerMessage("Height must be a number.")
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
			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((x) * (y) * (z)/2 > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to pyramid (Limit is %s)" % limit)
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
									self.client.total += 1 # This is how you increase a number in python.... - Stacy
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
					if fromloc == 'user':
						self.client.finalizeMassCMD('pyramid', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@writer_only
	def commandLine(self, parts, fromloc, overriderank):
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
			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if (len(coordinatelist2) > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to line (Limit is %s)" % limit)
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
					self.client.total += 1
					yield
			# Now, set up a loop delayed by the reactor
			block_iter = iter(generate_changes())
			def do_step():
				# Do 10 blocks
				try:
					for x in range(10): #10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
						block_iter.next()
					reactor.callLater(0.01, do_step) #This is how long(in seconds) it waits to run another 10 blocks
				except StopIteration:
					if fromloc == 'user':
						self.client.finalizeMassCMD('line', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@op_only
	def commandCsphere(self, parts, fromloc, overriderank):
		"/csphere blocktype blocktype x y z radius - Op\nPlace/delete a block and /csphere block radius"
		self.total_a = 0
		self.total_b = 0
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
			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((radius*2)**3 > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to csphere (Limit is %s)" % limit)
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
									self.client.sendServerMessage("Out of bounds csphere error.")
									return
								if ticker == 0:
									self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block2), world=world)
									self.client.sendBlock(x+i, y+j, z+k, block2)
								else:
									self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
									self.client.sendBlock(x+i, y+j, z+k, block)
								self.client.total += 1
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
					if fromloc == 'user':
						self.client.finalizeMassCMD('csphere', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@op_only
	def commandCircle(self, parts, fromloc, overriderank):
		"/circle blocktype x y z radius axis - Op\nPlace/delete a block and /circle block radius axis"
		if len(parts) < 7 and len(parts) != 4:
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
			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if (int(2*cmath.pi*(radius)**2) > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to circle (Limit is %s)" % limit)
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
									self.client.total += 1
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
					if fromloc == 'user':
						self.client.finalizeMassCMD('circle', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@op_only
	def commandDome(self, parts, fromloc, overriderank):
		"/dome blocktype x y z radius - Op\nPlace/delete a block and /sphere block radius"
		if len(parts) < 7 and len(parts) != 4:
			self.client.sendServerMessage("Please enter a type, the radius and whether to fill (and possibly a coord triple)")
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
				self.client.sendServerMessage("Radius must be a integer.")
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
			# If they only provided the type argument, use the last block place
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
			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((radius*2)**3/2 > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to dome (Limit is %s)" % limit)
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
								self.client.total += 1
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
					if fromloc == 'user':
						self.client.finalizeMassCMD('dome', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@op_only
	def commandEllipsoid(self, parts, fromloc, overriderank):
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
			radius = int(round(endradius*2 + ((x2-x)**2+(y2-y)**2+(z2-z)**2)**0.5)/2 + 1)
			var_x = int(round(float(x+x2)/2))
			var_y = int(round(float(y+y2)/2))
			var_z = int(round(float(z+z2)/2))
			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if (int(4/3*cmath.pi*radius**2*endradius) > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to ellipsoid (Limit is %s)" % limit)
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
								self.client.total += 1
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
					if fromloc == 'user':
						self.client.finalizeMassCMD('ellpsoid', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@op_only
	def commandPolytri(self, parts, fromloc, overriderank):
		"/polytri blockname [x y z x2 y2 z2 x3 y3 z3] - Op\nSets all blocks between three points to block."
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
					x3, y3, z3 = self.client.last_block_changes[2]
				except:
					self.client.sendServerMessage("You have not clicked 3 points yet.")
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
			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((((x-x2)**2+(y-y2)**2+(z-z2)**2)**0.5*((x-x3)**2+(y-y3)**2+(z-z3)**2)**0.5) > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to polytri (Limit is %s)" % limit)
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
					self.client.total += 1
					yield
			# Now, set up a loop delayed by the reactor
			block_iter = iter(generate_changes())
			def do_step():
				# Do 10 blocks
				try:
					for x in range(10): #10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
						block_iter.next()
					reactor.callLater(0.01, do_step) #This is how long(in seconds) it waits to run another 10 blocks
				except StopIteration:
					if fromloc == 'user':
						self.client.finalizeMassCMD('polytri', self.client.total)
						self.client.total = 0
					pass
			do_step()
	@build_list
	@writer_only
	def commandStairs(self, parts, fromloc, overriderank):
		"/stairs blockname height (c) [x y z x2 y2 z2] - Builder\nBuilds a spiral staircase."
		if len(parts) < 9 and len(parts) != 3 and len(parts) != 4:
			self.client.sendServerMessage("Please enter a blocktype height (c (for counter-clockwise)")
			self.client.sendServerMessage("(and possibly two coord triples)")
			self.client.sendServerMessage("If the two points are on the 'ground' adjacent to each other, then")
			self.client.sendServerMessage("the second point will spawn the staircase and the first will")
			self.client.sendServerMessage("be used for the initial orientation")
		else:
			# Try getting the counter-clockwise flag
			if len(parts) == 4:
				if parts[3] == 'c':
					counterflag = 1
				else:
					self.client.sendServerMessage("The third entry must be 'c' for counter-clockwise")
					return
			else:
				counterflag = -1
			# Try getting the height as a direct integer type.
			try:
				height = int(parts[2])
			except ValueError:
				self.client.sendServerMessage("The height must be an integer")
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
			if len(parts) == 3 or len(parts) == 4:
				try:
					x, y, z = self.client.last_block_changes[0]
					x2, y2, z2 = self.client.last_block_changes[1]
				except IndexError:
					self.client.sendServerMessage("You have not clicked two corners yet.")
					return
			else:
				if len(parts) == 9:
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

			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if (height * 4 > limit) or limit == 0:
					self.client.sendSplitServerMessage("Sorry, that area is too big for you to make stairs(Limit is %s)" % limit)
					return
			# Draw all the blocks on, I guess
			# We use a generator so we can slowly release the blocks
			# We also keep world as a local so they can't change worlds and affect the new one
			world = self.client.world
			def generate_changes():
				if abs(x-x2)+abs(z-z2) == 1:
					if x - x2 == -1:
						orientation = 1
					elif z - z2 == -1:
						orientation = 2
					elif x - x2 == 1:
						orientation = 3
					else:
						orientation = 4
				else:
					orientation = 1
				if height >= 0:
					heightsign = 1
				else:
					heightsign = -1
				stepblock = chr(BLOCK_STEP)
				for h in range(abs(height)):
					locy = y+h*heightsign
					if counterflag == -1:
						if orientation == 1:
							blocklist = [(x,locy,z),(x+1,locy,z+1),(x+1,locy,z),(x+1,locy,z-1)]
						elif orientation == 2:
							blocklist = [(x,locy,z),(x-1,locy,z+1),(x,locy,z+1),(x+1,locy,z+1)]
						elif orientation == 3:
							blocklist = [(x,locy,z),(x-1,locy,z-1),(x-1,locy,z),(x-1,locy,z+1)]
						else:
							blocklist = [(x,locy,z),(x+1,locy,z-1),(x,locy,z-1),(x-1,locy,z-1)]
					else:
						if orientation == 1:
							blocklist = [(x,locy,z),(x+1,locy,z-1),(x+1,locy,z),(x+1,locy,z+1)]
						elif orientation == 2:
							blocklist = [(x,locy,z),(x+1,locy,z+1),(x,locy,z+1),(x-1,locy,z+1)]
						elif orientation == 3:
							blocklist = [(x,locy,z),(x-1,locy,z+1),(x-1,locy,z),(x-1,locy,z-1)]
						else:
							blocklist = [(x,locy,z),(x-1,locy,z-1),(x,locy,z-1),(x+1,locy,z-1)]
					orientation = orientation - heightsign*counterflag
					if orientation > 4:
						orientation = 1
					if orientation < 1:
						orientation = 4
					for entry in blocklist:
						i,j,k = entry
						if not self.client.AllowedToBuild(i, j, k):
							return
					for entry in blocklist[:3]:
						i,j,k = entry
						try:
							world[i, j, k] = block
						except AssertionError:
							self.client.sendServerMessage("Out of bounds stairs error.")
							return
						self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
						self.client.sendBlock(i, j, k, block)
						yield
						i,j,k = blocklist[3]
						try:
							world[i, j, k] = stepblock
						except AssertionError:
							self.client.sendServerMessage("Out of bounds stairs error.")
							return
						self.client.queueTask(TASK_BLOCKSET, (i, j, k, stepblock), world=world)
						self.client.sendBlock(i, j, k, stepblock)
						self.client.total += 1 # This is how you increase a number in python.... - Stacy
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
					if fromloc == 'user':
						self.client.finalizeMassCMD('stairs', self.total)
						self.client.total = 0
					pass
			do_step()