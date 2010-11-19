# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import random

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class HidePlugin(ProtocolPlugin):
	commands = {
		"hide": "commandHide",
		"cloak": "commandHide",
	}
	hooks = {
		"playerpos": "playerMoved",
	}
	def gotClient(self):
		self.hidden = False
	def playerMoved(self, x, y, z, h, p):
		"Stops transmission of player positions if hide is on."
		if self.hidden:
			return False
	@player_list
	@op_only
	def commandHide(self, params, fromloc, overriderank):
		"/hide - Op\nAliases: cloak\nHides you so no other players can see you. Toggle."
		if not self.hidden:
			self.client.sendServerMessage("You have vanished.")
			self.hidden = True
			# Send the "player has disconnected" command to people
			self.client.queueTask(TASK_PLAYERLEAVE, [self.client.id])
		else:
			self.client.sendServerMessage("That was Magic!")
			self.hidden = False
			#Imagine that! They've mysteriously appeared.
			self.client.queueTask(TASK_NEWPLAYER, [self.client.id, self.client.username, self.client.x, self.client.y, self.client.z, self.client.h, self.client.p])
			#self.client.queueTask(TASK_PLAYERCONNECT, [self.client.id, self.client.username, self.client.x, self.client.y, self.client.z, self.client.h, self.client.p])
