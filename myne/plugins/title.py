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

from myne.plugins import ProtocolPlugin
from myne.decorators import *
import cPickle #Now using the MUCH faster, optimized cPickle
class TitlePlugin(ProtocolPlugin):
    
    commands = {
        "title":     "commandSetTitle",
    }
    
    #System methods, not for commands
    def loadRank(self):
        file = open('ranks.dat', 'r')
        rank_dic = cPickle.load(file)
        file.close()
        return rank_dic
    
    def dumpRank(self, bank_dic):
        file = open('ranks.dat', 'w')
        cPickle.dump(bank_dic, file)
        file.close()
    
    @player_list
    @director_only
    def commandSetTitle(self, parts, byuser, overriderank):
        "/title username [title] - Director\nGives or removes a title to username."
        if len(parts)==3:
            rank = self.loadRank()
            user = parts[1]
            if len(parts[2])<6:
                rank[user] = parts[2]
                self.dumpRank(rank)
                self.client.sendServerMessage("Added title.")
            else:
                self.client.sendServerMessage("A title must be 5 character or less")
        elif len(parts)==2:
            rank = self.loadRank()
            user = parts[1]
            if user not in rank:
                self.client.sendServerMessage("Syntax: /title username title")
                return False
            else:
                rank.pop(user)
                self.dumpRank(rank)
                self.client.sendServerMessage("Removed title.")
        elif len(parts)>3:
            self.client.sendServerMessage("You may only set one word as a title.")
