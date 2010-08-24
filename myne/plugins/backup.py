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

import os
import shutil
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class BackupPlugin(ProtocolPlugin):

    commands = {
    "backup": "commandBackup",
    "restore": "commandRestore",
    }

    @world_list
    @op_only
    def commandBackup(self, parts, byuser, overriderank):
        "/backup worldname - Op\nMakes a backup copy of the map of the map."
        if len(parts) == 1:
            parts.append(self.client.world.basename.lstrip("worlds"))
        world_id = parts[1]
        world_dir = ("worlds/%s/" % world_id)
        if not os.path.exists(world_dir):
           self.client.sendServerMessage("World %s does not exist." % (world_id))
        else:
            if not os.path.exists(world_dir+"backup/"):
                os.mkdir(world_dir+"backup/")
            folders = os.listdir(world_dir+"backup/")
            backups = list([])
            for x in folders:
                if x.isdigit():
                    backups.append(x)
            backups.sort(lambda x, y: int(x) - int(y))
            path = os.path.join(world_dir+"backup/", "0")
            if backups:
                path = os.path.join(world_dir+"backup/", str(int(backups[-1])+1))
            os.mkdir(path)
            shutil.copy(world_dir + "blocks.gz", path)
            try:
                self.client.sendServerMessage("Backup %s saved." % str(int(backups[-1])+1))
            except:
                self.client.sendServerMessage("Backup 0 saved.")

    @world_list
    @op_only
    def commandRestore(self, parts, byuser, overriderank):
        "/restore worldname number - Op\nRestore map to indicated number."
        
        if len(parts) < 2:
            self.client.sendServerMessage("Please specify at least a world ID!")
        else:
            world_id = parts[1].lower()
            world_dir = ("worlds/%s/" % world_id)
            if len(parts) < 3:
                backups = os.listdir(world_dir+"backup/")
                backups.sort(lambda x, y: int(x) - int(y))
                backup_number = str(int(backups[-1]))
            else:
                backup_number = parts[2]
            if not os.path.exists(world_dir+"backup/%s/" %backup_number):
                self.client.sendServerMessage("Backup %s does not exist." %backup_number)
            else:
                old_clients = self.client.factory.worlds[world_id].clients                    
                if not os.path.exists(world_dir+"blocks.gz.new"):
                    shutil.copy( world_dir+"backup/%s/blocks.gz" %backup_number,world_dir)
                else:
                    reactor.callLater(1, self.commandRestore(self, parts, byuser, overriderank))
                self.client.factory.loadWorld("worlds/%s" % world_id, world_id)
                self.client.sendServerMessage("%s has been restored to %s and booted." %(world_id,backup_number))
                self.client.factory.worlds[world_id].clients = old_clients
                for client in self.client.factory.worlds[world_id].clients:
                    client.changeToWorld(world_id)
