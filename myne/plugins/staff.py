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
from myne.globals import *
class ModsPlugin(ProtocolPlugin):
    
    commands = {
        "staff": "commandStaff",
        "members": "commandMembers",
        "directors": "commandDirectors",
        "admins": "commandAdmins",
        "mods": "commandMods",
    }

    @info_list
    def commandStaff(self, parts, byuser, overriderank):
        self.client.sendServerList(["The Server Staff"])
        list = Staff(self)
        for each in list:
            self.client.sendServerList(each)

    @info_list
    def commandMembers(self, parts, byuser, overriderank):
        if len(self.client.factory.members):
            self.client.sendServerList(["Members:"] + list(self.client.factory.members))

    @info_list
    def commandDirectors(self, parts, byuser, overriderank):
        if len(self.client.factory.directors):
            self.client.sendServerList(["Directors:"] + list(self.client.factory.directors))

    @info_list
    def commandAdmins(self, parts, byuser, overriderank):
        if len(self.client.factory.admins):
            self.client.sendServerList(["Admins:"] + list(self.client.factory.admins))

    @info_list
    def commandMods(self, parts, byuser, overriderank):
        if len(self.client.factory.mods):
            self.client.sendServerList(["Mods:"] + list(self.client.factory.mods))
