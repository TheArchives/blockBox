#    iCraft is Copyright 2010 both
#
#    The Archives team:
#                   <Adam Guy> adam@adam-guy.com AKA "Adam01"
#                   <Andrew Godwin> andrew@aeracode.org AKA "Aera"
#                   <Dylan Lukes> lukes.dylan@gmail.com AKA "revenant"
#                   <Gareth Coles> colesgareth2@hotmail.com AKA "gdude2002"
#
#    And,
#
#    The iCraft team:
#                   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#                   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#                   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#                   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#                   <James Kirslis> james@helplarge.com AKA "iKJames"
#                   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#                   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
#                   <Nick Tolrud> ntolrud@yahoo.com AKA "ntfwc"
#                   <Noel Benzinger> ronnygmod@gmail.com AKA "Dwarfy"
#                   <Randy Lyne> qcksilverdragon@gmail.com AKA "goober"
#                   <Willem van der Ploeg> willempieeploeg@live.nl AKA "willempiee"
#
#    iCraft is licensed under the Creative Commons
#    Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
#    To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#    Or, send a letter to Creative Commons, 171 2nd Street,
#    Suite 300, San Francisco, California, 94105, USA.

import random
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *
from myne.irc_client import *
from myne import *

class SlapPlugin(ProtocolPlugin):

    commands = {
        "slap": "commandSlap",
        "punch": "commandPunch",
    }

    @player_list
    def commandSlap(self, parts, byuser, overriderank):
        "/slap username [with object] - Guest\nSlap username [with object]."
	self.irc_relay = ChatBotFactory(self)
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
				self.irc_relay.sendServerMessage("%s slaps %s with %s!" % (self.client.username,name,object))
			else:
					self.client.sendWorldMessage("* "+COLOUR_PURPLE+"%s slaps %s with a giant smelly trout!" % (self.client.username,name))
					self.irc_relay.sendServerMessage("* %s slaps %s with a giant smelly trout!" % (self.client.username,name))

    @player_list
    def commandPunch(self, parts, byuser, overriderank):
        "/punch username [by bodypart] - Punch username [by bodypart]."
	self.irc_relay = ChatBotFactory(self)
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
				self.irc_relay.sendServerMessage("%s punches %s in the %s!" % (self.client.username,name,object))
			else: 
					self.client.sendWorldMessage("* "+COLOUR_PURPLE+"%s punches %s in the face!" % (self.client.username,name))
					self.irc_relay.sendServerMessage("* %s punches %s in the face!" % (self.client.username,name))
