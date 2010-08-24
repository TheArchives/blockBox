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

from twisted.internet import reactor
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *
import math
import random

class ToolsPlugin(ProtocolPlugin):
	
	commands = {
		"ruler": "commandRuler",
		"measure": "commandRuler",
       	"roll": "commandRoll"
	}
	
	@world_list
	def commandRuler(self, parts, byuser, overriderank):
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

        def commandRoll(self, parts, byuser, overriderank):
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
