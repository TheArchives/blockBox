# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class BlbPlugin(ProtocolPlugin):
	"Commands for massive block buildings."

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

	@config("category", "build")
	def commandBlb(self, parts, fromloc, overriderank):
		"/blb blockname [x y z x2 y2 z2] - Guest\nAliases: box, cub, cuboid, draw\nSets all blocks in this area to block."
		if len(parts) < 8 and len(parts) != 2:
			self.client.sendServerMessage("Please enter a type (and possibly two coord triples)")
		else:
			block = self.client.GetBlockValue(parts[1])
			if block == None:
				return
			if not self.client.canUseRestrictedBlocks(block):
				self.client.sendServerMessage("Sorry, but you are not allowed to use that block.")
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
					self.client.sendServerMessage("All coordinate parameters must be integers.")
					return
			# Reverse the coordinate, if necessary.
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
					reactor.callLater(0.01, do_step) # This is how long(in seconds) it waits to run another 10 blocks
				except StopIteration:
					if fromloc == 'user':
						self.client.finalizeMassCMD('blb', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@config("category", "build")
	def commandHBlb(self, parts, fromloc, overriderank):
		"/bhb blockname [x y z x2 y2 z2] - Guest\nAliases: hbox\nSets all blocks in this area to block, hollow."
		if len(parts) < 8 and len(parts) != 2:
			self.client.sendServerMessage("Please enter a block type.")
		else:
			block = self.client.GetBlockValue(parts[1])
			if block == None:
				return
			if not self.client.canUseRestrictedBlocks(block):
				self.client.sendServerMessage("Sorry, but you are not allowed to use that block.")
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
					self.client.sendServerMessage("All coordinate parameters must be integers.")
					return
			# Reverse the coordinates, if necessary.
			if x > x2:
				x, x2 = x2, x
			if y > y2:
				y, y2 = y2, y
			if z > z2:
				z, z2 = z2, z

			limit = self.client.getBlbLimit()
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
								if not self.client.AllowedToBuild(i, j, k) and not overriderank:
									return
								if i == x or i == x2 or j == y or j == y2 or k == z or k == z2:
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
					for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
						block_iter.next()
					reactor.callLater(0.01, do_step) # This is how long(in seconds) it waits to run another 10 blocks
				except StopIteration:
					if fromloc == 'user':
						self.client.finalizeMassCMD('bhb', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@config("category", "build")
	def commandWBlb(self, parts, fromloc, overriderank):
		"/bwb blockname [x y z x2 y2 z2] - Guest\nBuilds four walls between the two areas.\nHollow, with no roof or floor."
		if len(parts) < 8 and len(parts) != 2:
			self.client.sendServerMessage("Please enter a block type.")
		else:
			block = self.client.GetBlockValue(parts[1])
			if block == None:
				return
			if not self.client.canUseRestrictedBlocks(block):
				self.client.sendServerMessage("Sorry, but you are not allowed to use that block.")
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
					self.client.sendServerMessage("All coordinate parameters must be integers.")
					return
			# Reverse the coordinates, if necessary.
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
					self.client.sendServerMessage("Sorry, that area is too big for you to bwb (Limit is %s)" % limit)
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
								if not self.client.AllowedToBuild(i, j, k) and not overriderank:
									return
								if i == x or i == x2 or k == z or k == z2:
									world[i, j, k] = block
									self.client.runHook("blockchange", x, y, z, ord(block), ord(block), fromloc)
									self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
									self.client.sendBlock(i, j, k, block)
									self.client.total += 1
									yield
				except AssertionError:
					self.client.sendServerMessage("Out of bounds bwb error.")
					return

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
						self.client.finalizeMassCMD('bwb', self.client.total)
					pass
			do_step()

	@config("category", "build")
	def commandBcb(self, parts, fromloc, overriderank):
		"/bcb blockname blockname2 [x y z x2 y2 z2] - Guest\nSets all blocks in this area to block, checkered."
		if len(parts) < 9 and len(parts) != 3:
			self.client.sendServerMessage("Please enter two types (and possibly two coord triples)")
		else:
			block = self.client.GetBlockValue(parts[1])
			block2 = self.client.GetBlockValue(parts[2])
			if block == None or block2 == None:
				return
			if not self.client.canUseRestrictedBlocks(block) or not self.client.canUseRestrictedBlocks(block2):
				self.client.sendServerMessage("Sorry, but you are not allowed to use that block.")
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
			# Reverse the coordinates, if necessary.
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
					self.client.sendServerMessage("Sorry, that area is too big for you to bcb (Limit is %s)" % limit)
					return

			# Draw all the blocks on, I guess
			# We use a generator so we can slowly release the blocks
			# We also keep world as a local so they can't change worlds and affect the new one
			world = self.client.world
			def generate_changes():
				ticker = 0
				try:
					for i in range(x, x2+1):
						for j in range(y, y2+1):
							for k in range(z, z2+1):
								if not self.client.AllowedToBuild(i, j, k):
									return
									if (i + j + k) % 2 == 0:
										ticker = 1
									else:
										ticker = 0
									if ticker == 0:
										world[i, j, k] = block
									else:
										world[i, j, k] = block2
								if ticker == 0:
									self.client.queueTask(TASK_BLOCKSET, (i, j, k, block2), world=world)
									self.client.sendBlock(i, j, k, block2)
								else:
									self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
									self.client.sendBlock(i, j, k, block)
								self.client.total += 1
								yield
				except AssertionError:
					self.client.sendServerMessage("Out of bounds bcb error.")
					return
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

	@config("category", "build")
	def commandBhcb(self, parts, fromloc, overriderank):
		"/bhcb blockname blockname2 [x y z x2 y2 z2] - Guest\nSets all blocks in this area to blocks, checkered hollow."
		if len(parts) < 9 and len(parts) != 3:
			self.client.sendServerMessage("Please enter two block types")
		else:
			block = self.client.GetBlockValue(parts[1])
			block2 = self.client.GetBlockValue(parts[2])
			if block == None or block2 == None:
				return
			if not self.client.canUseRestrictedBlocks(block) or not self.client.canUseRestrictedBlocks(block2):
				self.client.sendServerMessage("Sorry, but you are not allowed to use that block.")
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
					self.client.sendServerMessage("All coordinate parameters must be integers.")
					return
			# Reverse the coordinate, if necessary.
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
					self.client.sendServerMessage("Sorry, that area is too big for you to bhcb (Limit is %s)" % limit)
					return

			# Draw all the blocks on, I guess
			# We use a generator so we can slowly release the blocks
			# We also keep world as a local so they can't change worlds and affect the new one
			world = self.client.world
			def generate_changes():
				ticker = 0
				try:
					for i in range(x, x2+1):
						for j in range(y, y2+1):
							for k in range(z, z2+1):
								if not self.client.AllowedToBuild(i, j, k):
									return
								if i == x or i == x2 or j == y or j == y2 or k == z or k == z2:
									if (i + j + k) % 2 == 0:
										ticker = 1
									else:
										ticker = 0
									if ticker == 0:
										world[i, j, k] = block
									else:
										world[i, j, k] = block2
									if ticker == 0:
										self.client.queueTask(TASK_BLOCKSET, (i, j, k, block2), world=world)
										self.client.sendBlock(i, j, k, block2)
									else:
										self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
										self.client.sendBlock(i, j, k, block)
									self.client.total += 1
									yield
				except AssertionError:
					self.client.sendServerMessage("Out of bounds bhcb error.")
					return

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
						self.client.finalizeMassCMD('bhcb', self.client.total)
					pass
			do_step()

	@config("category", "build")
	def commandFBlb(self, parts, fromloc, overriderank):
		"/bfb blockname [x y z x2 y2 z2] - Guest\nSets all blocks in this area to block, wireframe."
		if len(parts) < 8 and len(parts) != 2:
			self.client.sendServerMessage("Please enter a block type.")
		else:
			block = self.client.GetBlockValue(parts[1])
			if block == None:
				return
			if not self.client.canUseRestrictedBlocks(block):
				self.client.sendServerMessage("Sorry, but you are not allowed to use that block.")
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
					self.client.sendServerMessage("All coordinate parameters must be integers.")
					return
			# Reverse the coordinate, if necessary.
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
					self.client.sendServerMessage("Sorry, that area is too big for you to bfb (Limit is %s)" % limit)
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
								if not self.client.AllowedToBuild(i, j, k):
									return
								if ((i == x and j == y) or (i == x2 and j == y2) or (j == y2 and k == z2) or (i == x2 and k == z2) or \
									(j == y and k == z) or (i == x and k == z) or (i == x and k == z2) or (j == y and k == z2) or \
									(i == x2 and k == z) or (j == y2 and k == z) or (i == x and j == y2) or (i == x2 and j == y)):
									world[i, j, k] = block
									self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
									self.client.sendBlock(i, j, k, block)
									self.client.total += 1
									yield
				except AssertionError:
					self.client.sendServerMessage("Out of bounds bfb error.")
					return
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
						self.client.finalizeMassCMD('bfb', self.client.total)
						self.client.total = 0
					pass
			do_step()

#	@config("rank", "owner")
#	@on_off_command
#	def commandToggleUseBlb(self, onoff, fromloc, overriderank):
#		"/useblblimit on|off - Owner\nSet if the server will use custom BLB limit or the default limit."
#		if onoff == "on":
#			self.client.factory.useblblimit = True
#			self.client.sendServerMessage("Custom BLB Limit is now on.")
#		else:
#			self.client.factory.useblblimit = False
#			self.client.sendServerMessage("Custom BLB Limit is now off.")