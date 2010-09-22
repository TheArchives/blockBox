
import random
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from blockbox.irc_client import *
from myne import *

class SlapPlugin(ProtocolPlugin):

	commands = {
		"slap": "commandSlap",
		"punch": "commandPunch",
	}

	@player_list
	def commandSlap(self, parts, byuser, overriderank):
		"/slap username [with object] - Guest\nSlap username [with object]."
		if len(parts) == 1:
			self.client.sendServerMessage("Enter the name for the slappee")
		else:
			stage = 0
			name = ''
			object = ''
			for i in range(1, len(parts)):
				if parts[i] == "with":
					stage = 1
					continue
					if stage == 0 : 
						name += parts[i]
						if (i+1 != len(parts) ) : 
							if ( parts[i+1] != "with" ) : name += " "
					else:
						object += parts[i]
						if ( i != len(parts) - 1 ) : object += " "
				else:
					if stage == 1:
						self.client.sendWorldMessage("* "+COLOUR_PURPLE+"%s slaps %s with %s!" % (self.client.username,name,object))
						self.client.factory.irc_relay.sendServerMessage("%s slaps %s with %s!" % (self.client.username,name,object))
					else:
						self.client.sendWorldMessage("* "+COLOUR_PURPLE+"%s slaps %s with a giant smelly trout!" % (self.client.username,name))
						self.client.factory.irc_relay.sendServerMessage("* %s slaps %s with a giant smelly trout!" % (self.client.username,name))

	@player_list
	def commandPunch(self, parts, byuser, overriderank):
		"/punch username [by bodypart] - Punch username [by bodypart]."
		if len(parts) == 1:
			self.client.sendServerMessage("Enter the name for the punchee")
		else:
			stage = 0
			name = ''
			object = ''
			for i in range(1, len(parts)):
				if parts[i] == "by":
					stage = 1
					continue
					if stage == 0 : 
						name += parts[i]
						if (i+1 != len(parts) ) : 
							if ( parts[i+1] != "by" ) : name += " "
					else:
						object += parts[i]
						if ( i != len(parts) - 1 ) : object += " "
				else:
					if stage == 1:
						self.client.sendWorldMessage("* "+COLOUR_PURPLE+"%s punches %s in the %s!" % (self.client.username,name,object))
						self.client.factory.irc_relay.sendServerMessage("%s punches %s in the %s!" % (self.client.username,name,object))
					else: 
						self.client.sendWorldMessage("* "+COLOUR_PURPLE+"%s punches %s in the face!" % (self.client.username,name))
						self.client.factory.irc_relay.sendServerMessage("* %s punches %s in the face!" % (self.client.username,name))
