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

class PhysicsControlPlugin(ProtocolPlugin):
    
    commands = {
        "physics": "commandPhysics",
        #"physflush": "commandPhysflush",
        "unflood": "commandUnflood",
        "fwater": "commandFwater",
        "asd":"commandASD",
    }
    
    @world_list
    @op_only
    def commandUnflood(self, parts, byuser, overriderank):
        "/unflood worldname - Op\nSlowly removes all water and lava from the map."
        self.client.world.start_unflooding()
        self.client.sendWorldMessage("Unflooding has been initiated.")
    
    @world_list
    @admin_only
    @on_off_command
    def commandPhysics(self, onoff, byuser, overriderank):
        "/physics on|off - Admin\nEnables or disables physics in this world."
        if onoff == "on":
            if self.client.world.physics:
                self.client.sendWorldMessage("Physics is already on here.")
            else:
                if self.client.factory.numberWithPhysics() >= self.client.factory.physics_limit:
                    self.client.sendWorldMessage("There are already %s worlds with physics on (the max)." % self.client.factory.physics_limit)
                else:
                    self.client.world.physics = True
                    self.client.sendWorldMessage("This world now has physics enabled.")
        else:
            if not self.client.world.physics:
                self.client.sendWorldMessage("Physics is already off here.")
            else:
                self.client.world.physics = False
                self.client.sendWorldMessage("This world now has physics disabled.")
    
    @world_list
    @op_only
    @on_off_command
    def commandFwater(self, onoff, byuser, overriderank):
        "/fwater on|off - Op\nEnables or disables finite water in this world."
        if onoff == "on":
            self.client.world.finite_water = True
            self.client.sendWorldMessage("This world now has finite water enabled.")
        else:
            self.client.world.finite_water = False
            self.client.sendWorldMessage("This world now has finite water disabled.")
    
    @world_list
    @admin_only
    @on_off_command
    def commandASD(self, onoff, byuser, overriderank):
        "/asd on|off - Admin\nEnables or disables whether the world shuts down if no one is on it."
        if onoff == "on":
            self.client.world.autoshutdown = True
            self.client.sendWorldMessage("This world now automaticaly shuts down.")
        else:
            self.client.world.autoshutdown = False
            self.client.sendWorldMessage("This world now shuts down manualy.")

    # Needs updating for new physics engine separation
    #@admin_only
    #def commandPhysflush(self,):
    #    "/physflush - Tells the physics engine to rescan the world."
    #    self.client.world.physics_engine.was_physics = False
    #    self.sendServerMessage("Physics flush running.")
