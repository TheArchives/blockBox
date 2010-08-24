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
from myne.constants import *

class MutePlugin(ProtocolPlugin):
    
    commands = {
        "mute": "commandMute",
        "unmute": "commandUnmute",
        "muted": "commandMuted",
        "silence": "commandSilence",
        "desilence": "commandDesilence",
    }
    
    hooks = {
        "recvmessage": "messageReceived",
    }
    
    def gotClient(self):
        self.muted = set()
    
    def messageReceived(self, colour, username, text, action):
        "Stop viewing a message if we've muted them."
        if username.lower() in self.muted:
            return False
    
    @player_list
    @only_username_command
    def commandMute(self, username, byuser, overriderank):
        "/mute username - Guest\nStops you hearing messages from 'username'."
        self.muted.add(username)
        self.client.sendServerMessage("%s muted." % username)
    
    @player_list
    @only_username_command
    def commandUnmute(self, username, byuser, overriderank):
        "/unmute username - Guest\nLets you hear messages from this player again"
        if username in self.muted:
            self.muted.remove(username)
            self.client.sendServerMessage("%s unmuted." % username)
        else:
            self.client.sendServerMessage("%s wasn't muted to start with" % username)
    
    @player_list
    def commandMuted(self, username, byuser, overriderank):
        "/muted - Guest\nLists people you have muted."
        if self.muted:
            self.client.sendServerList(["Muted:"] + list(self.muted))
        else:
            self.client.sendServerMessage("You haven't muted anyone.")
    
    @player_list
    @mod_only
    @only_username_command
    def commandSilence(self, username, byuser, overriderank):
        "/silence username - Mod\nDisallows the Player to talk."
        if self.client.factory.usernames[username].isMod():
            self.client.sendServerMessage("You cannot silence staff!")
            return
        self.client.factory.silenced.add(username)
        self.client.sendServerMessage("%s is now Silenced." % username)

    @player_list
    @mod_only
    @only_username_command
    def commandDesilence(self, username, byuser, overriderank):
        "/desilence username - Mod\nAllows the Player to talk."
        self.client.factory.silenced.remove(username)
        self.client.sendServerMessage("%s is no longer Silenced." % username.lower())
