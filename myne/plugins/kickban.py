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

class KickBanPlugin(ProtocolPlugin):
    
    commands = {
        "ban": "commandBan",
        "banb": "commandBanBoth",
        "ipban": "commandIpban",
        "ipreason": "commandIpreason",
        "kick": "commandKick",
        "banreason": "commandReason",
        "unban": "commandUnban",
        "unipban": "commandUnipban",
        "banned": "commandBanned",
        "freeze": "commandFreeze",
        "stop": "commandFreeze",
        "unfreeze": "commandUnFreeze",
        "unstop": "commandUnFreeze",
    }

    @player_list
    @admin_only
    def commandBanned(self, user, byuser, overriderank):
        "/banned - Admin\nShows who is banned."
        done = ""
        for element in self.client.factory.banned.keys():
            done = done + " " + element
        if len(done):
            self.client.sendServerList(["Banned:"] + done.split(' '))
        else:
            self.client.sendServerList(["Banned: No one."])

    @player_list
    @mod_only
    @username_command
    def commandKick(self, user, byuser, overriderank, params=[]):
        "/kick username [reason] - Mod\nKicks the Player off the server."
        if params:
            user.sendError("Kicked: %s" % " ".join(params))
            self.client.sendServerMessage("They were just kicked.")
        else:
            user.sendError("You got Kicked.")
            self.client.sendServerMessage("They were just kicked.")
    
    @player_list
    @admin_only
    @only_username_command
    def commandBanBoth(self, username, byuser, overriderank, params=[]):
        "/banb username reason - Admin\nName and IP ban a Player from this server."
        if not params:
            self.client.sendServerMessage("Please give a reason.")
        else:
            if username in self.client.factory.usernames:
                self.commandIpban(["/banb",username] + params, byuser, overriderank)
            self.commandBan(["/banb",username] + params, byuser, overriderank)

    @player_list
    @admin_only
    @only_username_command
    def commandBan(self, username, byuser, overriderank, params=[]):
        "/ban username reason - Admin\nBans the Player from this server."
        if self.client.factory.isBanned(username):
            self.client.sendServerMessage("%s is already Banned." % username)
        else:
            if not params:
                self.client.sendServerMessage("Please give a reason.")
            else:
                self.client.factory.addBan(username, " ".join(params))
                if username in self.client.factory.usernames:
                    self.client.factory.usernames[username].sendError("You got Banned!")
                self.client.sendServerMessage("%s has been Banned." % username)
    
    @player_list
    @director_only
    @only_username_command
    def commandIpban(self, username, byuser, overriderank, params=[]):
        "/ipban username reason - Director\nBan a Player's IP from this server."
        ip = self.client.factory.usernames[username].transport.getPeer().host
        if self.client.factory.isIpBanned(ip):
            self.client.sendServerMessage("%s is already IPBanned." % ip)
        else:
            if not params:
                self.client.sendServerMessage("Please give a reason.")
            else:
                self.client.factory.addIpBan(ip, " ".join(params))
                if username in self.client.factory.usernames:
                    self.client.factory.usernames[username].sendError("You got Banned!")
                self.client.sendServerMessage("%s has been IPBanned." % ip)
    
    @player_list
    @admin_only
    @only_username_command
    def commandUnban(self, username, byuser, overriderank):
        "/unban username - Admin\nRemoves the Ban on the Player."
        if not self.client.factory.isBanned(username):
            self.client.sendServerMessage("%s is not Banned." % username)
        else:
            self.client.factory.removeBan(username)
            self.client.sendServerMessage("%s was UnBanned." % username)
    
    @player_list
    @director_only
    @only_string_command("IP")
    def commandUnipban(self, ip, byuser, overriderank):
        "/unipban ip - Director\nRemoves the Ban on the IP."
        if not self.client.factory.isIpBanned(ip):
            self.client.sendServerMessage("%s is not Banned." % ip)
        else:
            self.client.factory.removeIpBan(ip)
            self.client.sendServerMessage("%s UnBanned." % ip)

    @player_list
    @admin_only    
    @only_username_command
    def commandReason(self, username, byuser, overriderank):
        "/banreason username - Admin\nGives the reason a Player was Banned."
        if not self.client.factory.isBanned(username):
            self.client.sendServerMessage("%s is not Banned." % username)
        else:
            self.client.sendServerMessage("Reason: %s" % self.client.factory.banReason(username))
    
    @player_list
    @director_only
    @only_string_command("IP")
    def commandIpreason(self, ip, byuser, overriderank):
        "/ipreason username - Director\nGives the reason an IP was Banned."
        if not self.client.factory.isIpBanned(ip):
            self.client.sendServerMessage("%s is not Banned." % ip)
        else:
            self.client.sendServerMessage("Reason: %s" % self.client.factory.ipBanReason(ip))
    
    @mod_only
    def commandUnFreeze(self, parts, byuser, overriderank):
        "/unfreeze payername - Mod\nAliases: unstop\nUnfreezes the player, allowing them to move again."
        try:
            username = parts[1]
        except:
            self.client.sendServerMessage("No player name given.")
            return
        try:
            user = self.client.factory.usernames[username]
        except:
            self.client.sendServerMessage("Player is not online.")
            return
        user.frozen = False
        user.sendNormalMessage("&4You have been unfrozen by %s!" % self.client.username)

    @mod_only
    def commandFreeze(self, parts, byuser, overriderank):
        "/freeze payername - Mod\nAliases: stop\nFreezes the player, preventing them from moving."
        try:
            username = parts[1]
        except:
            self.client.sendServerMessage("No player name given.")
            return
        try:
            user = self.client.factory.usernames[username]
        except:
            self.client.sendServerMessage("Player is not online.")
            return
        user.frozen = True
        user.sendNormalMessage("&4You have been frozen by %s!" % self.client.username)
