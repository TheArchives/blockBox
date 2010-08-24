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

import traceback
import logging
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *
from twisted.internet import reactor
from random import randint

explosionblocklist = [(-4, -1, -1), (-4, -1, 0), (-4, -1, 1), (-4, 0, -1), (-4, 0, 0), (-4, 0, 1), (-4, 1, -1), (-4, 1, 0), (-4, 1, 1), (-3, -3, 0), (-3, -2, -2), (-3, -2, -1), (-3, -2, 0), (-3, -2, 1), (-3, -2, 2), (-3, -1, -2), (-3, -1, -1), (-3, -1, 0), (-3, -1, 1), (-3, -1, 2), (-3, 0, -3), (-3, 0, -2), (-3, 0, -1), (-3, 0, 0), (-3, 0, 1), (-3, 0, 2), (-3, 0, 3), (-3, 1, -2), (-3, 1, -1), (-3, 1, 0), (-3, 1, 1), (-3, 1, 2), (-3, 2, -2), (-3, 2, -1), (-3, 2, 0), (-3, 2, 1), (-3, 2, 2), (-3, 3, 0), (-2, -3, -2), (-2, -3, -1), (-2, -3, 0), (-2, -3, 1), (-2, -3, 2), (-2, -2, -3), (-2, -2, -2), (-2, -2, -1), (-2, -2, 0), (-2, -2, 1), (-2, -2, 2), (-2, -2, 3), (-2, -1, -3), (-2, -1, -2), (-2, -1, -1), (-2, -1, 0), (-2, -1, 1), (-2, -1, 2), (-2, -1, 3), (-2, 0, -3), (-2, 0, -2), (-2, 0, -1), (-2, 0, 0), (-2, 0, 1), (-2, 0, 2), (-2, 0, 3), (-2, 1, -3), (-2, 1, -2), (-2, 1, -1), (-2, 1, 0), (-2, 1, 1), (-2, 1, 2), (-2, 1, 3), (-2, 2, -3), (-2, 2, -2), (-2, 2, -1), (-2, 2, 0), (-2, 2, 1), (-2, 2, 2), (-2, 2, 3), (-2, 3, -2), (-2, 3, -1), (-2, 3, 0), (-2, 3, 1), (-2, 3, 2), (-1, -4, -1), (-1, -4, 0), (-1, -4, 1), (-1, -3, -2), (-1, -3, -1), (-1, -3, 0), (-1, -3, 1), (-1, -3, 2), (-1, -2, -3), (-1, -2, -2), (-1, -2, -1), (-1, -2, 0), (-1, -2, 1), (-1, -2, 2), (-1, -2, 3), (-1, -1, -4), (-1, -1, -3), (-1, -1, -2), (-1, -1, -1), (-1, -1, 0), (-1, -1, 1), (-1, -1, 2), (-1, -1, 3), (-1, -1, 4), (-1, 0, -4), (-1, 0, -3), (-1, 0, -2), (-1, 0, -1), (-1, 0, 0), (-1, 0, 1), (-1, 0, 2), (-1, 0, 3), (-1, 0, 4), (-1, 1, -4), (-1, 1, -3), (-1, 1, -2), (-1, 1, -1), (-1, 1, 0), (-1, 1, 1), (-1, 1, 2), (-1, 1, 3), (-1, 1, 4), (-1, 2, -3), (-1, 2, -2), (-1, 2, -1), (-1, 2, 0), (-1, 2, 1), (-1, 2, 2), (-1, 2, 3), (-1, 3, -2), (-1, 3, -1), (-1, 3, 0), (-1, 3, 1), (-1, 3, 2), (-1, 4, -1), (-1, 4, 0), (-1, 4, 1), (0, -4, -1), (0, -4, 0), (0, -4, 1), (0, -3, -3), (0, -3, -2), (0, -3, -1), (0, -3, 0), (0, -3, 1), (0, -3, 2), (0, -3, 3), (0, -2, -3), (0, -2, -2), (0, -2, -1), (0, -2, 0), (0, -2, 1), (0, -2, 2), (0, -2, 3), (0, -1, -4), (0, -1, -3), (0, -1, -2), (0, -1, -1), (0, -1, 0), (0, -1, 1), (0, -1, 2), (0, -1, 3), (0, -1, 4), (0, 0, -4), (0, 0, -3), (0, 0, -2), (0, 0, -1), (0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (0, 1, -4), (0, 1, -3), (0, 1, -2), (0, 1, -1), (0, 1, 0), (0, 1, 1), (0, 1, 2), (0, 1, 3), (0, 1, 4), (0, 2, -3), (0, 2, -2), (0, 2, -1), (0, 2, 0), (0, 2, 1), (0, 2, 2), (0, 2, 3), (0, 3, -3), (0, 3, -2), (0, 3, -1), (0, 3, 0), (0, 3, 1), (0, 3, 2), (0, 3, 3), (0, 4, -1), (0, 4, 0), (0, 4, 1), (1, -4, -1), (1, -4, 0), (1, -4, 1), (1, -3, -2), (1, -3, -1), (1, -3, 0), (1, -3, 1), (1, -3, 2), (1, -2, -3), (1, -2, -2), (1, -2, -1), (1, -2, 0), (1, -2, 1), (1, -2, 2), (1, -2, 3), (1, -1, -4), (1, -1, -3), (1, -1, -2), (1, -1, -1), (1, -1, 0), (1, -1, 1), (1, -1, 2), (1, -1, 3), (1, -1, 4), (1, 0, -4), (1, 0, -3), (1, 0, -2), (1, 0, -1), (1, 0, 0), (1, 0, 1), (1, 0, 2), (1, 0, 3), (1, 0, 4), (1, 1, -4), (1, 1, -3), (1, 1, -2), (1, 1, -1), (1, 1, 0), (1, 1, 1), (1, 1, 2), (1, 1, 3), (1, 1, 4), (1, 2, -3), (1, 2, -2), (1, 2, -1), (1, 2, 0), (1, 2, 1), (1, 2, 2), (1, 2, 3), (1, 3, -2), (1, 3, -1), (1, 3, 0), (1, 3, 1), (1, 3, 2), (1, 4, -1), (1, 4, 0), (1, 4, 1), (2, -3, -2), (2, -3, -1), (2, -3, 0), (2, -3, 1), (2, -3, 2), (2, -2, -3), (2, -2, -2), (2, -2, -1), (2, -2, 0), (2, -2, 1), (2, -2, 2), (2, -2, 3), (2, -1, -3), (2, -1, -2), (2, -1, -1), (2, -1, 0), (2, -1, 1), (2, -1, 2), (2, -1, 3), (2, 0, -3), (2, 0, -2), (2, 0, -1), (2, 0, 0), (2, 0, 1), (2, 0, 2), (2, 0, 3), (2, 1, -3), (2, 1, -2), (2, 1, -1), (2, 1, 0), (2, 1, 1), (2, 1, 2), (2, 1, 3), (2, 2, -3), (2, 2, -2), (2, 2, -1), (2, 2, 0), (2, 2, 1), (2, 2, 2), (2, 2, 3), (2, 3, -2), (2, 3, -1), (2, 3, 0), (2, 3, 1), (2, 3, 2), (3, -3, 0), (3, -2, -2), (3, -2, -1), (3, -2, 0), (3, -2, 1), (3, -2, 2), (3, -1, -2), (3, -1, -1), (3, -1, 0), (3, -1, 1), (3, -1, 2), (3, 0, -3), (3, 0, -2), (3, 0, -1), (3, 0, 0), (3, 0, 1), (3, 0, 2), (3, 0, 3), (3, 1, -2), (3, 1, -1), (3, 1, 0), (3, 1, 1), (3, 1, 2), (3, 2, -2), (3, 2, -1), (3, 2, 0), (3, 2, 1), (3, 2, 2), (3, 3, 0), (4, -1, -1), (4, -1, 0), (4, -1, 1), (4, 0, -1), (4, 0, 0), (4, 0, 1), (4, 1, -1), (4, 1, 0), (4, 1, 1)]
maxentitiystepsatonetime = 20

class EntityPlugin(ProtocolPlugin):
    
    commands = {
        "mob": "commandEntity",
        "mobclear": "commandEntityclear",
        "nummobs": "commandNumentities",
        "mobs": "commandEntities",
        "entity": "commandEntity",
        "entityclear": "commandEntityclear",
        "numentities": "commandNumentities",
        "entities": "commandEntities",
    }

    hooks = {
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
    }

    def gotClient(self):
        self.var_entityselected = "None"

    def newWorld(self, world):
        "Hook to reset materialmaking in new worlds."
        self.var_entityselected = "None"

    def blockChanged(self, x, y, z, block, selected_block, byuser):
        "Hook trigger for block changes."
        world = self.client.world
        try:
            entitylist = world.var_entities_entitylist
        except:
            return
        dellist = []
        for index in range(len(entitylist)):
            entity = entitylist[index]
            identity = entity[0]
            i,j,k = entity[1]
            if (i,j,k) == (x,y,z) or ((identity == "creeper" or identity == "zombie" or identity == "fastzombie" or identity == "human") and (i,j+1,k) == (x,y,z)):
                dellist.append(index)
            
                
        dellist.reverse()
        for index in dellist:
            del entitylist[index]
            self.client.sendServerMessage("Mob was deleted.")
        if block != 0:
            if self.var_entityselected != "None":
                #if self.var_entityselected == "mob1":
                    #entitylist.append(["mob1",(x,y,z),2,2])
                    #self.client.sendServerMessage("Mob1 was created.")
                #if self.var_entityselected == "cloud":
                    #entitylist.append(["cloud",(x,y,z),2,2])
                    #self.client.sendServerMessage("cloud was created.")
                if self.var_entityselected == "rain":
                    entitylist.append(["rain",(x,y,z),2,2])
                    self.client.sendServerMessage("rain was created.")
                elif self.var_entityselected == "bird":
                    entitylist.append(["bird",(x,y,z),8,8])
                    self.client.sendServerMessage("Bird was created.")
                elif self.var_entityselected == "blob":
                    entitylist.append(["blob",(x,y,z),8,8])
                    self.client.sendServerMessage("Blob was created.")
                #elif self.var_entityselected == "passiveblob":
                    #entitylist.append(["passiveblob",(x,y,z),8,8])
                    #self.client.sendServerMessage("PassiveBlob was created.")
                #elif self.var_entityselected == "petblob":
                    #entitylist.append(["petblob",(x,y,z),8,8,self.client])
                    #self.client.sendServerMessage("PetBlob was created.")
                elif self.var_entityselected == "pet":
                    entitylist.append(["pet",(x,y,z),8,8,self.client])
                    self.client.sendServerMessage("Pet was created.")
                elif self.var_entityselected == "trippyflower":
                    entitylist.append(["trippyflower",(x,y,z),8,8,self.client])
                    self.client.sendServerMessage("TrippyFlower was created.")
                elif self.var_entityselected == "slime":
                    entitylist.append(["slime",(x,y,z),8,8,self.client])
                    self.client.sendServerMessage("Slime was created.")
                elif self.var_entityselected == "jumpingshroom":
                    entitylist.append(["jumpingshroom",(x,y,z),8,8])
                    self.client.sendServerMessage("JumpingShroom was created.")
                elif self.var_entityselected == "trippyshroom":
                    entitylist.append(["trippyshroom",(x,y,z),4,4,True])
                    self.client.sendServerMessage("TrippyShroom created.")
                elif self.var_entityselected == "smoke":
                    entitylist.append(["smoke",(x,y,z),4,4])
                    self.client.sendServerMessage("Smoke was created.")
                elif self.var_entityselected == "zombie":
                    entitylist.append(["zombie",(x,y,z),8,8])
                    self.client.sendServerMessage("Zombie was created.")
                elif self.var_entityselected == "creeper":
                    entitylist.append(["creeper",(x,y,z),8,8])
                    self.client.sendServerMessage("Creeper was created.")
                elif self.var_entityselected == "tnt":
                    if block == 46:
                        entitylist.append(["tnt",(x,y,z),1,1,True,24,5])
                        self.client.sendServerMessage("TNT was created.")
                    else:
                        self.client.sendServerMessage("Please place TNT Blocks to create TNT Mobs.")
                elif self.var_entityselected == "fastzombie":
                    entitylist.append(["fastzombie",(x,y,z),6,6])
                    self.client.sendServerMessage("FastZombie was created.")
                elif self.var_entityselected == "human":
                    entitylist.append(["human",(x,y,z),8,8])
                    self.client.sendServerMessage("Human was created.")
                #elif self.var_entityselected == "noob":
                    #entitylist.append(["noob",(x,y,z),8,8])
                    #self.client.sendServerMessage("Noob was created.")

    def posChanged(self, x, y, z, h, p):
        username = self.client.username
        world = self.client.world
        try:
            keyuser = world.var_entities_keyuser
        except:
            world.var_entities_keyuser = username
            keyuser = username
        clients = world.clients
        worldusernamelist = []
        for client in clients:
            worldusernamelist.append(client.username)
        if not keyuser in worldusernamelist:
            keyuser = username
        if username == keyuser:
            try:
                entitylist = world.var_entities_entitylist
            except:
                return
            var_dellist = []
            var_num = len(entitylist)
            if var_num > maxentitiystepsatonetime:
                var_num = maxentitiystepsatonetime
            for index in range(var_num):
                entity = entitylist[index]
                var_type = entity[0]
                var_position = entity[1]
                var_delay = entity[2]
                var_maxdelay = entity[3]
                var_delay -= 1
                if var_delay < 0:
                    try:
                        var_delay = var_maxdelay
                        if index not in var_dellist:
                            #if var_type == "mob1":
                                #x,y,z = var_position
                                #var_cango = True
                                #try:
                                    #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x, y, z+1)])
                                    #if blocktocheck != 0:
                                        #var_cango = False
                                #except:
                                    #var_cango = False
                                #if var_cango:
                                    #block = chr(0)
                                    #try:
                                        #world[x, y, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)
                                    #var_position = (x,y,z+1)
                                    #z += 1
                                    #block = chr(11) 
                                    #try:
                                        #world[x, y, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)
                                #else:
                                    #block = chr(0)
                                    #var_dellist.append(index)
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)


                            if var_type == "bird":
                                x,y,z = var_position
                                userpositionlist = []
                                for user in clients:
                                    userpositionlist.append((user.x >> 5,user.y >> 5,user.z >> 5))
                                closestposition = (0,0)
                                closestclient = None
                                closestdistance = None
                                for var_pos in userpositionlist:
                                    i,j,k = var_pos
                                    distance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
                                    if closestdistance == None:
                                        closestdistance = distance
                                        closestposition = (var_pos[0],var_pos[2])
                                    else:
                                        if distance < closestdistance:
                                            closestdistance = distance
                                            closestposition = (var_pos[0],var_pos[2])
                                i,k = closestposition
                                distance = ((i-x)**2+(k-z)**2)**0.5
                                if distance != 0 and distance > 2:
                                    target = [int((i-x)/(distance/1.75)) + x,int((j-y)/(distance/1.75)) + y,int((k-z)/(distance/1.75)) + z]
                                    i,j,k = target
                                    var_cango = True
                                    try:
                                        blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                        if blocktocheck != 0:
                                            var_cango = False
                                    except:
                                        var_cango = False
                                    if var_cango:
                                        block = chr(0)
                                        try:
                                            world[x, y, z] = block
                                        except:
                                            return
                                        self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                        self.client.sendBlock(x, y, z, block)
                                        var_position = target
                                        x,y,z = var_position
                                        block = chr(35)
                                        try:
                                            world[x, y, z] = block
                                        except:
                                            return
                                        self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                        self.client.sendBlock(x, y, z, block)
                                    else:
                                        var_cango = True
                                        target[1] = target[1] + 1
                                        j = target[1]
                                        try:
                                            blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                            if blocktocheck != 0:
                                                var_cango = False
                                        except:
                                            var_cango = False
                                        if var_cango:
                                            block = chr(0)
                                            try:
                                                world[x, y, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            self.client.sendBlock(x, y, z, block)
                                            var_position = target
                                            x,y,z = var_position
                                            block = chr(35)
                                            try:
                                                world[x, y, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            self.client.sendBlock(x, y, z, block)

                            elif var_type == "blob":
                                x,y,z = var_position
                                var_cango = True
                                try:
                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
                                    if blocktocheck != 0:
                                        var_cango = False
                                except:
                                    var_cango = False
                                if var_cango:
                                    block = chr(0)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                    var_position = (x,y-1,z)
                                    x,y,z = var_position
                                    block = chr(11)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                else:
                                    userpositionlist = []
                                    for user in clients:
                                        userpositionlist.append((user,(user.x >> 5,user.y >> 5,user.z >> 5)))
                                    closestposition = (0,0)
                                    closestclient = None
                                    closestdistance = None
                                    for entry in userpositionlist:
                                        client = entry[0]
                                        var_pos = entry[1]
                                        i,j,k = var_pos
                                        distance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
                                        if closestdistance == None:
                                            closestdistance = distance
                                            closestclient = client
                                            closestposition = (var_pos[0],var_pos[2])
                                        else:
                                            if distance < closestdistance:
                                                closestdistance = distance
                                                closestclient = client
                                                closestposition = (var_pos[0],var_pos[2])
                                    if closestdistance < 2:
                                        sx,sy,sz,sh = world.spawn
                                        closestclient.teleportTo(sx,sy,sz,sh)
                                        self.client.sendPlainWorldMessage("%s%s has died." % (COLOUR_DARKRED, closestclient.username))
                                        
                                    if closestdistance != 0:
                                        i,k = closestposition
                                        target = [int((i-x)/(closestdistance/1.75)) + x,y,int((k-z)/(closestdistance/1.75)) + z]
                                        i,j,k = target
                                        var_cango = True
                                        try:
                                            blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                            if blocktocheck != 0:
                                                var_cango = False
                                        except:
                                            var_cango = False
                                        if var_cango:
                                            block = chr(0)
                                            try:
                                                world[x, y, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            self.client.sendBlock(x, y, z, block)
                                            var_position = target
                                            x,y,z = var_position
                                            block = chr(11)
                                            try:
                                                world[x, y, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            self.client.sendBlock(x, y, z, block)
                                        else:
                                            var_cango = True
                                            target[1] = target[1] + 1
                                            j = target[1]
                                            try:
                                                blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                if blocktocheck != 0:
                                                    var_cango = False
                                            except:
                                                var_cango = False
                                            if var_cango:
                                                block = chr(0)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                                                var_position = target
                                                x,y,z = var_position
                                                block = chr(11)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                            #elif var_type == "passiveblob":
                                #x,y,z = var_position
                                #var_cango = True
                                #try:
                                    #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
                                    #if blocktocheck != 0:
                                        #var_cango = False
                                #except:
                                    #var_cango = False
                                #if var_cango:
                                    #block = chr(0)
                                    #try:
                                        #world[x, y, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)
                                    #var_position = (x,y-1,z)
                                    #x,y,z = var_position
                                    #block = chr(9)
                                    #try:
                                        #world[x, y, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)
                                #else:
                                    #userpositionlist = []
                                    #for user in clients:
                                        #userpositionlist.append((user.x >> 5,user.y >> 5,user.z >> 5))
                                    #closestposition = (0,0)
                                    #closestclient = None
                                    #closestdistance = None
                                    #for var_pos in userpositionlist:
                                        #i,j,k = var_pos
                                        #distance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
                                        #if closestdistance == None:
                                            #closestdistance = distance
                                            #closestposition = (var_pos[0],var_pos[2])
                                        #else:
                                            #if distance < closestdistance:
                                                #closestdistance = distance
                                                #closestposition = (var_pos[0],var_pos[2])
                                    #i,k = closestposition
                                    #distance = ((i-x)**2+(k-z)**2)**0.5
                                    #if distance != 0 and distance > 3:
                                        #target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
                                        #i,j,k = target
                                        #var_cango = True
                                        #try:
                                            #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                            #if blocktocheck != 0:
                                                #var_cango = False
                                        #except:
                                            #var_cango = False
                                        #if var_cango:
                                            #block = chr(0)
                                            #try:
                                                #world[x, y, z] = block
                                            #except:
                                                #return
                                            #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            #self.client.sendBlock(x, y, z, block)
                                            #var_position = target
                                            #x,y,z = var_position
                                            #block = chr(9)
                                            #try:
                                                #world[x, y, z] = block
                                            #except:
                                                #return
                                            #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            #self.client.sendBlock(x, y, z, block)
                                        #else:
                                            #var_cango = True
                                            #target[1] = target[1] + 1
                                            #j = target[1]
                                            #try:
                                                #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                #if blocktocheck != 0:
                                                    #var_cango = False
                                            #except:
                                                #var_cango = False
                                            #if var_cango:
                                                #block = chr(0)
                                                #try:
                                                    #world[x, y, z] = block
                                                #except:
                                                    #return
                                                #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                #self.client.sendBlock(x, y, z, block)
                                                #var_position = target
                                                #x,y,z = var_position
                                                #block = chr(9)
                                                #try:
                                                    #world[x, y, z] = block
                                                #except:
                                                    #return
                                                #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                #self.client.sendBlock(x, y, z, block)

                            elif var_type == "slime":
                                x,y,z = var_position
                                var_cango = True
                                try:
                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
                                    if blocktocheck != 0:
                                        var_cango = False
                                except:
                                    var_cango = False
                                if var_cango:
                                    block = chr(0)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                    var_position = (x,y-1,z)
                                    x,y,z = var_position
                                    block = chr(24)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                else:
                                    userpositionlist = []
                                    for user in clients:
                                        userpositionlist.append((user.x >> 5,user.y >> 5,user.z >> 5))
                                    closestposition = (0,0)
                                    closestclient = None
                                    closestdistance = None
                                    for var_pos in userpositionlist:
                                        i,j,k = var_pos
                                        distance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
                                        if closestdistance == None:
                                            closestdistance = distance
                                            closestposition = (var_pos[0],var_pos[2])
                                        else:
                                            if distance < closestdistance:
                                                closestdistance = distance
                                                closestposition = (var_pos[0],var_pos[2])
                                    i,k = closestposition
                                    distance = ((i-x)**2+(k-z)**2)**0.5
                                    if distance != 0 and distance > 3:
                                        target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
                                        i,j,k = target
                                        var_cango = True
                                        try:
                                            blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                            if blocktocheck != 0:
                                                var_cango = False
                                        except:
                                            var_cango = False
                                        if var_cango:
                                            block = chr(0)
                                            try:
                                                world[x, y, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            self.client.sendBlock(x, y, z, block)
                                            var_position = target
                                            x,y,z = var_position
                                            block = chr(24)
                                            try:
                                                world[x, y, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            self.client.sendBlock(x, y, z, block)
                                        else:
                                            var_cango = True
                                            target[1] = target[1] + 1
                                            j = target[1]
                                            try:
                                                blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                if blocktocheck != 0:
                                                    var_cango = False
                                            except:
                                                var_cango = False
                                            if var_cango:
                                                block = chr(0)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                                                var_position = target
                                                x,y,z = var_position
                                                block = chr(24)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)

                            #elif var_type == "petblob":
                                #x,y,z = var_position
                                #var_cango = True
                                #try:
                                    #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
                                    #if blocktocheck != 0:
                                        #var_cango = False
                                #except:
                                    #var_cango = False
                                #if var_cango:
                                    #block = chr(0)
                                    #try:
                                        #world[x, y, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)
                                    #var_position = (x,y-1,z)
                                    #x,y,z = var_position
                                    #block = chr(9)
                                    #try:
                                        #world[x, y, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)
                                #else:
                                    #ownerclient = entity[4]
                                    #ownername = ownerclient.username
                                    #if ownername in worldusernamelist:
                                        #i,j,k = (ownerclient.x >> 5,ownerclient.y >> 5,ownerclient.z >> 5)
                                        #distance = ((i-x)**2+(k-z)**2)**0.5
                                        #if distance != 0 and distance > 2:
                                            #target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
                                            #i,j,k = target
                                            #var_cango = True
                                            #try:
                                                #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                #if blocktocheck != 0:
                                                    #var_cango = False
                                            #except:
                                                #var_cango = False
                                            #if var_cango:
                                                #block = chr(0)
                                                #try:
                                                    #world[x, y, z] = block
                                                #except:
                                                    #return
                                                #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                #self.client.sendBlock(x, y, z, block)
                                                #var_position = target
                                                #x,y,z = var_position
                                                #block = chr(9)
                                                #try:
                                                    #world[x, y, z] = block
                                                #except:
                                                    #return
                                                #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                #self.client.sendBlock(x, y, z, block)
                                            #else:
                                                #var_cango = True
                                                #target[1] = target[1] + 1
                                                #j = target[1]
                                                #try:
                                                    #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                    #if blocktocheck != 0:
                                                        #var_cango = False
                                                #except:
                                                    #var_cango = False
                                                #if var_cango:
                                                    #block = chr(0)
                                                    #try:
                                                        #world[x, y, z] = block
                                                    #except:
                                                        #return
                                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                    #self.client.sendBlock(x, y, z, block)
                                                    #var_position = target
                                                    #x,y,z = var_position
                                                    #block = chr(9)
                                                    #try:
                                                        #world[x, y, z] = block
                                                    #except:
                                                        #return
                                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                    #self.client.sendBlock(x, y, z, block)

                            elif var_type == "pet":
                                x,y,z = var_position
                                var_cango = True
                                try:
                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
                                    if blocktocheck != 0:
                                        var_cango = False
                                except:
                                    var_cango = False
                                if var_cango:
                                    block = chr(0)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                    var_position = (x,y-1,z)
                                    x,y,z = var_position
                                    block = chr(49)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                else:
                                    ownerclient = entity[4]
                                    ownername = ownerclient.username
                                    if ownername in worldusernamelist:
                                        i,j,k = (ownerclient.x >> 5,ownerclient.y >> 5,ownerclient.z >> 5)
                                        distance = ((i-x)**2+(k-z)**2)**0.5
                                        if distance != 0 and distance > 2:
                                            target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
                                            i,j,k = target
                                            var_cango = True
                                            try:
                                                blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                if blocktocheck != 0:
                                                    var_cango = False
                                            except:
                                                var_cango = False
                                            if var_cango:
                                                block = chr(0)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                                                var_position = target
                                                x,y,z = var_position
                                                block = chr(49)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                                            else:
                                                var_cango = True
                                                target[1] = target[1] + 1
                                                j = target[1]
                                                try:
                                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                    if blocktocheck != 0:
                                                        var_cango = False
                                                except:
                                                    var_cango = False
                                                if var_cango:
                                                    block = chr(0)
                                                    try:
                                                        world[x, y, z] = block
                                                    except:
                                                        return
                                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                    self.client.sendBlock(x, y, z, block)
                                                    var_position = target
                                                    x,y,z = var_position
                                                    block = chr(49)
                                                    try:
                                                        world[x, y, z] = block
                                                    except:
                                                        return
                                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                    self.client.sendBlock(x, y, z, block)

                            elif var_type == "jumpingshroom":
                                x,y,z = var_position
                                var_cango = True
                                try:
                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x, y-1, z)])
                                    if blocktocheck != 0:
                                        var_cango = False
                                except:
                                    var_cango = False
                                if var_cango:
                                    block = chr(0)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                    var_position = (x,y-1,z)
                                    y -= 1
                                    block = chr(39) 
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                else:
                                    var_cango = True
                                    try:
                                        blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x, y+1, z)])
                                        if blocktocheck != 0:
                                            var_cango = False
                                    except:
                                        var_cango = False
                                    if var_cango:
                                        block = chr(0)
                                        try:
                                            world[x, y, z] = block
                                        except:
                                            return
                                        self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                        self.client.sendBlock(x, y, z, block)
                                        var_position = (x,y+1,z)
                                        y += 1
                                        block = chr(39) 
                                        try:
                                            world[x, y, z] = block
                                        except:
                                            return
                                        self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                        self.client.sendBlock(x, y, z, block)

                            elif var_type == "smoke":
                                x,y,z = var_position
                                i = randint(-1,1) + x
                                j = 1 + y
                                k = randint(-1,1) + z
                                var_cango = True
                                block = chr(0)
                                try:
                                    world[x, y, z] = block
                                except:
                                    return
                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                self.client.sendBlock(x, y, z, block)
                                try:
                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)])
                                    if blocktocheck != 0:
                                        var_cango = False
                                except:
                                    var_cango = False
                                if var_cango and randint(0,10) != 10:
                                    var_position = (i,j,k)
                                    x,y,z = var_position
                                    block = chr(36) 
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                else:
                                    var_dellist.append(index)

                            elif var_type == "trippyshroom":
                                x,y,z = var_position
                                if entity[4]:
                                    entity[4] = False
                                    block = chr(39)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                else:
                                    entity[4] = True
                                    block = chr(40)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)

                            elif var_type == "trippyflower":
                                x,y,z = var_position
                                if entity[4]:
                                    entity[4] = False
                                    block = chr(37)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                else:
                                    entity[4] = True
                                    block = chr(38)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                            
                            #elif var_type == "cloud":
                                #x,y,z = var_position
                                #i = randint(-1,1) + x
                                #j = randint(-1,1) + y
                                #k = randint(-1,1) + z
                                #var_cango = True
                                #block = chr(0)
                                #try:
                                    world[x, y, z] = block
                                #except:
                                    return
                                #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                #self.client.sendBlock(x, y, z, block)
                                #try:
                                    #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)])
                                    #if blocktocheck != 0:
                                        #var_cango = False
                                #except:
                                    #var_cango = False
                                #if var_cango and randint(0,200) != 200:
                                    #var_position = (i,j,k)
                                    #x,y,z = var_position
                                    #block = chr(36) 
                                    #try:
                                        #world[x, y, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)
                                #else:
                                    #entitylist.append(["rain",(x,y-1,z+1),4,4])
       
                            #elif var_type == "rain":
                                #x,y,z = var_position
                                #i = x
                                #j = -1 + y
                                #k = z
                                #var_cango = True
                                #block = chr(0)
                                #try:
                                    #world[x, y, z] = block
                                #except:
                                    #return
                                #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                #self.client.sendBlock(x, y, z, block)
                                #try:
                                    #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)])
                                    #if blocktocheck != 0:
                                        #var_cango = False
                                #except:
                                    #var_cango = False
                                #if var_cango and randint(0,45) != 45:
                                    #var_position = (i,j,k)
                                    #x,y,z = var_position
                                    #block = chr(9) 
                                    #try:
                                        #world[x, y, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)
                                #else:
                                    #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)])
                                    #if blocktocheck != 0:
                                        #var_cango = False
                                        #var_dellist.append(index)
                                    
                            elif var_type == "zombie" or var_type == "fastzombie":
                                x,y,z = var_position
                                var_cango = True
                                try:
                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
                                    if blocktocheck != 0:
                                        var_cango = False
                                except:
                                    var_cango = False
                                if var_cango:
                                    block = chr(0)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                    try:
                                        world[x, y+1, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                    self.client.sendBlock(x, y+1, z, block)
                                    var_position = (x,y-1,z)
                                    x,y,z = var_position
                                    block = chr(35)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                    block = chr(25)
                                    try:
                                        world[x, y+1, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                    self.client.sendBlock(x, y+1, z, block)
                                else:
                                    userpositionlist = []
                                    for user in clients:
                                        userpositionlist.append((user,(user.x >> 5,user.y >> 5,user.z >> 5)))
                                    closestposition = (0,0)
                                    closestclient = None
                                    closestdistance = None
                                    for entry in userpositionlist:
                                        client = entry[0]
                                        var_pos = entry[1]
                                        i,j,k = var_pos
                                        distance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
                                        if closestdistance == None:
                                            closestdistance = distance
                                            closestclient = client
                                            closestposition = (var_pos[0],var_pos[2])
                                        else:
                                            if distance < closestdistance:
                                                closestdistance = distance
                                                closestclient = client
                                                closestposition = (var_pos[0],var_pos[2])
                                    

                                    if closestdistance < 2:
                                        sx,sy,sz,sh = world.spawn
                                        closestclient.teleportTo(sx,sy,sz,sh)
                                        self.client.sendPlainWorldMessage("%s%s has died." % (COLOUR_DARKRED, closestclient.username))
                                        
                                    i,k = closestposition
                                    distance = ((i-x)**2+(k-z)**2)**0.5
                                    if distance != 0:
                                        target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
                                        i,j,k = target
                                        var_cango = True
                                        try:
                                            blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                            if blocktocheck != 0:
                                                var_cango = False
                                            blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j+1,k)])
                                            if blocktocheck != 0:
                                                var_cango = False
                                        except:
                                            var_cango = False
                                        if var_cango:
                                            block = chr(0)
                                            try:
                                                world[x, y, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            self.client.sendBlock(x, y, z, block)
                                            try:
                                                world[x, y+1, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                            self.client.sendBlock(x, y+1, z, block)
                                            var_position = target
                                            x,y,z = var_position
                                            block = chr(35)
                                            try:
                                                world[x, y, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            self.client.sendBlock(x, y, z, block)
                                            block = chr(25)
                                            try:
                                                world[x, y+1, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                            self.client.sendBlock(x, y+1, z, block)
                                        else:
                                            var_cango = True
                                            target[1] = target[1] + 1
                                            j = target[1]
                                            try:
                                                blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                if blocktocheck != 0:
                                                    var_cango = False
                                                blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j+1,k)])
                                                if blocktocheck != 0:
                                                    var_cango = False
                                            except:
                                                var_cango = False
                                            if var_cango:
                                                block = chr(0)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                                                try:
                                                    world[x, y+1, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                                self.client.sendBlock(x, y+1, z, block)
                                                var_position = target
                                                x,y,z = var_position
                                                block = chr(35)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                                                block = chr(25)
                                                try:
                                                    world[x, y+1, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                                self.client.sendBlock(x, y+1, z, block)
                            elif var_type == "creeper":
                                x,y,z = var_position
                                var_cango = True
                                try:
                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
                                    if blocktocheck != 0:
                                        var_cango = False
                                except:
                                    var_cango = False
                                if var_cango:
                                    block = chr(0)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                    try:
                                        world[x, y+1, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                    self.client.sendBlock(x, y+1, z, block)
                                    var_position = (x,y-1,z)
                                    x,y,z = var_position
                                    block = chr(25)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                    block = chr(24)
                                    try:
                                        world[x, y+1, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                    self.client.sendBlock(x, y+1, z, block)
                                else:
                                    userpositionlist = []
                                    for user in clients:
                                        userpositionlist.append((user.x >> 5,user.y >> 5,user.z >> 5))
                                    closestposition = (0,0)
                                    closestdistance = None
                                    for var_pos in userpositionlist:
                                        i,j,k = var_pos
                                        distance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
                                        if closestdistance == None:
                                            closestdistance = distance
                                            closestposition = (var_pos[0],var_pos[2])
                                        else:
                                            if distance < closestdistance:
                                                closestdistance = distance
                                                closestposition = (var_pos[0],var_pos[2])
                                    
                                    var_continue = True
                                    if closestdistance < 4:
                                        entitylist.append(["tnt",(x,y,z),1,1,True,0,5])
                                        var_dellist.append(index)
                                        var_continue = False
                                    if var_continue:
                                        i,k = closestposition
                                        distance = ((i-x)**2+(k-z)**2)**0.5
                                        if distance != 0:
                                            target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
                                            i,j,k = target
                                            var_cango = True
                                            try:
                                                blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                if blocktocheck != 0:
                                                    var_cango = False
                                                blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j+1,k)])
                                                if blocktocheck != 0:
                                                    var_cango = False
                                            except:
                                                var_cango = False
                                            if var_cango:
                                                block = chr(0)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                                                try:
                                                    world[x, y+1, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                                self.client.sendBlock(x, y+1, z, block)
                                                var_position = target
                                                x,y,z = var_position
                                                block = chr(25)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                                                block = chr(24)
                                                try:
                                                    world[x, y+1, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                                self.client.sendBlock(x, y+1, z, block)
                                            else:
                                                var_cango = True
                                                target[1] = target[1] + 1
                                                j = target[1]
                                                try:
                                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                    if blocktocheck != 0:
                                                        var_cango = False
                                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j+1,k)])
                                                    if blocktocheck != 0:
                                                        var_cango = False
                                                except:
                                                    var_cango = False
                                                if var_cango:
                                                    block = chr(0)
                                                    try:
                                                        world[x, y, z] = block
                                                    except:
                                                        return
                                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                    self.client.sendBlock(x, y, z, block)
                                                    try:
                                                        world[x, y+1, z] = block
                                                    except:
                                                        return
                                                    self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                                    self.client.sendBlock(x, y+1, z, block)
                                                    var_position = target
                                                    x,y,z = var_position
                                                    block = chr(25)
                                                    try:
                                                        world[x, y, z] = block
                                                    except:
                                                        return
                                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                    self.client.sendBlock(x, y, z, block)
                                                    block = chr(24)
                                                    try:
                                                        world[x, y+1, z] = block
                                                    except:
                                                        return
                                                    self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                                    self.client.sendBlock(x, y+1, z, block)
                                                    
                            elif var_type == "tnt":
                                x,y,z = var_position
                                bombintialdelay = entity[5]
                                bombfinaldelay = entity[6]
                                if bombintialdelay <= 0:
                                    if entity[4]:
                                        entity[4] = False
                                        var_userkillist = []
                                        var_userkillist2 = []
                                        for var_offsettuple in explosionblocklist:
                                            i,j,k = var_offsettuple
                                            for index in range(len(entitylist)):
                                                var_entity = entitylist[index]
                                                identity = var_entity[0]
                                                if identity != "tnt" and identity != "smoke" and identity != "creeper" and identity != "entity1":
                                                    rx,ry,rz = var_entity[1]
                                                    dx,dy,dz = (i+x,j+y,k+z)
                                                    if (rx,ry,rz) == (dx,dy,dz) or ((identity == "creeper" or identity == "zombie" or identity == "fastzombie" or identity == "human") and (rx,ry+1,rz) == (dx,dy,dz)):
                                                        var_dellist.append(index)
                                            for user in clients:
                                                tx,ty,tz = (user.x >> 5,user.y >> 5,user.z >> 5)
                                                distance = ((tx-x)**2+(ty-y)**2+(tz-z)**2)**0.5
                                                if distance < 5:
                                                    var_userkillist.append(user)
                                            unbreakables = [chr(BLOCK_SOLID), chr(BLOCK_IRON), chr(BLOCK_GOLD), chr(BLOCK_TNT)]
                                            strongblocks = [chr(BLOCK_ROCK), chr(BLOCK_STONE), chr(BLOCK_OBSIDIAN), chr(BLOCK_WATER), chr(BLOCK_STILLWATER), chr(BLOCK_LAVA), chr(BLOCK_STILLLAVA), chr(BLOCK_BRICK), chr(BLOCK_GOLDORE), chr(BLOCK_IRONORE), chr(BLOCK_COAL), chr(BLOCK_SPONGE)]
                                            ax,ay,az = (i+x,j+y,k+z)
                                            block = chr(11)
                                            try:
                                                world[ax,ay, az] = block
                                                self.client.queueTask(TASK_BLOCKSET, (ax, ay, az, block), world=world)
                                                self.client.sendBlock(ax, ay, az, block)
                                            except:
                                                pass
                                        for user in var_userkillist:
                                            if user not in var_userkillist2:
                                                var_userkillist2.append(user)
                                        for user in var_userkillist2:
                                            sx,sy,sz,sh = world.spawn
                                            user.teleportTo(sx,sy,sz,sh)
                                            self.client.sendPlainWorldMessage("%s%s has died." % (COLOUR_DAKRRED, user.username))
                                    if bombfinaldelay <=0:
                                        var_dellist.append(index)
                                        for var_offsettuple in explosionblocklist:
                                            i,j,k = var_offsettuple
                                            unbreakables = [chr(BLOCK_SOLID), chr(BLOCK_IRON), chr(BLOCK_GOLD), chr(BLOCK_TNT)]
                                            strongblocks = [chr(BLOCK_ROCK), chr(BLOCK_STONE), chr(BLOCK_OBSIDIAN), chr(BLOCK_WATER), chr(BLOCK_STILLWATER), chr(BLOCK_LAVA), chr(BLOCK_STILLLAVA), chr(BLOCK_BRICK), chr(BLOCK_GOLDORE), chr(BLOCK_IRONORE), chr(BLOCK_COAL), chr(BLOCK_SPONGE)]
                                            ax,ay,az = (i+x,j+y,k+z)
                                            block = chr(0)
                                            try:
                                                world[ax,ay, az] = block
                                                self.client.queueTask(TASK_BLOCKSET, (ax, ay, az, block), world=world)
                                                self.client.sendBlock(ax, ay, az, block)
                                            except:
                                                pass
                                        entitylist.append(["smoke",(x,y,z),4,4])
                                        entitylist.append(["smoke",(x,y+2,z),4,4])
                                        entitylist.append(["smoke",(x,y+1,z+1),4,4])
                                        entitylist.append(["smoke",(x+1,y+1,z),4,4])
                                        entitylist.append(["smoke",(x+1,y-1,z),4,4])
                                        entitylist.append(["smoke",(x,y-1,z-1),4,4])
                                        entitylist.append(["smoke",(x,y-1,z+1),4,4])
                                    else:
                                        bombfinaldelay -= 1
                                else:
                                    bombintialdelay -= 1
                                entity[5] = bombintialdelay
                                entity[6] = bombfinaldelay
                                
                            elif var_type == "human":
                                x,y,z = var_position
                                var_cango = True
                                try:
                                    blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
                                    if blocktocheck != 0:
                                        var_cango = False
                                except:
                                    var_cango = False
                                if var_cango:
                                    block = chr(0)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                    try:
                                        world[x, y+1, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                    self.client.sendBlock(x, y+1, z, block)
                                    var_position = (x,y-1,z)
                                    x,y,z = var_position
                                    block = chr(29)
                                    try:
                                        world[x, y, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    self.client.sendBlock(x, y, z, block)
                                    block = chr(12)
                                    try:
                                        world[x, y+1, z] = block
                                    except:
                                        return
                                    self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                    self.client.sendBlock(x, y+1, z, block)
                                else:
                                    userpositionlist = []
                                    for user in clients:
                                        userpositionlist.append((user.x >> 5,user.y >> 5,user.z >> 5))
                                    closestposition = (0,0)
                                    closestdistance = None
                                    for var_pos in userpositionlist:
                                        i,j,k = var_pos
                                        distance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
                                        if closestdistance == None:
                                            closestdistance = distance
                                            closestposition = (var_pos[0],var_pos[2])
                                        else:
                                            if distance < closestdistance:
                                                closestdistance = distance
                                                closestposition = (var_pos[0],var_pos[2])
                                    i,k = closestposition
                                    distance = ((i-x)**2+(k-z)**2)**0.5
                                    if distance != 0 and distance > 3:
                                        target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
                                        i,j,k = target
                                        var_cango = True
                                        try:
                                            blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                            if blocktocheck != 0:
                                                var_cango = False
                                            blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j+1,k)])
                                            if blocktocheck != 0:
                                                var_cango = False
                                        except:
                                            var_cango = False
                                        if var_cango:
                                            block = chr(0)
                                            try:
                                                world[x, y, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            self.client.sendBlock(x, y, z, block)
                                            try:
                                                world[x, y+1, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                            self.client.sendBlock(x, y+1, z, block)
                                            var_position = target
                                            x,y,z = var_position
                                            block = chr(29)
                                            try:
                                                world[x, y, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            self.client.sendBlock(x, y, z, block)
                                            block = chr(12)
                                            try:
                                                world[x, y+1, z] = block
                                            except:
                                                return
                                            self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                            self.client.sendBlock(x, y+1, z, block)
                                        else:
                                            var_cango = True
                                            target[1] = target[1] + 1
                                            j = target[1]
                                            try:
                                                blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                if blocktocheck != 0:
                                                    var_cango = False
                                                blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j+1,k)])
                                                if blocktocheck != 0:
                                                    var_cango = False
                                            except:
                                                var_cango = False
                                            if var_cango:
                                                block = chr(0)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                                                try:
                                                    world[x, y+1, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                                self.client.sendBlock(x, y+1, z, block)
                                                var_position = target
                                                x,y,z = var_position
                                                block = chr(29)
                                                try:
                                                    world[x, y, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                self.client.sendBlock(x, y, z, block)
                                                block = chr(12)
                                                try:
                                                    world[x, y+1, z] = block
                                                except:
                                                    return
                                                self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                                self.client.sendBlock(x, y+1, z, block)
                            #elif var_type == "noob":
                                #x,y,z = var_position
                                #var_cango = True
                                #try:
                                    #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
                                    #if blocktocheck != 0:
                                        #var_cango = False
                                #except:
                                    #var_cango = False
                                #if var_cango:
                                    #block = chr(0)
                                    #try:
                                        #world[x, y, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)
                                    #try:
                                        #world[x, y+1, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                    #self.client.sendBlock(x, y+1, z, block)
                                    #var_position = (x,y-1,z)
                                    #x,y,z = var_position
                                    #block = chr(29)
                                    #try:
                                        #world[x, y, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                    #self.client.sendBlock(x, y, z, block)
                                    #block = chr(12)
                                    #try:
                                        #world[x, y+1, z] = block
                                    #except:
                                        #return
                                    #self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                    #self.client.sendBlock(x, y+1, z, block)
                                #else:
                                    #userpositionlist = []
                                    #for user in clients:
                                        #userpositionlist.append((user,(user.x >> 5,user.y >> 5,user.z >> 5)))
                                    #closestposition = (0,0)
                                    #closestclient = None
                                    #closestdistance = None
                                    #for entry in userpositionlist:
                                        #client = entry[0]
                                        #var_pos = entry[1]
                                        #i,j,k = var_pos
                                        #distance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
                                        #if closestdistance == None:
                                            #closestdistance = distance
                                            #closestclient = client
                                            #closestposition = (var_pos[0],var_pos[2])
                                        #else:
                                            #if distance < closestdistance:
                                                #closestdistance = distance
                                                #closestclient = client
                                                #closestposition = (var_pos[0],var_pos[2])
                                    

                                    #if closestdistance < 3:
                                        #closestclient.sendNormalMessage("%sNoob: CAN I HAS OP PLOX?" % COLOUR_WHITE)
                                        
                                    #i,k = closestposition
                                    #distance = ((i-x)**2+(k-z)**2)**0.5
                                    #if distance != 0 and distance > 2:
                                        #target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
                                        #i,j,k = target
                                        #var_cango = True
                                        #try:
                                            #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                            #if blocktocheck != 0:
                                                #var_cango = False
                                            #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j+1,k)])
                                            #if blocktocheck != 0:
                                                #var_cango = False
                                        #except:
                                            #var_cango = False
                                        #if var_cango:
                                            #block = chr(0)
                                            #try:
                                                #world[x, y, z] = block
                                            #except:
                                                #return
                                            #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            #self.client.sendBlock(x, y, z, block)
                                            #try:
                                                #world[x, y+1, z] = block
                                            #except:
                                                #return
                                            #self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                            #self.client.sendBlock(x, y+1, z, block)
                                            #var_position = target
                                            #x,y,z = var_position
                                            #block = chr(29)
                                            #try:
                                                #world[x, y, z] = block
                                            #except:
                                                #return
                                            #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                            #self.client.sendBlock(x, y, z, block)
                                            #block = chr(12)
                                            #try:
                                                #world[x, y+1, z] = block
                                            #except:
                                                #return
                                            #self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                            #self.client.sendBlock(x, y+1, z, block)
                                        #else:
                                            #var_cango = True
                                            #target[1] = target[1] + 1
                                            #j = target[1]
                                            #try:
                                                #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
                                                #if blocktocheck != 0:
                                                    #var_cango = False
                                                #blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j+1,k)])
                                                #if blocktocheck != 0:
                                                    #var_cango = False
                                            #except:
                                                #var_cango = False
                                            #if var_cango:
                                                #block = chr(0)
                                                #try:
                                                    #world[x, y, z] = block
                                                #except:
                                                    #return
                                                #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                #self.client.sendBlock(x, y, z, block)
                                                #try:
                                                    #world[x, y+1, z] = block
                                                #except:
                                                    #return
                                                #self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                                #self.client.sendBlock(x, y+1, z, block)
                                                #var_position = target
                                                #x,y,z = var_position
                                                #block = chr(29)
                                                #try:
                                                    #world[x, y, z] = block
                                                #except:
                                                    #return
                                                #self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
                                                #self.client.sendBlock(x, y, z, block)
                                                #block = chr(12)
                                                #try:
                                                    #world[x, y+1, z] = block
                                                #except:
                                                    #return
                                                #self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
                                                #self.client.sendBlock(x, y+1, z, block)
                    except:
                        self.client.sendWorldMessage("ERROR")
                        self.client.log(traceback.format_exc(), level=logging.ERROR)

                entity[1] = var_position
                entity[2] = var_delay
                entity[3] = var_maxdelay
            var_dellist2 = []
            for index in var_dellist:
                if index not in var_dellist2:
                        var_dellist2.append(index)
            var_dellist2.sort()
            var_dellist2.reverse()
            for index in var_dellist2:
                del entitylist[index]
            if len(entitylist) > maxentitiystepsatonetime:
                for i in range(maxentitiystepsatonetime):
                    entitylist.append(entitylist.pop(0))
                
    @op_only
    def commandEntity(self, parts, byuser, overriderank):
        "/mob mobname - Op\nAliases: entitity\nCreates the specified Mob"
        if len(parts) != 2:
            if self.var_entityselected == "None":
                self.client.sendServerMessage("Please enter an Mob Name (type /mobs for a list)")
            else:
                self.var_entityselected = "None"
                self.client.sendServerMessage("Mob was deselected.")
        else:
            world = self.client.world
            try:
                entitylist = world.var_entities_entitylist
            except:
                world.var_entities_entitylist = []
                self.client.sendServerMessage("World MobList was created.")
            entity = parts[1]
            #if entity == "mob1":
                #self.var_entityselected = "mob1"
            #if entity == "cloud":
                #self.var_entityselected = "cloud"
            if entity == "rain":
                self.var_entityselected = "rain"
            elif entity == "bird":
                self.var_entityselected = "bird"
            elif entity == "blob":
                self.var_entityselected = "blob"
            #elif entity == "passiveblob":
                #self.var_entityselected = "passiveblob"
            #elif entity == "petblob":
                #self.var_entityselected = "petblob"
            elif entity == "pet":
                self.var_entityselected = "pet"
            elif entity == "trippyflower":
                self.var_entityselected = "trippyflower"
            elif entity == "slime":
                self.var_entityselected = "slime"
            elif entity == "jumpingshroom":
                self.var_entityselected = "jumpingshroom"
            elif entity == "trippyshroom":
                self.var_entityselected = "trippyshroom"
            elif entity == "smoke":
                self.var_entityselected = "smoke"
            elif entity == "zombie":
                self.var_entityselected = "zombie"
            elif entity == "creeper":
                self.var_entityselected = "creeper"
            elif entity == "tnt":
                self.var_entityselected = "tnt"
            elif entity == "fastzombie":
                self.var_entityselected = "fastzombie"
            elif entity == "human":
                self.var_entityselected = "human"
            #elif entity == "noob":
                #self.var_entityselected = "noob"
            else:
                self.client.sendServerMessage("%s is not a valid Mob." % entity)
                return
            self.client.sendServerMessage("Mob %s selected" % entity)
            self.client.sendServerMessage("To deselect just type /mob")

    @op_only
    def commandNumentities(self, parts, byuser, overriderank):
        "/nummobs - Op\nAliases: numentities\nTells you the number of Mobs in the map"
        world = self.client.world
        try:
            entitylist = world.var_entities_entitylist
        except:
            self.client.sendServerMessage("No List.")
            return
        self.client.sendServerMessage(str(len(entitylist)))
        
    @op_only
    def commandEntityclear(self, parts, byuser, overriderank):
        "/mobclear - Op\nAliases: entityclear\nClears the Mobs from the World."
        self.client.world.var_entities_entitylist = []
        self.client.sendServerMessage("Mobs cleared")
        
    @op_only
    def commandEntities(self, parts, byuser, overriderank):
        "/mobs - Op\nAliases: entities\nDisplays available Mobs"
        var_listofvalidentities = ["blob","pet","slime","creeper","zombie","fastzombie","bird","human","tnt","jumpingshroom","trippyshroom","trippyflower"]
        self.client.sendServerList(["Available Mobs:"] + var_listofvalidentities)
