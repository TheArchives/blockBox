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

class CorePlugin(ProtocolPlugin):
    
    commands = {
        "pll": "commandPluginload",
        "plu": "commandPluginunload",
        "plr": "commandPluginreload",
    }
    
    @admin_only
    @only_string_command("plugin name")
    def commandPluginreload(self, plugin_name, byuser, overriderank):
        try:
            self.client.factory.unloadPlugin(plugin_name)
            self.client.factory.loadPlugin(plugin_name)
        except IOError:
            self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
        else:
            self.client.sendServerMessage("Plugin '%s' reloaded." % plugin_name)
    
    @director_only
    @only_string_command("plugin name")
    def commandPluginload(self, plugin_name, byuser, overriderank):
        try:
            self.client.factory.loadPlugin(plugin_name)
        except IOError:
            self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
        else:
            self.client.sendServerMessage("Plugin '%s' loaded." % plugin_name)
    
    @director_only
    @only_string_command("plugin name")
    def commandPluginunload(self, plugin_name, byuser, overriderank):
        try:
            self.client.factory.unloadPlugin(plugin_name)
        except IOError:
            self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
        else:
            self.client.sendServerMessage("Plugin '%s' unloaded." % plugin_name)
