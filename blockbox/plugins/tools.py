# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
import math
import random

class ToolsPlugin(ProtocolPlugin):
	
	commands = {
		"ruler": "commandRuler",
		"measure": "commandRuler",
		"roll": "commandRoll"
	}
	
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

	def commandRoll(self, parts, fromloc, overriderank):
		"/roll max - Guest\nRolls a random number from 1 to max. Announces to world."
		if len(parts) == 1:
			self.client.sendServerMessage("Please enter a number as the maximum roll.")
		else:
			try:
				roll = roll = int(math.floor((random.random()*(int(parts[1])-1)+1)))
			except ValueError:
				self.client.sendServerMessage("Please enter an integer as the maximum roll.")
			else:
				self.client.sendWorldMessage("%s rolled a %s" % (self.client.username, roll))
