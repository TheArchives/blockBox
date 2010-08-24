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

import cPickle #Now using the MUCH faster, optimized cPickle
import logging
import time
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class PlayersPlugin(ProtocolPlugin):
    
    commands = {
        "who": "commandWho",
        "players": "commandWho",
        "pinfo": "commandWho",
        "locate": "commandLocate",
        "find": "commandLocate",
        "lastseen": "commandLastseen",
    }

    @only_username_command
    def commandLastseen(self, username, byuser, overriderank):
        "/lastseen username - Guest\nTells you when 'username' was last seen."
        if username not in self.client.factory.lastseen:
            self.client.sendServerMessage("There are no records of %s." % username)
        else:
            t = time.time() - self.client.factory.lastseen[username]
            days = t // 86400
            hours = (t % 86400) // 3600
            mins = (t % 3600) // 60
            desc = "%id, %ih, %im" % (days, hours, mins)
            self.client.sendServerMessage("%s was last seen %s ago." % (username, desc))

    @username_command
    def commandLocate(self, user, byuser, overriderank):
        "/locate username - Guest\nAliases: find\nTells you what world a user is in."
        self.client.sendServerMessage("%s is in %s" % (user.username, user.world.id))

    @player_list
    def commandWho(self, parts, byuser, overriderank):
        "/who [username] - Guest\nAliases: players, pinfo\nOnline players, or player lookup."
        if len(parts) < 2:
            self.client.sendServerMessage("Do '/who username' for more info.")
            self.client.sendServerList(["Players:"] + list(self.client.factory.usernames))
        else:
            def loadBank():
                file = open('balances.dat', 'r')
                bank_dic = cPickle.load(file)
                file.close()
                return bank_dic
            bank = loadBank()
            user = parts[1].lower()
            if parts[1].lower() in self.client.factory.usernames:
                #Parts is an array, always, so we get the first item.
                username = self.client.factory.usernames[parts[1].lower()]
                if username.isOwner():
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKGREEN+"Owner")
                elif username.isDirector():
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREEN+"Director")
                elif username.isAdmin():
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_RED+"Admin")
                elif username.isMod():
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLUE+"Mod")
                elif username.isWorldOwner():
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKPURPLE+"World Owner")
                elif username.isOp():
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKCYAN+"Operator")
                elif username.isMember():
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREY+"Member")
                elif username.isWriter():
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_CYAN+"Builder")
                elif username.isSpectator():
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLACK+"Spec")
                else:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_WHITE+"Player")
                if self.client.isAdmin():
                    self.client.sendServerMessage("IP: "+str(username.transport.getPeer().host))
                if username.gone == 1:
                    self.client.sendServerMessage("Status: "+COLOUR_DARKPURPLE+"Away")
                elif username.gone == 0:
                    self.client.sendServerMessage("Status: "+COLOUR_DARKGREEN+"Online")
                else:
                    self.client.sendServerMessage("Status: "+COLOUR_DARKGREEN+"Online")
                self.client.sendServerMessage("World: %s" % (username.world.id))
                if user in bank:
                    self.client.sendServerMessage("Balance: M%d." %(bank[user]))
                else:
                    self.client.sendServerMessage("Balance: N/A")
            else:
                #Parts is an array, always, so we get the first item.
                username = parts[1].lower()
                if username in self.client.factory.spectators:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLACK+"Spec")
                elif username in self.client.factory.owner:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKGREEN+"Owner")
                elif username in self.client.factory.directors:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREEN+"Director")
                elif username in self.client.factory.admins:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_RED+"Admin")
                elif username in self.client.factory.mods:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_BLUE+"Mod")
                elif username in self.client.world.owner:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKPURPLE+"World Owner")
                elif username in self.client.world.ops:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_DARKCYAN+"Operator")
                elif username in self.client.factory.members:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_GREY+"Member")
                elif username in self.client.world.writers:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_CYAN+"Builder")
                else:
                    self.client.sendServerMessage(parts[1]+" - "+COLOUR_WHITE+"Guest")
                self.client.sendServerMessage("Status: "+COLOUR_DARKRED+"Offline")
                if username not in self.client.factory.lastseen:
                    self.client.sendServerMessage("Last Seen: N/A")
                else:
                    t = time.time() - self.client.factory.lastseen[username]
                    days = t // 86400
                    hours = (t % 86400) // 3600
                    mins = (t % 3600) // 60
                    desc = "%id, %ih, %im" % (days, hours, mins)
                    self.client.sendServerMessage("Last Seen: %s ago." % (desc))
                    #self.commandLastseen(parts, byuser, overriderank)
                if user in bank:
                    self.client.sendServerMessage("Balance: C%d." %(bank[user]))
                else:
                    self.client.sendServerMessage("Balance: N/A")
