# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from blockbox.persistence import PersistenceEngine as Persist
import logging
import datetime
import traceback
import random
import time
import cPickle
from blockbox.timer import ResettableTimer
from blockbox.persistence import PersistenceEngine as Persist

class CommandPlugin(ProtocolPlugin):
	
	commands = {
		"cmdhelp": "commandCmdHelp",
		"cmd": "commandCommand",
		"gcmd": "commandGuestCommand",
		"scmd": "commandSensorCommand",
		"gscmd": "commandGuestSensorCommand",
		"cmdend": "commandCommandend",
		"cmddel": "commandCommanddel",
		"cmddelend": "commandCommanddelend",
		"cmdshow": "commandShowcmdblocks",
		"cmdinfo": "commandcmdinfo",
	}
	
	hooks = {
		"blockclick": "blockChanged",
		"newworld": "newWorld",
		"poschange": "posChanged",
		"chatmsg": "message"
	}
	
	def gotClient(self):
		self.twocoordcommands = list(["blb", "bhb", "bwb", "mountain", "hill", "dune", "pit", "lake", "hole", "copy", "replace"])
		self.onecoordcommands = list(["sphere", "hsphere", "paste"])
		self.command_remove = False
		self.last_block_position = None
		self.command_cmd = list({})
		self.command_dest = None
		self.placing_cmd = False
		self.cmdinfo = False
		self.runningcmdlist = list({})
		self.runningsensor = False
		self.listeningforpay = False
		self.inputvar = None
		self.inputnum = None
		self.inputblock = None
		self.inputyn = None
		self.customvars = dict({})
		self.cmdinfolines = None
		self.infoindex = None

	def message(self, message):
		if self.cmdinfolines is not None:
			if message.lower() == "next":

				self.infoindex+=10
				index = int(self.infoindex)
				print self.cmdinfolines
				cmdlist = self.cmdinfolines[index:index+10]
				if len(cmdlist) < 10:
					print cmdlist
					print ("Reached the end.")
					if len(cmdlist) > 0:
						print len(self.cmdinfolines)
						self.client.sendServerMessage("Page %s of %s:" %(int((index+11)/10), int((len(self.cmdinfolines)/10)+1)))
						for x in cmdlist:
							self.client.sendServerMessage(x)
					self.client.sendServerMessage("Reached the end.")
					self.infoindex = None
					self.cmdinfolines = None
					return True
				print cmdlist
				self.client.sendServerMessage("Page %s of %s:" %(int((index+11)/10), int((len(self.cmdinfolines)/10)+1)))
				for x in cmdlist:
					self.client.sendServerMessage(x)
				return True
			elif message.lower() == "back":
				self.infoindex-=10
				try:
					cmdlist = self.cmdinfolines[self.infoindex:self.infoindex+10]
				except:
					self.infoindex+=10
					self.client.sendServerMessage("Reached the beginning.")
					return
				self.client.sendServerMessage("Page %s of %s:" %(int((self.infoindex+1)/10), int(len(self.cmdinfolist)/10)))
				for x in cmdlist:
					self.client.sendServerMessage(x)
				return True
			elif message.lower() == "cancel":
				self.infoindex = None
				self.cmdinfolines = None
				return True
			else:
				self.client.sendServerMessage("Please use next, back, or cancel.")
				return True
		if self.listeningforpay:
			if message.lower() == "y" or message.lower() == "yes":
				self.listeningforpay = False
				self.client.sendServerMessage("Payment confirmed!")
				try:
					x = self.runningcmdlist[0]
				except IndexError:
					return
				runcmd = True
				thiscmd = x
				thiscmd = thiscmd.replace(" /", "/") #sometimes the meta file stores it with a leading space :/
				if thiscmd.startswith("/gcmd"):
					guest = True
					runcmd = not self.runningsensor
				elif thiscmd.startswith("/gscmd"):
					guest = True
					runcmd = self.runningsensor
				elif thiscmd.startswith("/scmd"):
					guest = False
					runcmd = self.runningsensor
				else:
					guest = False
					runcmd = not self.runningsensor
				thiscmd = thiscmd.replace("/gcmd", "")
				thiscmd = thiscmd.replace("/cmd", "")
				thiscmd = thiscmd.replace("/gscmd", "")
				thiscmd = thiscmd.replace("/scmd", "")
				thiscmd = thiscmd.replace("$name", self.client.username)
				thiscmd = thiscmd.replace("$date", time.strftime("%m/%d/%Y",time.localtime(time.time())))
				thiscmd = thiscmd.replace("$time", time.strftime("%H:%M:%S",time.localtime(time.time())))
				parts = thiscmd.split()
				command = str(parts[0])
				self.runningcmdlist.remove(x)
				reactor.callLater(0.01, self.runcommands)
				if not command.lower() in self.client.commands:
					if runcmd:
						self.client.sendServerMessage("Unknown command '%s'" % command)
					runcmd = False
				try:
					func = self.client.commands[command.lower()]
				except KeyError:
					if runcmd:
						self.client.sendServerMessage("Unknown command '%s'" % command)
					runcmd = False
				try:
					if runcmd:
						func(parts, False, guest)
				except UnboundLocalError:
					self.client.sendServerMessage("Internal Server Error")
			elif message.lower() == "n" or message.lower() == "no":
				self.listeningforpay = False
				self.runningcmdlist = list({})
				self.runningsensor = False
				self.listeningforpay = False
				self.client.sendServerMessage("Payment declined.")
			else:
				self.client.sendServerMessage("Please use 'y' or 'n' to confirm.")
			return True
		if self.inputvar:
			self.customvars[self.inputvar] = message
			self.inputvar = None
			reactor.callLater(0.01, self.runcommands)
			return True
		if self.inputnum:
			try:
				int(message)
			except ValueError:
				self.client.sendServerMessage("Please enter an valid integer.")
				return True
			self.customvars[self.inputnum] = message
			self.inputnum = None
			reactor.callLater(0.01, self.runcommands)
			return True
		if self.inputblock:
			try:
				block = ord(self.client.GetBlockValue(message))
			except TypeError:
				#it was invalid
				return True
			if 49<block<0:
				self.client.sendServerMessage("Invalid block number.")
				return True
			self.customvars[self.inputblock] = message
			self.inputblock = None
			reactor.callLater(0.01, self.runcommands)
			return True
		if self.inputyn:
			if message=="y":
				self.customvars[self.inputyn] = message
				self.inputyn = None
				reactor.callLater(0.01, self.runcommands)
				return True
			elif message=="n":
				self.customvars[self.inputyn] = message
				self.inputyn = None
				reactor.callLater(0.01, self.runcommands)
				return True
			else:
				self.client.sendServerMessage("Please answer yes or no.")
				return True

	def blockChanged(self, x, y, z, block, byUser):
		"Hook trigger for block changes."
		#avoid infinite loops by making blocks unaffected by commands
		if not byUser:
			return False
		if self.client.world.has_command(x, y, z):
			if self.cmdinfo:
				cmdlist = self.client.world.get_command(x, y, z)
				
				if len(cmdlist)<11:
					self.client.sendServerMessage("Page 1 of 1:")
					for x in cmdlist:
						self.client.sendServerMessage(x)
				else:
					self.client.sendServerMessage("Page 1 of %s:" %int((len(cmdlist)/10)+1))
					for x in cmdlist[:9]:
						self.client.sendServerMessage(x)
					self.infoindex = 0
					self.cmdinfolines = cmdlist
				return False
			if self.command_remove is True:
				self.client.world.delete_command(x, y, z)
				self.client.sendServerMessage("You deleted a command block.")
			else:
				if self.listeningforpay:
					self.client.sendServerMessage("Please confirm or cancel payment before using a cmdblock.")
					return False
				if self.inputvar is not None or self.inputnum is not None or self.inputblock is not None or self.inputyn is not None:
					self.client.sendServerMessage("Please give input before using a cmdblock")
					return False
				if self.cmdinfolines is not None:
					self.client.sendServerMessage("Please complete the cmdinfo before using a cmdblock.")
					return False
				self.runningcmdlist = list(self.client.world.get_command(x, y, z))
				self.runningsensor = False
				reactor.callLater(0.01, self.runcommands)
				return False
		if self.command_cmd:
			if self.placing_cmd:
				self.client.sendServerMessage("You placed a command block. Type /cmdend to stop.")
				self.client.world.add_command(x, y, z, self.command_cmd)

	def newWorld(self, world):
		"Hook to reset Command abilities in new worlds if not op."
		if not self.client.isWriter():
			self.command_cmd = None
			self.command_remove = False
			
	def posChanged(self, x, y, z, h, p):
		"Hook trigger for when the player moves"
		rx = x >> 5
		ry = y >> 5
		rz = z >> 5
		try:
			if self.client.world.has_command(rx, ry, rz) and (rx, ry, rz) != self.last_block_position:
				if self.listeningforpay:
					self.client.sendServerMessage("Please confirm or cancel payment before using a cmdblock.")
					return False
				if self.inputvar is not None or self.inputnum is not None or self.inputblock is not None or self.inputyn is not None:
					self.client.sendServerMessage("Please give input before using a cmdblock")
					return False
				self.runningcmdlist = list(self.client.world.get_command(rx, ry, rz))
				self.runningsensor = True
				reactor.callLater(0.01, self.runcommands)
		except AssertionError:
			pass
		self.last_block_position = (rx, ry, rz)

	@info_list
	@writer_only
	def commandCmdHelp(self, parts, byuser, overriderank):
		"/cmdhelp category [subcategory] - Builder\ncmdblocks help, learn what you can do in them."
		if len(parts) > 1:
			if parts[1].lower() == "types":
				if len(parts) > 2:
					if parts[2].lower() == "cmd":
						self.client.sendSplitServerMessage("cmd - This is the main type of cmdblocks. Activated by clicking the block, these commands will only work if the user can.")
					elif parts[2].lower() == "gcmd":
						self.client.sendSplitServerMessage("gcmd - This is the guest type of cmdblocks. Activated by clicking the block, these commands will work for anyone.")
					elif parts[2].lower() == "scmd":
						self.client.sendSplitServerMessage("scmd - This is the sensor type of cmdblocks. Activated by passing through, these commands will only work if the user can.")
					elif parts[2].lower() == "gscmd":
						self.client.sendSplitServerMessage("gscmd - This is the guest sensor of cmdblocks. Activated by passing through, these commands will work for anyone.")
					else:
						self.client.sendServerMessage("That subcategory doesn't exist.")
				else:
					self.client.sendServerMessage("cmdblocks Help - Types")
					self.client.sendServerMessage("There are many types of cmdblocks.")
					self.client.sendServerMessage("Subcategories: cmd gcmd scmd gscmd")
			elif parts[1].lower() == "functions":
				if len(parts) > 2:
					if parts[2].lower() == "self":
						self.client.sendServerMessage("self message - Outputs a message like a msgblock.")
					elif parts[2].lower() == "exit":
						self.client.sendServerMessage("exit - Stops the cmdblock, no more commands.")
					elif parts[2].lower() == "wait":
						self.client.sendServerMessage("wait seconds - Pauses the cmdblock for x seconds.")
					elif parts[2].lower() == "getinput":
						self.client.sendSplitServerMessage("getinput varname displaymsg - Pauses the cmdblock waiting for input. The input will be any type of data, stores it for retrieval via $varname")
					elif parts[2].lower() == "getnum":
						self.client.sendSplitServerMessage("getnum varname displaymsg - Pauses the cmdblock waiting for num input. The input will be any type of number, stores it for retrieval via $varname")
					elif parts[2].lower() == "getblock":
						self.client.sendSplitServerMessage("getblock varname displaymsg - Pauses the cmdblock waiting for block input. The input will be any type of block, stores it for retrieval via $varname")
					elif parts[2].lower() == "getyesno":
						self.client.sendSplitServerMessage("getyesno varname displaymsg - Pauses the cmdblock waiting for yesno input. The input will be a 'y' or 'n', stores it for retrieval via $varname")
					else:
						self.client.sendServerMessage("That subcategory doesn't exist.")
				else:
					self.client.sendServerMessage("cmdblocks Help - Functions")
					self.client.sendSplitServerMessage("In cmdblocks there are functions, these are commands that exist only in cmdblocks and can't be done seperate.")
					self.client.sendSplitServerMessage("Subcategories: getblock getinput getnum getyesno exit self wait")
			elif parts[1].lower() == "variables":
				if len(parts) > 2:
					if parts[2].lower() == "bank":
						self.client.sendServerMessage("$bank - Balance of the player.")
					elif parts[2].lower() == "block":
						self.client.sendServerMessage("$block(x,y,x) - Block type, as a integer, for xyz")
					elif parts[2].lower() == "bname":
						self.client.sendServerMessage("$bname - Returns the block num as name, can use with $block")
					elif parts[2].lower() == "cname":
						self.client.sendServerMessage("$cname - Name color of the player.")
					elif parts[2].lower() == "date":
						self.client.sendServerMessage("$date - Date of the server, Month/Day/Year")
					elif parts[2].lower() == "eval":
						self.client.sendServerMessage("$eval(expression) - Evaluate the string, returns the cal.")
					elif parts[2].lower() == "first":
						self.client.sendServerMessage("$first - True if first time, False if not.")
					elif parts[2].lower() == "irc":
						self.client.sendServerMessage("$irc - Returns the IRC network and channel.")
					elif parts[2].lower() == "ircchan":
						self.client.sendServerMessage("$ircchan - Returns the IRC channel.")
					elif parts[2].lower() == "ircnet":
						self.client.sendServerMessage("$ircnet - Returns the IRC network.")
					elif parts[2].lower() == "name":
						self.client.sendServerMessage("$name - Username of the player.")
					elif parts[2].lower() == "owner":
						self.client.sendServerMessage("$owner - Returns the server owner.")
					elif parts[2].lower() == "posa":
						self.client.sendServerMessage("$posa - Returns the xyz of the player.")
					elif parts[2].lower() == "posx":
						self.client.sendServerMessage("$posx - Returns the x of the player.")
					elif parts[2].lower() == "posy":
						self.client.sendServerMessage("$posy - Returns the y of the player.")
					elif parts[2].lower() == "posz":
						self.client.sendServerMessage("$posz - Returns the z of the player.")
					elif parts[2].lower() == "rank":
						self.client.sendServerMessage("$rank - Rank name of the player.")
					elif parts[2].lower() == "ranknum":
						self.client.sendServerMessage("$ranknum - Rank number of the player.")
					elif parts[2].lower() == "rnd":
						self.client.sendServerMessage("$rnd(min,max) - Returns a random number between the min and max.")
					elif parts[2].lower() == "server":
						self.client.sendServerMessage("$server - Name of the server.")
					elif parts[2].lower() == "time":
						self.client.sendServerMessage("$time - Time of the server, hours:minutes:seconds")
					else:
						self.client.sendServerMessage("That subcategory doesn't exist.")
				else:
					self.client.sendServerMessage("cmdblocks Help - Variables")
					self.client.sendSplitServerMessage("In cmdblocks there are variables, these get replaced with the respectful information when the user uses a cmdblock. All Variables start with a $ for use and work in very purposes like display and IFs.")
					self.client.sendSplitServerMessage("Subcategories: bank block bname cname date eval first irc ircchan ircnet name owner posa posx posy posz rank ranknum rnd server time")
			else:
				self.client.sendServerMessage("That category doesn't exist.")
		else:
			self.client.sendServerMessage("cmdblocks Help - Use: /cmdhelp category [subcategory]")
			self.client.sendSplitServerMessage("Categories: types functions variables")

	@writer_only
	def commandCommand(self, parts, byuser, permissionoverride):
		"/cmd command [arguments] - Builder\nStarts creating a command block, or adds a command to the command block.\nThe command can be any server command.\nAfter you have entered all commands, type /cmd again to begin placing.\nOnce placed, the blocks will run the command when clicked\nas if the one clicking had typed the commands."
		if len(parts) < 2:
			if self.command_cmd == list({}):
				self.client.sendServerMessage("Please enter a command.")
			else:
				self.placing_cmd = True
				self.client.sendServerMessage("You are now placing command blocks.")
		else:
			if parts[1] in self.twocoordcommands:
				if len(parts) <  8:
					if len(self.client.last_block_changes) > 1:
						x, y, z = self.client.last_block_changes[0]
						x2, y2, z2 = self.client.last_block_changes[1]
						parts.append(x)
						parts.append(y)
						parts.append(z)
						parts.append(x2)
						parts.append(y2)
						parts.append(z2)
						
			if parts[1] in self.onecoordcommands:
				if len(parts) < 5:
					if len(self.client.last_block_changes) > 1:
						x, y, z = self.client.last_block_changes[0]
						parts.append(x)
						parts.append(y)
						parts.append(z)
			commandtext = ""
			for x in parts:
				   commandtext = commandtext + " " + str(x)
			if not self.command_cmd is None:
				if len(self.command_cmd) == 50:
						self.client.sendServerMessage("You can only use 50 commands per block!")
				else:	   
					self.command_cmd.append(commandtext)
					if len(self.command_cmd) > 1:	 
						self.client.sendServerMessage("Command added.")
					else:
						self.client.sendServerMessage("You are now creating a command block.")
						self.client.sendServerMessage("Use /cmd command again to add a command")
						self.client.sendServerMessage("Type /cmd with no args to start placing the block.")

	@mod_only					
	def commandGuestCommand(self, parts, byuser, permissionoverride):
		"/gcmd command [arguments] - Mod\nMakes the next block you place a guest command block."
		if len(parts) < 2:
			if self.command_cmd == list({}):
				self.client.sendServerMessage("Please enter a command.")
			else:
				self.client.sendServerMessage("You are now placing guest command blocks.")
				self.placing_cmd = True
		else:
			if parts[1] in self.twocoordcommands:
				if len(parts) <  8:
					if len(self.client.last_block_changes) > 1:
						x, y, z = self.client.last_block_changes[0]
						x2, y2, z2 = self.client.last_block_changes[1]
						parts.append(x)
						parts.append(y)
						parts.append(z)
						parts.append(x2)
						parts.append(y2)
						parts.append(z2)
						
			if parts[1] in self.onecoordcommands:
				if len(parts) < 5:
					if len(self.client.last_block_changes) > 1:
						x, y, z = self.client.last_block_changes[0]
						parts.append(x)
						parts.append(y)
						parts.append(z)
			commandtext = ""
			command = str(parts[1])
			cmdspecials = ["wait", "if", "exit", "getinput", "getnum", "getblock", "getyn", "self"] #not actual commands but can be used in cmdblocks
			if not command in cmdspecials:
				if command.lower() in self.client.commands:
					func = self.client.commands[command.lower()]
				else:
					self.client.sendServerMessage("Unknown command '%s'" % command)
					return
				if (self.client.isSpectator() and (getattr(func, "admin_only", False) or getattr(func, "mod_only", False) or getattr(func, "op_only", False) or getattr(func, "advbuilder_only", False) or getattr(func, "worldowner_only", False) or getattr(func, "writer_only", False))):

					return

				if getattr(func, "director_only", False) and not self.client.isDirector():

					return

				if getattr(func, "admin_only", False) and not self.client.isAdmin():

					return

				if getattr(func, "mod_only", False) and not (self.client.isMod() or self.client.isAdmin()):

					return

				if getattr(func, "op_only", False) and not (self.client.isOp() or self.isWorldOwner() or self.client.isMod()):

					return

				if getattr(func, "worldowner_only", False) and not (self.client.isWorldOwner() or self.client.isMod()):

					return

				if getattr(func, "advbuilder_only", False) and not (self.client.isAdvBuilder() or self.client.isOp() or self.client.isWorldOwner() or self.client.isMod()):

					return

				if getattr(func, "writer_only", False) and not (self.client.isWriter() or self.client.isOp() or self.client.isWorldOwner() or self.client.isMod()):

					return
			for x in parts:
				   commandtext = commandtext + " " + str(x)
			if not self.command_cmd is None:
				if len(self.command_cmd) == 50:
						self.client.sendServerMessage("You can only use 50 commands per block!")
				else:	   
					self.command_cmd.append(commandtext)
					if len(self.command_cmd) > 1:	 
						self.client.sendServerMessage("Command added.")
					else:
						self.client.sendServerMessage("You are now creating a guest command block.")
						self.client.sendServerMessage("WARNING: Commands on this block can be run by ANYONE")
						self.client.sendServerMessage("Use /gcmd command again to add a command")
						self.client.sendServerMessage("Type /gcmd with no args to start placing the block.")
						
	@writer_only
	def commandSensorCommand(self, parts, byuser, permissionoverride):
		"/scmd command [arguments] - Builder\nStarts creating a command block, or adds a command to the command block.\nThe command can be any server command.\nAfter you have entered all commands, type /cmd again to begin placing.\nOnce placed, the blocks will run the command when clicked\nas if the one clicking had typed the commands."
		if len(parts) < 2:
			if self.command_cmd == list({}):
				self.client.sendServerMessage("Please enter a command.")
			else:
				self.placing_cmd = True
				self.client.sendServerMessage("You are now placing sensor command blocks.")
		else:
			twocoordcommands=["blb", "bhb", "bwb", "mountain", "hill", "dune", "pit", "lake", "hole", "copy", "replace"]
			onecoordcommands=["sphere", "hsphere", "paste"]
			if parts[1] in self.twocoordcommands:
				if len(parts) <  8:
					if len(self.client.last_block_changes) > 1:
						x, y, z = self.client.last_block_changes[0]
						x2, y2, z2 = self.client.last_block_changes[1]
						parts.append(x)
						parts.append(y)
						parts.append(z)
						parts.append(x2)
						parts.append(y2)
						parts.append(z2)
						
			if parts[1] in self.onecoordcommands:
				if len(parts) < 5:
					if len(self.client.last_block_changes) > 1:
						x, y, z = self.client.last_block_changes[0]
						parts.append(x)
						parts.append(y)
						parts.append(z)
			commandtext = ""
			for x in parts:
				   commandtext = commandtext + " " + str(x)
			if not self.command_cmd is None:
				if len(self.command_cmd) == 50:
						self.client.sendServerMessage("You can only use 50 commands per block!")
				else:	   
					self.command_cmd.append(commandtext)
					if len(self.command_cmd) > 1:	 
						self.client.sendServerMessage("Command added.")
					else:
						self.client.sendServerMessage("You are now creating a sensor command block.")
						self.client.sendServerMessage("Use /scmd command again to add a command")
						self.client.sendServerMessage("Type /scmd with no args to start placing the block.")
						
	@mod_only					
	def commandGuestSensorCommand(self, parts, byuser, permissionoverride):
		"/gscmd command [arguments] - Mod\nMakes the next block you place a guest sensor command block."
		if len(parts) < 2:
			if self.command_cmd == list({}):
				self.client.sendServerMessage("Please enter a command.")
			else:
				self.client.sendServerMessage("You are now placing guest sensor command blocks.")
				self.placing_cmd = True
		else:
			if parts[1] in self.twocoordcommands:
				if len(parts) <  8:
					if len(self.client.last_block_changes) > 1:
						x, y, z = self.client.last_block_changes[0]
						x2, y2, z2 = self.client.last_block_changes[1]
						parts.append(x)
						parts.append(y)
						parts.append(z)
						parts.append(x2)
						parts.append(y2)
						parts.append(z2)
						
			if parts[1] in self.onecoordcommands:
				if len(parts) < 5:
					if len(self.client.last_block_changes) > 1:
						x, y, z = self.client.last_block_changes[0]
						parts.append(x)
						parts.append(y)
						parts.append(z)
			commandtext = ""
			command = str(parts[1])
			cmdspecials = ["wait", "if", "exit", "getinput", "getnum", "getblock", "getyn", "self"]  #not actual commands but can be used in cmdblocks
			if not command in cmdspecials:
				if command.lower() in self.client.commands:
					func = self.client.commands[command.lower()]
				else:
					self.client.sendServerMessage("Unknown command '%s'" % command)
					return
				if (self.client.isSpectator() and (getattr(func, "admin_only", False) or getattr(func, "mod_only", False) or getattr(func, "op_only", False) or getattr(func, "advbuilder_only", False) or getattr(func, "worldowner_only", False) or getattr(func, "writer_only", False))):

					self.client.sendServerMessage("'%s' is not available to specs." % command)

					return

				if getattr(func, "director_only", False) and not self.client.isDirector():

					self.client.sendServerMessage("'%s' is a Director-only command!" % command)

					return

				if getattr(func, "admin_only", False) and not self.client.isAdmin():

					self.client.sendServerMessage("'%s' is an Admin-only command!" % command)

					return

				if getattr(func, "mod_only", False) and not (self.client.isMod() or self.client.isAdmin()):

					self.client.sendServerMessage("'%s' is a Mod-only command!" % command)

					return

				if getattr(func, "op_only", False) and not (self.client.isOp() or self.client.isWorldOwner() or self.client.isMod()):

					self.client.sendServerMessage("'%s' is an Op-only command!" % command)

					return

				if getattr(func, "worldowner_only", False) and not (self.client.isWorldOwner() or self.client.isMod()):

					self.client.sendServerMessage("'%s' is an WorldOwner-only command!" % command)

					return

				if getattr(func, "advbuilder_only", False) and not (self.client.isAdvBuilder() or self.client.isMod()):

					self.client.sendServerMessage("'%s' is a Advanced Builder-only command!" % command)

					return

				if getattr(func, "writer_only", False) and not (self.client.isWriter() or self.client.isOp() or self.client.isWorldOwner() or self.client.isMod()):

					self.client.sendServerMessage("'%s' is a Builder-only command!" % command)

					return
			for x in parts:
				   commandtext = commandtext + " " + str(x)
			if not self.command_cmd is None:
				if len(self.command_cmd) == 50:
						self.client.sendServerMessage("You can only use 50 commands per block!")
				else:	   
					self.command_cmd.append(commandtext)
					if len(self.command_cmd) > 1:	 
						self.client.sendServerMessage("Command added.")
					else:
						self.client.sendServerMessage("You are now creating a guest sensor command block.")
						self.client.sendServerMessage("WARNING: Commands on this block can be run by ANYONE")
						self.client.sendServerMessage("Use /gscmd command again to add a command")
						self.client.sendServerMessage("Type /gscmd with no args to start placing the block.")

	@writer_only
	def commandCommandend(self, parts, byuser, permissionoverride):
		"/cmdend - Builder\nStops placing command blocks."
		self.command_cmd =  self.command_cmd = list({})
		self.command_remove = False
		self.placing_cmd = False
		self.client.sendServerMessage("You are no longer placing command blocks.")
	
	
	@writer_only
	def commandCommanddel(self, parts, byuser, permissionoverride):
		"/cmddel - Builder\nEnables Command-deleting mode"
		self.client.sendServerMessage("You are now able to delete command blocks. /cmddelend to stop")
		self.command_remove = True
	
	@writer_only
	def commandCommanddelend(self, parts, byuser, permissionoverride):
		"/cmddelend - Builder\nDisables Command-deleting mode"
		self.client.sendServerMessage("Command deletion mode ended.")
		self.command_remove = False
		
	@writer_only
	def commandShowcmdblocks(self, parts, byuser, permissionoverride):
	   "/cmdshow - Builder\nShows all command blocks as yellow, only to you."
	   for offset in self.client.world.commands.keys():
		   x, y, z = self.client.world.get_coords(offset)
		   self.client.sendPacked(TYPE_BLOCKSET, x, y, z, BLOCK_YELLOW)
	   self.client.sendServerMessage("All commands appearing yellow temporarily.")
	
	@writer_only
	@on_off_command
	def commandcmdinfo(self, onoff, byuser, permissionoverride):
	   "/cmdinfo - Builder\nTells you the commands in a cmdblock"
	   self.cmdinfo = onoff == "on"
	   self.client.sendServerMessage("Command block info is now %s." %onoff)



	def runcommands(self):
		try:
			x = self.runningcmdlist[0]
		except IndexError:
			self.customvars = dict({})
			return
		runcmd = True
		thiscmd = str(x)
		thiscmd = thiscmd.replace(" /", "/") #sometimes the meta file stores it with a leading space :/
		if thiscmd.startswith("/gcmd"):
			guest = True
			runcmd = not self.runningsensor
		elif thiscmd.startswith("/gscmd"):
			guest = True
			runcmd = self.runningsensor
		elif thiscmd.startswith("/scmd"):
			guest = False
			runcmd = self.runningsensor
		else:
			guest = False
			runcmd = not self.runningsensor
		thiscmd = thiscmd.replace("/gcmd", "")
		thiscmd = thiscmd.replace("/cmd", "")
		thiscmd = thiscmd.replace("/gscmd", "")
		thiscmd = thiscmd.replace("/scmd", "")
		thiscmd = thiscmd.replace("$name", self.client.username)
		thiscmd = thiscmd.replace("$cname", self.client.colouredUsername())
		user = self.client.username.lower()
		with Persist(user) as p:
			balance = p.int("bank", "balance", 0)
		thiscmd = thiscmd.replace("$bank", str(balance))
		with Persist(user) as p:
			lastseen = p.string("main", "lastseen", 0)
			if lastseen is 0:
				lastseen = "?"
		thiscmd = thiscmd.replace("$first", lastseen)
		thiscmd = thiscmd.replace("$server", self.client.factory.server_name)
		if self.client.factory.use_irc:
			thiscmd = thiscmd.replace("$irc", self.client.factory.conf_irc.get("irc", "server") + " " + self.client.factory.irc_channel)
			thiscmd = thiscmd.replace("$ircchan", self.client.factory.irc_channel)
			thiscmd = thiscmd.replace("$ircnet", self.client.factory.conf_irc.get("irc", "server"))
		thiscmd = thiscmd.replace("$owner", self.client.factory.owner)
		thiscmd = thiscmd.replace("$rcolor", self.client.userColour())
		thiscmd = thiscmd.replace("$rname", self.client.rankName())
		thiscmd = thiscmd.replace("$date", time.strftime("%m/%d/%Y",time.localtime(time.time())))
		thiscmd = thiscmd.replace("$time", time.strftime("%H:%M:%S",time.localtime(time.time())))
		myrank = "guest"
		myranknum = 1
		if self.client.isSpectator():
			myrank = "spec"
			myranknum = 0
		elif self.client.isOwner():
			myrank = "owner"
			myranknum = 9
		elif self.client.isDirector():
			myrank = "director"
			myranknum = 8
		elif self.client.isAdmin():
			myrank = "admin"
			myranknum = 7
		elif self.client.isMod():
			myrank = "mod"
			myranknum = 6
		elif self.client.isAdvBuilder():
			myrank = "advbuilder"
			myranknum = 3
		elif self.client.isOp():
			myrank = "op"
			myranknum = 4
		elif self.client.isWorldOwner():
			myrank = "worldowner"
			myranknum = 5
		elif self.client.isWriter():
			myrank = "builder"
			myranknum = 2
		rx = self.client.x >> 5
		ry = self.client.y >> 5
		rz = self.client.z >> 5
		thiscmd = thiscmd.replace("$posx", str(rx))
		thiscmd = thiscmd.replace("$posy", str(ry))
		thiscmd = thiscmd.replace("$posz", str(rz))
		thiscmd = thiscmd.replace("$posa", str(rx)+" "+str(ry)+" "+str(rx))
		thiscmd = thiscmd.replace("$rank", myrank)
		thiscmd = thiscmd.replace("$rnum", str(myranknum))
		for variable in self.customvars.keys():
			thiscmd = thiscmd.replace("$"+variable, str(self.customvars[variable]))
		for num in range(len(thiscmd)):
			if thiscmd[num:(num+4)] == "$rnd":
				try:
					limits = thiscmd[thiscmd.find("(", num)+1:thiscmd.find(")", num+5)].split(",")
					thiscmd = thiscmd.replace(thiscmd[num:thiscmd.find(")", num)+1], str(random.randint(int(limits[0]), int(limits[1])))) #holy crap this is complicated
				except:
					self.client.sendServerMessage("$rnd syntax error! Use $rnd(num1,num2)")
		for num in range(len(thiscmd)):
			if thiscmd[num:(num+6)] == "$block":
				try:
					coords = thiscmd[thiscmd.find("(", num)+1:thiscmd.find(")", num+5)].split(",")
					x = int(coords[0])
					y = int(coords[1])
					z = int(coords[2])
					check_offset = self.client.world.blockstore.get_offset(x, y, z)
					block = ord(self.client.world.blockstore.raw_blocks[check_offset])
					thiscmd = thiscmd.replace(thiscmd[num:thiscmd.find(")", num)+1], str(block)) #holy crap this is complicated
				except:
					self.client.sendServerMessage("$block syntax error! Use $block(x,y,z)")
		for num in range(len(thiscmd)):
			if thiscmd[num:(num+5)] == "$eval":
				try:
					parentheses = 0
					for num2 in range(num+6, len(thiscmd)-1):
						if thiscmd[num2] == "(":
							parentheses = parentheses+1
						elif thiscmd[num2] == ")":
							parentheses = parentheses-1
						if parentheses == 0:
							#We've reached the end of the expression
							lastindex = num2
					print str(thiscmd[thiscmd.find("(", num)+1:lastindex+1])
					expression = str(eval(thiscmd[thiscmd.find("(", num)+1:lastindex+1]))
					thiscmd = thiscmd.replace(thiscmd[num:lastindex+2], expression) #holy crap this is complicated
				except:
					self.client.sendServerMessage("$eval syntax error! Use $eval(expression)")
		blocklist = ["air", "rock", "grass", "dirt", "cobblestone", "wood", "plant", "solid", "water", "still water", "lava", "still lava", "sand", "gravel", "gold ore", "iron ore", "coal ore", "trunk", "leaf", "sponge", "glass", "red cloth", "orange cloth", "yellow cloth", "lime green cloth", "green cloth", "turquoise cloth", "cyan cloth", "blue cloth", "dark blue cloth", "violet cloth", "purple cloth", "magenta cloth", "pink cloth", "black cloth", "gray cloth", "white cloth", "flower", "rose", "red mushroom", "brown mushroom", "gold", "iron", "double step", "step", "brick", "TNT", "bookshelf", "mossy cobblestone", "obsidian"]
		for num in range(len(thiscmd)):
			if thiscmd[num:(num+6)] == "$bname":
				try:
					blocknum = int(thiscmd[thiscmd.find("(", num)+1:thiscmd.find(")", num+5)])
					thiscmd = thiscmd.replace(thiscmd[num:thiscmd.find(")", num)+1], blocklist[blocknum]) #holy crap this is complicated
				except:
					self.client.sendServerMessage("$bname syntax error! Use $bname(blockint)")
		if thiscmd.startswith(" if"):
			try:
				condition = thiscmd[4:thiscmd.find(":")]
				if (bool(eval(condition, {}, {}))) == False:
					runcmd=False
				thiscmd = thiscmd.replace(thiscmd[:thiscmd.find(":")+1], "")
			except:
				self.client.sendServerMessage("if syntax error! Use if a=b: command!")
				
		parts = thiscmd.split()
		
		command = str(parts[0])


		#since whispers aren't commands, we have to handle it seperately...
		if command.startswith("@"):
			runcmd = False
			username = command.lstrip("@").lower()
			text = ""
			firstword = True #This is to keep the @username part from being included as text
			for word in parts:
				if not firstword:
					text = text + " " + word
				firstword = False
			if text == "":
				self.client.sendServerMessage("Please include a message to send.")
			else:

				if username in self.client.factory.usernames:
					self.client.factory.usernames[username].sendWhisper(self.client.username, text)

					self.client.sendWhisper(self.client.username, text)

					self.client.log("@"+self.client.username+" to "+username+": "+text)

					self.client.whisperlog.write(datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M")+" | @"+self.client.username+" to "+username+": "+text+"\n")

					self.client.whisperlog.flush()

				else:

					self.client.sendServerMessage("%s is currently offline." % username)


		#Require confirmation
		if command == "pay":
			try:
				target = parts[1]
				amount = int(parts[2])
			except:
				self.client.sendServerMessage("Pay syntax error.")
				runcmd = False
			if runcmd:
				user = self.client.username.lower()
				with Perist(user) as p:
					balance = p.int("bank", "balance", -1)
			if balance is not -1:
				if balance >= amount:
					self.listeningforpay = True
					self.client.sendServerMessage("%s is requesting payment of C%s. Pay? [Y/N]" %(target, amount))
					return
				else:
					self.client.sendServerMessage("You don't have enough money to pay!")
					self.runningcmdlist = list({})
					self.runningsensor = False
					return
			else:
				self.client.sendServerMessage("You don't have a bank account!")
				self.runningcmdlist = list({})
				self.runningsensor = False
				return
		# Look for command
		if command == "self" and runcmd:
			msg = ""
			parts.pop(0)
			msg = " ".join(parts)
			self.client._sendMessage(COLOUR_GREEN, msg)
			runcmd = False
		if command == "wait" and runcmd:
			delay = float(0.1)
			try:
				delay = float(parts[1])
			except:
				self.client.sendServerMessage("Wait time must be a number!")
				runcmd = False
			self.runningcmdlist.remove(self.runningcmdlist[0])
			reactor.callLater(delay, self.runcommands)
			return
		if command == "exit" and runcmd:
			self.runningcmdlist = list({})
			return
		if command == "getinput" and runcmd:
			try:
				self.inputvar = parts[1]
			except IndexError:
				self.client.sendServerMessage("You must give a variable name!")
				runcmd = False
			if runcmd:
				if len(parts)>2:
					self.client.sendServerMessage("[INPUT] "+" ".join(parts[2:]))
				else:
					self.client.sendServerMessage("This command block is requesting input.")
				self.runningcmdlist.remove(self.runningcmdlist[0])
				return
		if command == "getnum" and runcmd:
			try:
				self.inputnum = parts[1]
			except IndexError:
				self.client.sendServerMessage("You must give a variable name!")
				runcmd = False
			if runcmd:
				if len(parts)>2:
					self.client.sendServerMessage("[INPUT] "+" ".join(parts[2:]))
				else:
					self.client.sendServerMessage("This command block is requesting input.")
				self.runningcmdlist.remove(self.runningcmdlist[0])
				return
		if command == "getblock" and runcmd:
			try:
				self.inputblock = parts[1]
			except IndexError:
				self.client.sendServerMessage("You must give a variable name!")
				runcmd = False
			if runcmd:
				if len(parts)>2:
					self.client.sendServerMessage("[BLOCK INPUT] "+" ".join(parts[2:]))
				else:
					self.client.sendServerMessage("This command block is requesting block input.")
				self.runningcmdlist.remove(self.runningcmdlist[0])
				return
		if command == "getyesno" and runcmd:
			try:
				self.inputyn = parts[1]
			except IndexError:
				self.client.sendServerMessage("You must give a variable name!")
				runcmd = False
			if runcmd:
				if len(parts)>2:
					self.client.sendServerMessage("[Y/N] "+" ".join(parts[2:]))
				else:
					self.client.sendServerMessage("This command block is requesting yes/no input.")
				self.runningcmdlist.remove(self.runningcmdlist[0])
				return
		try:
			if not command.lower() in self.client.commands:
				if runcmd:
					self.client.sendServerMessage("Unknown command '%s'" % command)
				runcmd = False

			func = self.client.commands[command.lower()]
		except KeyError:
			if runcmd:
				self.client.sendServerMessage("Unknown command '%s'" % command)

				runcmd = False


		if runcmd is True:
			if guest is False:
				if (self.client.isSpectator() and (getattr(func, "admin_only", False) or getattr(func, "mod_only", False) or getattr(func, "op_only", False) or getattr(func, "advbuilder_only", False) or getattr(func, "worldowner_only", False) or getattr(func, "writer_only", False))):

					self.client.sendServerMessage("'%s' is not available to specs." % command)

					runcmd = False

				if getattr(func, "director_only", False) and not self.client.isDirector():

					self.client.sendServerMessage("'%s' is a Director-only command!" % command)

					runcmd = False

				if getattr(func, "admin_only", False) and not self.client.isAdmin():

					self.client.sendServerMessage("'%s' is an Admin-only command!" % command)

					runcmd = False

				if getattr(func, "mod_only", False) and not (self.client.isMod() or self.client.isAdmin()):

					self.client.sendServerMessage("'%s' is a Mod-only command!" % command)

					runcmd = False

				if getattr(func, "op_only", False) and not (self.client.isOp() or self.client.isMod()):

					self.client.sendServerMessage("'%s' is an Op-only command!" % command)

					runcmd = False

				if getattr(func, "worldowner_only", False) and not (self.client.isWorldOwner() or self.client.isMod()):

					self.client.sendServerMessage("'%s' is an WorldOwner-only command!" % command)

					runcmd = False

				if getattr(func, "advbuilder_only", False) and not (self.client.isAdvBuilder() or self.client.isOp() or self.client.isWorldOwner() or self.client.isMod()):

					self.client.sendServerMessage("'%s' is a Advanced Builder-only command!" % command)

					runcmd = False

				if getattr(func, "writer_only", False) and not (self.client.isWriter() or self.client.isOp() or self.client.isWorldOwner() or self.client.isMod()):

					self.client.sendServerMessage("'%s' is a Builder-only command!" % command)

					runcmd = False

			try:

				try:
					if runcmd:
						func(parts, False, guest)
				except UnboundLocalError:
					self.client.sendServerMessage("Internal server error.")
					self.client.log(traceback.format_exc(), "error")
			except Exception, e:

				self.client.sendServerMessage("Internal server error.")

				self.client.log(traceback.format_exc(), "error")
		self.runningcmdlist.remove(self.runningcmdlist[0])
		reactor.callLater(0.1, self.runcommands)

		

