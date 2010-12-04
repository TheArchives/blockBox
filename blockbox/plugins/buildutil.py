# blockBox is Copyright 2009-2010 of the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class BuildUtilPlugin(ProtocolPlugin):
	"Commands for helping players to build."
	commands = {
		"ruler": "commandRuler",
		"measure": "commandRuler",
		"paint": "commandPaint",
		"bind": "commandBind",
		"material": "commandBind",		"replace": "commandReplace",
		"brep": "commandReplace",
		"creplace": "commandCreplace",
		"crep": "commandCreplace",
		"fill": "commandFill",		"copy": "commandSave",
		"paste": "commandLoad",
		"rotate": "commandRotate"
	}

	hooks = {
		"preblockchange": "preBlockChanged",		"blockchange": "blockChanged",
	}
	def gotClient(self):
		self.painting = False
		self.block_overrides = {}

	def preBlockChanged(self, x, y, z, block, selected_block, fromloc):
		"Hook trigger for block changes."
		if block is BLOCK_AIR and self.painting:			return selected_block
	def blockChanged(self, x, y, z, block, selected_block, fromloc):
		"Hook trigger for block changes."
		if block in self.block_overrides:
			return self.block_overrides[block]

	def canBreakAdminBlocks(self):
		"Shortcut for checking permissions."
		if hasattr(self.client, "world"):
			return (not self.client.world.admin_blocks) or self.client.isOp()
		else:
			return False

	@world_list
	def commandRuler(self, parts, fromloc, overriderank):
		"/ruler - Guest\nAliases: measure\nCounts the amount of blocks between two clicks."
		# Use the last two block places
		try:
			x, y, z = self.client.last_block_changes[0]
			x2, y2, z2 = self.client.last_block_changes[1]
		except IndexError:
			self.client.sendServerMessage("You have not clicked two blocks yet.")
			return
		xRange, yRange, zRange = abs(x - x2) + 1 , abs(y-y2) + 1, abs(z-z2) + 1
		self.client.sendServerMessage("X = %d, Y = %d, Z = %d" % (xRange, yRange, zRange) )

	@build_list
	def commandPaint(self, parts, fromloc, overriderank):
		"/paint - Guest\nLets you break-and-build in one move. Toggle."
		if self.painting:
			self.painting = False
			self.client.sendServerMessage("Painting mode is now off.")
		else:
			self.painting = True
			self.client.sendServerMessage("Painting mode is now on.")
	@build_list
	def commandAir(self, params, fromloc, overriderank):
		"/air - Guest\nAliases: place, stand\nPuts a block under you for easier building in the air."
		self.client.sendPacked(TYPE_BLOCKSET, self.client.x>>5, (self.client.y>>5)-3, (self.client.z>>5), BLOCK_WHITE)
	@build_list
	def commandBind(self, parts, fromloc, overriderank):
		"/bind blockA blockB - Guest\nAliases: build, material\nBinds blockB to blockA."
		if len(parts) == 1:
			if self.block_overrides:
				temp = tuple(self.block_overrides)
				for each in temp:
					del self.block_overrides[each]
				self.client.sendServerMessage("All blocks are back to normal")
				del temp
				return
			self.client.sendServerMessage("Please enter two block types.")
		elif len(parts) == 2:
			try:
				old = ord(self.client.GetBlockValue(parts[1]))
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
			if old == None:
				return
			old = ord(old)
			new = self.client.GetBlockValue(parts[2])
			if new == None:
				return
			new = ord(new)
			if ord(old) > 49 or ord (new):
				self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
				return
			if ord(new) == 7:
				try:
					username = self.client.factory.usernames[self.client.username.lower()]
				except:
					self.client.sendServerMessage("ERROR: Identity could not be confirmed")
					return
				if username.isDirector():
					pass
				elif username.isAdmin():
					pass
				elif username.isMod():
					pass
				elif username.isAdvBuilder():
					pass
				elif username.isOp():
					pass
				else:
					self.client.sendServerMessage("Solid is op-only")
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

	@build_list
	@writer_only
	def commandLoad(self, parts, fromloc, overriderank):
		"/paste [x y z] - Builder\nRestore blocks saved earlier using /copy"
		if len(parts) < 4 and len(parts) != 1:
			self.client.sendServerMessage("Please enter coordinates.")
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
					self.client.sendServerMessage("All parameters must be integers")
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
				for i, j, k, block in self.client.bsaved_blocks:
					if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
						return
					rx = x + i
					ry = y + j
					rz = z + k
					try:
						world[rx, ry, rz] = block
						self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
						self.client.sendBlock(rx, ry, rz, block)
						self.client.total += 1 # This is how you increase a number in python.... - Stacy
					except AssertionError:
						self.client.sendServerMessage("Out of bounds paste error.")
						return
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
						self.client.finalizeMassCMD('paste', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@writer_only
	def commandSave(self, parts, fromloc, overriderank):
		"/copy [x y z x2 y2 z2] - Builder\nCopy blocks using specified offsets."
		if len(parts) < 7 and len(parts) != 1:
			self.client.sendServerMessage("Please enter coordinates.")
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
					self.client.sendServerMessage("Sorry, that area is too big for you to copy (Limit is %s)" % limit)
					return

			self.client.bsaved_blocks = set()
			world = self.client.world
			def generate_changes():
				for i in range(x, x2+1):
					for j in range(y, y2+1):
						for k in range(z, z2+1):
							if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
								return
							try:
								check_offset = world.blockstore.get_offset(i, j, k)
								block = world.blockstore.raw_blocks[check_offset]
								self.client.bsaved_blocks.add((i -x, j - y, k -z, block))
								self.client.total += 1
							except AssertionError:
								self.client.sendServerMessage("Out of bounds copy error.")
								return
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
						self.client.finalizeMassCMD('copy', self.client.total)
						self.client.total = 0
					pass
			do_step()

	@build_list
	@writer_only
	def commandRotate(self, parts, fromloc, overriderank):
		"/rotate angle - Builder\nAllows you to rotate what you copied."
		if len(parts)<2:
			self.client.sendServerMessage("You must give an angle to rotate!")
			return
		try:
			angle = int(parts[1])
		except ValueError:
			self.client.sendServerMessage("Angle must be an integer!")
			return
		if angle % 90 != 0:
			self.client.sendServerMessage("Angle must be divisible by 90!")
			return
		rotations = angle/90
		self.client.sendServerMessage("Rotating %s degrees..." %angle)
		for rotation in range(rotations):
			tempblocks = set()
			xmax=zmax=0
			try:
				for x, y, z, block in self.client.bsaved_blocks:
					if x > xmax:
						xmax=x
					if z > zmax:
						zmax=z
			except:
				self.client.sendServerMessage("You haven't used /copy yet.")
				return
			for x, y, z, block in self.client.bsaved_blocks:
				tempx = x
				tempz = z
				x = zmax-tempz
				z = tempx
				tempblocks.add((x,y,z,block))
				self.client.total+1
			self.client.bsaved_blocks = tempblocks
		if fromloc == 'user':
			self.client.finalizeMassCMD('rotate', self.client.total)
			self.client.total = 0