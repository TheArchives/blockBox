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
from myne.globals import *

class helpPlugin(ProtocolPlugin):

    commands = {
        "help": "commandHelp",
        "cmdlist": "commandCmdlist",
        "commands": "commandCmdlist",
        "about": "commandAbout",
        "credits": "commandCredits",
    }

    @info_list
    def commandHelp(self, parts, byuser, overriderank):
        if len(parts) > 1:
            try:
                func = self.client.commands[parts[1].lower()]
            except KeyError:
                if parts[1].lower() == "basics":
                    self.client.sendServerMessage("The Basics")
                    self.client.sendServerMessage("/worlds - Lists all worlds.")
                    self.client.sendServerMessage("/l worldname - Takes you to another world.")
                    self.client.sendServerMessage("/tp username - This takes you to someone else.")
                    self.client.sendServerMessage("Step through portals to teleport around.")
                elif parts[1].lower() == "chat":
                    self.client.sendServerMessage("The Chats")
                    if self.client.isMod():
                        self.client.sendServerMessage("@Whispers")    
                        self.client.sendServerMessage("!World")
                        self.client.sendServerMessage("#Staff")
                    else:
                        self.client.sendServerMessage("@Whispers")    
                        self.client.sendServerMessage("!World")
                elif parts[1].lower() == "physic":
                    self.client.sendServerMessage("The Physic Engine")
                    self.client.sendServerMessage("Turn physics on to use Physics (max of 5 worlds)")
                    self.client.sendServerMessage("If fwater is on then your water won't move.")
                    self.client.sendServerMessage("Orange blocks make Lavafalls, darkblue blocks make Waterfalls.")
                    self.client.sendServerMessage("Spouts need fwater to be on in order to work.")
                    self.client.sendServerMessage("Sand will fall, grass will grow, sponges will absorb.")
                    self.client.sendServerMessage("Use unflood to move all water, lava, and spouts from the map.")
                elif parts[1].lower() == "ranks":
                    if self.client.isOwner():
                        self.client.sendServerMessage("The Server Ranks - Owner")
                    elif self.client.isDirector():
                        self.client.sendServerMessage("The Server Ranks - Director")
                    elif self.client.isAdmin():
                        self.client.sendServerMessage("The Server Ranks - Admin")
                    elif self.client.isMod():
                        self.client.sendServerMessage("The Server Ranks - Mod")
                    elif self.client.isWorldOwner():
                        self.client.sendServerMessage("The Server Ranks - World Owner")
                    elif self.client.isOp():
                        self.client.sendServerMessage("The Server Ranks - Operator")
                    elif self.client.isMember():
                        self.client.sendServerMessage("The Server Ranks - Member")
                    elif self.client.isWriter():
                        self.client.sendServerMessage("The Server Ranks - Builder")
                    elif self.client.isSpectator():
                        self.client.sendServerMessage("The Server Ranks - Spec")
                    else:
                        self.client.sendServerMessage("The Server Ranks - Guest")
                    self.client.sendServerMessage("* "+COLOUR_DARKGREEN+"Owner "+COLOUR_GREEN+"Director "+COLOUR_RED+"Admin "+COLOUR_BLUE+"Mod "+COLOUR_PURPLE+"IRC")
                    self.client.sendServerMessage("* "+COLOUR_DARKPURPLE+"World Owner "+COLOUR_DARKCYAN+"Op "+COLOUR_GREY+"Member "+COLOUR_CYAN+"Builder "+COLOUR_WHITE+"Guest "+COLOUR_BLACK+"Spec")
                else:
                    self.client.sendServerMessage("Unknown command '%s'" % parts[1])
            else:
                if func.__doc__:
                    for line in func.__doc__.split("\n"):
                        self.client.sendServerMessage(line)
                else:
                    self.client.sendServerMessage("There's no help for that command.")
        else:
            self.client.sendServerMessage("Help Center")
            self.client.sendServerMessage("Documents: /help [basics|chat|ranks|physic]")
            self.client.sendServerMessage("Commands: /cmdlist - Lookup: /help command")
            self.client.sendServerMessage("About: /about")
            self.client.sendServerMessage("Credits: /credits")

    @info_list
    def commandCmdlist(self, parts, byuser, overriderank):
        if len(parts) > 1:
            if parts[1].lower() == "all":
                self.ListCommands("all")
            elif parts[1].lower() == "build":
                self.ListCommands("build")
            elif parts[1].lower() == "world":
                self.ListCommands("world")
            elif parts[1].lower() == "player":
                self.ListCommands("player")
            elif parts[1].lower() == "info":
                self.ListCommands("info")
            elif parts[1].lower() == "other":
                self.ListCommands("other")
            else:
                self.client.sendServerMessage("Unknown cmdlist '%s'" % parts[1])
        else:
            self.client.sendServerMessage("The Command List")
            self.client.sendServerMessage("All: /cmdlist all")
            self.client.sendServerMessage("Build: /cmdlist build")
            self.client.sendServerMessage("World: /cmdlist world")
            self.client.sendServerMessage("Player: /cmdlist player")
            self.client.sendServerMessage("Info: /cmdlist info")
            self.client.sendServerMessage("Other: /cmdlist other")

    def ListCommands(self,list):
        self.client.sendServerMessage("%s Commands:"%list.title())
        commands = []
        for name, command in self.client.commands.items():
            if not list == "other":
                if not list == "all":
                    if not getattr(command, "%s_list"%list, False):
                        continue
                if getattr(command, "owner_only", False) and not self.client.isOwner():
                    continue
                if getattr(command, "director_only", False) and not self.client.isDirector():
                    continue
                if getattr(command, "admin_only", False) and not self.client.isAdmin():
                    continue
                if getattr(command, "mod_only", False) and not self.client.isMod():
                    continue
                if getattr(command, "worldowner_only", False) and not self.client.isWorldOwner():
                    continue
                if getattr(command, "op_only", False) and not self.client.isOp():
                    continue
                if getattr(command, "member_only", False) and not self.client.isMember():
                    continue
                if getattr(command, "writer_only", False) and not self.client.isWriter():
                    continue
            else:
                if getattr(command, "plugin_list", False):
                    continue
                if getattr(command, "info_list", False):
                    continue
                if getattr(command, "build_list", False):
                    continue
                if getattr(command, "player_list", False):
                    continue
                if getattr(command, "world_list", False):
                    continue
                if getattr(command, "owner_only", False) and not self.client.isOwner():
                    continue
                if getattr(command, "director_only", False) and not self.client.isDirector():
                    continue
                if getattr(command, "admin_only", False) and not self.client.isAdmin():
                    continue
                if getattr(command, "mod_only", False) and not self.client.isMod():
                    continue
                if getattr(command, "worldowner_only", False) and not self.client.isWorldOwner():
                    continue
                if getattr(command, "op_only", False) and not self.client.isOp():
                    continue
                if getattr(command, "member_only", False) and not self.client.isMember():
                    continue
                if getattr(command, "writer_only", False) and not self.client.isWriter():
                    continue
            commands.append(name)
        if commands:
            self.client.sendServerList(sorted(commands))

    @info_list
    def commandAbout(self, parts, byuser, overriderank):
        self.client.sendServerMessage("About The Server - iCraft %s http://hlmc.net/" % VERSION)
        self.client.sendServerMessage("Name: "+self.client.factory.server_name)
        self.client.sendServerMessage("URL: "+self.client.factory.info_url)
        self.client.sendServerMessage("Owner: "+self.client.factory.owner)
        if self.client.factory.config.getboolean("irc", "use_irc"):
            self.client.sendServerMessage("IRC: "+self.client.factory.config.get("irc", "server")+" "+self.client.factory.irc_channel)

    @info_list
    def commandCredits(self, parts, byuser, overriderank):
        self.client.sendServerMessage("Credits")
        list = Credits(self)
        for each in list:
            self.client.sendSplitServerMessage(each)
