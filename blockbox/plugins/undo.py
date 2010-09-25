# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from lib.twisted.internet import reactor
maxundos = 3000

class UndoPlugin(ProtocolPlugin):
	
	commands = {
		"undo": "commandUndo",
		"redo": "commandRedo",
	}
	
	hooks = {
		"blockchange": "blockChanged",
		"newworld": "newWorld",
	}
	def gotClient(self):
		self.client.var_undolist = []
		self.client.var_redolist = []
	
	def blockChanged(self, x, y, z, block, selected_block, byuser):
		"Hook trigger for block changes."
		world = self.client.world
		originalblock = world.blockstore.raw_blocks[world.blockstore.get_offset(x, y, z)]
		block = chr(block)
		if len(self.client.var_undolist) < maxundos:
			self.client.var_undolist.insert(0,((x,y,z),block,originalblock))
		else:
			del self.client.var_undolist[-1]
			self.client.var_undolist.insert(0,((x,y,z),block,originalblock))
	def newWorld(self, world):
		"Hook to reset undolist in new worlds."
		self.client.var_undolist = []

	@build_list
	def commandUndo(self, parts, byuser, overriderank):
		"/undo numchanges [username] - Guest\nUndoes yours or other people's changes (If Mod+)"
		world = self.client.world
		if len(parts) == 3:
			if not self.client.isMod():
				self.client.sendServerMessage("You are not a Mod+")
				return
			try:
				username = parts[2].lower()
				user = self.client.factory.usernames[username]
			except:
				self.client.sendServerMessage("%s is not online." % parts[2])
				return
			var_sublist = user.var_undolist[:]
			undolistlength = len(user.var_undolist)
			if parts[1] == "all":
				def generate_changes():
					try:
						user = self.client.factory.usernames[username]
						for index in range(undolistlength):
							originalblock = user.var_undolist[index][2]
							block = user.var_undolist[index][1]
							i,j,k = user.var_undolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You do not have permission to build here.")
								return
							del var_sublist[var_sublist.index(((i,j,k),block,originalblock))]
							user.var_redolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds undo error.")
								return
							user.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							user.sendBlock(i, j, k, originalblock)
							yield
						user.var_undolist = var_sublist
					except:
						self.client.sendSplitServerMessage("The user seems to have logged off before the undo could finish.")
						return
			else:
				try:
					num = int(parts[1])
				except:
					self.client.sendServerMessage("The numchanges must be a number or 'all'.")
					return
				if num > undolistlength:
					self.client.sendServerMessage("They have not made that many changes.")
					return
				def generate_changes():
					try:
						for index in range(num):
							originalblock = user.var_undolist[index][2]
							block = user.var_undolist[index][1]
							i,j,k = user.var_undolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You do not have permission to build here.")
								return
							del var_sublist[var_sublist.index(((i,j,k),block,originalblock))]
							user.var_redolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds undo error.")
								return
							user.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							user.sendBlock(i, j, k, originalblock)
							yield
						user.var_undolist = var_sublist
					except:
						self.client.sendSplitServerMessage("The user seems to have logged off before the undo could finish.")
						return
		else:
			self.client.sublist = self.client.var_undolist[:]
			undolistlength = len(self.client.var_undolist)
			if len(parts) == 1:
				self.client.sendSplitServerMessage("Please specify a number of changes to undo or 'all' (and if you are Mod+ you can specify a username)")
				return
			else:
				if parts[1] == "all":
					def generate_changes():
						for index in range(undolistlength):
							originalblock = self.client.var_undolist[index][2]
							block = self.client.var_undolist[index][1]
							i,j,k = self.client.var_undolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You no longer have permission to build here.")
								return
							del self.client.sublist[self.client.sublist.index(((i,j,k),block,originalblock))]
							self.client.var_redolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds undo error.")
								return
							self.client.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							self.client.sendBlock(i, j, k, originalblock)
							yield
						self.client.var_undolist = self.client.sublist
				else:
					try:
						num = int(parts[1])
					except:
						self.client.sendServerMessage("The numchanges must be a number or 'all'.")
						return
					if num > undolistlength:
						self.client.sendServerMessage("You have not made that many changes.")
						return
					def generate_changes():
						for index in range(num):
							originalblock = self.client.var_undolist[index][2]
							block = self.client.var_undolist[index][1]
							i,j,k = self.client.var_undolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You no longer have permission to build here.")
								return
							del self.client.sublist[self.client.sublist.index(((i,j,k),block,originalblock))]
							self.client.var_redolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds undo error.")
								return
							self.client.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							self.client.sendBlock(i, j, k, originalblock)
							self.total = self.total+1
							yield
						self.client.var_undolist = self.client.sublist
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
					self.client.finalizeMassCMD('undo', self.total)
					del self.total
				pass
		do_step()

	@build_list
	def commandRedo(self, parts, byuser, overriderank):
		"/redo numchanges [username] - Guest\nRedoes yours or other people's changes (If Mod+)"
		world = self.client.world
		if len(parts) == 3:
			if not self.client.isMod():
				self.client.sendServerMessage("You are not a Mod+")
				return
			try:
				username = parts[2].lower()
				user = self.client.factory.usernames[username]
			except:
				self.client.sendServerMessage("%s is not online." % parts[2])
				return
			var_sublist = user.var_redolist[:]
			redolistlength = len(user.var_redolist)
			if parts[1] == "all":
				def generate_changes():
					try:
						user = self.client.factory.usernames[username]
						for index in range(redolistlength):
							originalblock = user.var_redolist[index][2]
							block = user.var_redolist[index][1]
							i,j,k = user.var_redolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You do not have permission to build here.")
								return
							del var_sublist[var_sublist.index(((i,j,k),block,originalblock))]
							user.var_undolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds redo error.")
								return
							user.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							user.sendBlock(i, j, k, originalblock)
							self.total = self.total+1
							yield
						user.var_redolist = var_sublist
					except:
						self.client.sendSplitServerMessage("The user seems to have logged off before the redo could finish.")
						return
			else:
				try:
					num = int(parts[1])
				except:
					self.client.sendServerMessage("The numchanges must be a number or 'all'.")
					return
				if num > redolistlength:
					self.client.sendServerMessage("They have not made that many undos.")
					return
				def generate_changes():
					try:
						for index in range(num):
							originalblock = user.var_redolist[index][2]
							block = user.var_redolist[index][1]
							i,j,k = user.var_redolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You do not have permission to build here.")
								return
							del var_sublist[var_sublist.index(((i,j,k),block,originalblock))]
							user.var_undolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds redo error.")
								return
							user.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							user.sendBlock(i, j, k, originalblock)
							self.total = self.total+1
							yield
						user.var_redolist = var_sublist
					except:
						self.client.sendSplitServerMessage("The user seems to have logged off before the redo could finish.")
						return
		else:
			self.client.sublist = self.client.var_redolist[:]
			redolistlength = len(self.client.var_redolist)
			if len(parts) == 1:
				self.client.sendSplitServerMessage("Please specify a number of changes to redo or 'all' (and if you are Mod+ you can specify a username)")
				return
			else:
				if parts[1] == "all":
					def generate_changes():
						for index in range(redolistlength):
							originalblock = self.client.var_redolist[index][2]
							block = self.client.var_redolist[index][1]
							i,j,k = self.client.var_redolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You no longer have permission to build here.")
								return
							del self.client.sublist[self.client.sublist.index(((i,j,k),block,originalblock))]
							self.client.var_undolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds redo error.")
								return
							self.client.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							self.client.sendBlock(i, j, k, originalblock)
							self.total = self.total+1
							yield
						self.client.var_redolist = self.client.sublist
				else:
					try:
						num = int(parts[1])
					except:
						self.client.sendServerMessage("The numchanges must be a number or 'all'.")
						return
					if num > redolistlength:
						self.client.sendServerMessage("You have not made that many undos.")
						return
					def generate_changes():
						for index in range(num):
							originalblock = self.client.var_redolist[index][2]
							block = self.client.var_redolist[index][1]
							i,j,k = self.client.var_redolist[index][0]
							if not self.client.AllowedToBuild(i,j,k) and overriderank==False:
								self.client.sendServerMessage("You no longer have permission to build here.")
								return
							del self.client.sublist[self.client.sublist.index(((i,j,k),block,originalblock))]
							self.client.var_undolist.insert(0,((i,j,k),originalblock,block))
							try:
								world[i, j, k] = originalblock
							except AssertionError:
								self.client.sendServerMessage("Out of bounds redo error.")
								return
							self.client.queueTask(TASK_BLOCKSET, (i, j, k, originalblock), world=world)
							self.client.sendBlock(i, j, k, originalblock)
							self.total = self.total+1
							yield
						self.client.var_redolist = self.client.sublist
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
					self.client.finalizeMassCMD('redo', self.total)
					del self.total
				pass
		do_step()
