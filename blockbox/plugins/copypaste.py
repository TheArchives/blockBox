# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

import sys

class BsavePlugin(ProtocolPlugin):
	
	commands = {
		"copy": "commandSave",
		"paste": "commandLoad",
		"rotate": "commandRotate"
	}
	
	@build_list
	@writer_only
	def commandLoad(self, parts, byuser, overriderank):
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
					if byuser:
						self.client.sendServerMessage("Your paste just completed.")
					pass
			do_step()

	@build_list
	@writer_only
	def commandSave(self, parts, byuser, overriderank):
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
				self.client.sendServerMessage("Sorry, that area is too big for you to copy.")
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
					if byuser:
						self.client.sendServerMessage("Your copy just completed.")
					pass
			do_step()

	@build_list
	@writer_only
	def commandRotate(self, parts, byuser, overriderank):
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
			self.client.bsaved_blocks = tempblocks
		if byuser:
			self.client.sendServerMessage("Your rotate just completed.")
