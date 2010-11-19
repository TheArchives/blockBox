# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from blockbox.timer import ResettableTimer

class CountPlugin(ProtocolPlugin):

	commands = {
		"count": "commandCount",
		"countdown": "commandCount",
	}

	def gotClient(self):
		self.num = int(0)

	@writer_only
	def commandCount(self, parts, fromloc, overriderank):
		"/count [number] - Builder\nAliases: countdown\nCounts down from 3 or from number given (up to 15)"
		if self.num != 0:
			self.client.sendServerMessage("You can only have one count at a time!")
			return
		if len(parts) > 1:
			try:
				self.num = int(parts[1])
			except ValueError:
				self.client.sendServerMessage("Number must be an integer!")
				return
		else:
			self.num = 3
		if self.num > 15:
			self.client.sendServerMessage("You can't count from higher than 15!")
			self.num = 0
			return
		counttimer = ResettableTimer(self.num, 1, self.sendgo, self.sendcount)
		self.client.sendPlainWorldMessage("&2[COUNTDOWN] %s" %self.num)
		counttimer.start()

	def sendgo(self):
		self.client.sendPlainWorldMessage("&2[COUNTDOWN] GO!")
		self.num = 0

	def sendcount(self, count):
		if not int(self.num)-int(count) == 0:
			self.client.sendPlainWorldMessage("&2[COUNTDOWN] %s" %(int(self.num)-int(count)))