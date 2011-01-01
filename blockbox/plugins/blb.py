# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class BlbPlugin(ProtocolPlugin):
	"Commands for Massive block buildings."

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
		#"useblblimit": "commandToggleUseBlb",
	}

	def canBreakAdminBlocks(self):
		"Shortcut for checking permissions."
		if hasattr(self.client, "world"):
			return (not self.client.world.admin_blocks) or self.client.isOp()
		else:
			return False

	@build_list
	def commandBlb(self, parts, fromloc, overriderank):
		"/blb blockname [x y z x2 y2 z2] - Guest\nAliases: box, cub, cuboid, draw\nSets all blocks in this area to block."
		if len(parts) < 8 and len(parts) != 2:
			self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
		else:
			block = self.client.GetBlockValue(parts[1])
			if block == None:
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

			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to blb (Limit is %s)" % limit)
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
								if not self.client.AllowedToBuild(i, j, k) and overriderank == False:
									return
								world[i, j, k] = block
								self.client.runHook("blockchange", x, y, z, ord(block), ord(block), fromloc)
								self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
								self.client.sendBlock(i, j, k, block)
								self.client.total += 1
								yield
				except AssertionError:
					self.client.sendServerMessage("Out of bounds blb error.")
					return
				# Now, set up a loop delayed by the reactor
			block_iter = iter(generate_changes())
			def do_step():
				# Do 10 blocks
				try:
					for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
						block_iter.next()
					reactor.callLater(0.01, do_step) #This is how long(in seconds) it waits to run another 10 blocks
				except StopIteration:
					if fromloc == 'user':
						self.client.finalizeMassCMD('blb', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	def commandHBlb(self, parts, fromloc, overriderank):
		"/bhb blockname [x y z x2 y2 z2] - Guest\nAliases: hbox\nSets all blocks in this area to block, hollow."
		if len(parts) < 8 and len(parts) != 2:
			self.client.sendServerMessage("Please enter a block type")
		else:
			block = self.client.GetBlockValue(parts[1])
			if block == None:
				return
			if ord(block) == 7:
				if not self.canBreakAdminBlocks():
					self.client.sendServerMessage("Solid is op-only.")
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

			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if (x2 - x) * (y2 - y) * (z2 - z) > limit or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to bhb (Limit is %s)" % limit)
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
								if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
									return
								if i==x or i==x2 or j==y or j==y2 or k==z or k==z2:
									world[i, j, k] = block
									self.client.runHook("blockchange", x, y, z, ord(block), ord(block), fromloc)
								   	self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
									self.client.sendBlock(i, j, k, block)
									self.client.total += 1
									yield
				except AssertionError:
					self.client.sendServerMessage("Out of bounds bhb error.")
					return

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
						self.client.finalizeMassCMD('bhb', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	def commandWBlb(self, parts, fromloc, overriderank):
		"/bwb blockname [x y z x2 y2 z2] - Guest\nBuilds four walls between the two areas.\nHollow, with no roof or floor."
		if len(parts) < 8 and len(parts) != 2:
			self.client.sendServerMessage("Please enter a block type.")
		else:
			block = self.client.GetBlockValue(parts[1])
			if block == None:
				return
			if ord(block) == 7:
				if not self.canBreakAdminBlocks():
					self.client.sendServerMessage("Solid is op-only.")
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

			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to bwb (Limit is %s)" % limit)
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
									self.client.runHook("blockchange", x, y, z, ord(block), ord(block), fromloc)
								except AssertionError:
									self.client.sendServerMessage("Out of bounds bwb error.")
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
					for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
						block_iter.next()
					reactor.callLater(0.01, do_step)  # This is how long (in seconds) it waits to run another 10 blocks
				except StopIteration:
					if fromloc == 'user':
						self.client.finalizeMassCMD('bwb', self.client.count)
					pass
			do_step()

	@build_list
	def commandBcb(self, parts, fromloc, overriderank):
		"/bcb blockname blockname2 [x y z x2 y2 z2] - Guest\nSets all blocks in this area to block, checkered."
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
			if ord(block2) in op_blocks and not self.client.isOp():
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

			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to bcb (Limit is %s)" % limit)
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
							self.client.total += 1 # This is how you increase a number in python.... - Stacy
							yield

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
						self.client.finalizeMassCMD('bcb', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	def commandBhcb(self, parts, fromloc, overriderank):
		"/bhcb blockname blockname2 [x y z x2 y2 z2] - Guest\nSets all blocks in this area to blocks, checkered hollow."
		self.total_a = 0
		self.total_b = 0
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
			# Check that block2 is valid
			if ord(block2) > 49:
				self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
				return
			if ord(block2) in op_blocks and not self.client.isOp():
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

			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to bhcb (Limit is %s)" % limit)
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
										self.total_a = self.total_a+1
									else:
										world[i, j, k] = block2
										self.total_b = self.total_b+1
								except AssertionError:
									self.client.sendServerMessage("Out of bounds bhcb error.")
									return
								if ticker == 0:
									self.client.queueTask(TASK_BLOCKSET, (i, j, k, block2), world=world)
									self.client.sendBlock(i, j, k, block2)
								else:
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
						self.client.finalizeMassCMD('bhcb', self.client.total)
						self.client.sendServerMessage("%i %s, %i %s" % (self.total_a, block, self.total_b, block2))
						self.total_a = 0
						self.total_b = 0
					pass
			do_step()

	@build_list
	def commandFBlb(self, parts, fromloc, overriderank):
		"/bfb blockname [x y z x2 y2 z2] - Guest\nSets all blocks in this area to block, wireframe."
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

			limit = self.client.getBlbLimit(self.client.username)
			if limit != -1:
				# Stop them doing silly things
				if ((x2 - x) * (y2 - y) * (z2 - z) > limit) or limit == 0:
					self.client.sendServerMessage("Sorry, that area is too big for you to bfb (Limit is %s)" % limit)
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
						self.client.finalizeMassCMD('bfb', count)
					pass
			do_step()

#	@owner_only
#	@on_off_command
#	def commandToggleUseBlb(self, onoff, fromloc, overriderank):
#		"/useblblimit on|off - Owner\nSet if the server will use custom BLB limit or the default limit."
#		if onoff == "on":
#			self.client.factory.useblblimit = True
#			self.client.sendServerMessage("Custom BLB Limit is now on.")
#		else:
#			self.client.factory.useblblimit = False
#			self.client.sendServerMessage("Custom BLB Limit is now off.")