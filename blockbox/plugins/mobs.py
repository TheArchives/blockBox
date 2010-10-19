# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from lib.twisted.internet import reactor
from random import randint
import os,sys, traceback
from time import time
import math

initfile = open("blockbox/entities/__init__.py")
exec initfile
initfile.close()
initfile = None

entitycodedict = {}
entityselectdict = {}
entitycreatedict = {}
validentities = []

def loadentities():
	global validentities
	datafilelist = os.listdir("blockbox/entities/")
	del datafilelist[datafilelist.index("__init__.py")]
	listofentityfiles = []
	for entry in datafilelist:
		if entry.find('_') == -1 and entry.endswith('.py'):
			listofentityfiles.append(entry)
	for entry in listofentityfiles:
		entitycodedict[entry[:-3]] = open("blockbox/entities/%s" % entry)
	validentities = entitycodedict.keys()
	
	for entry in validentities:
		possibeAliasFile = entry + "_aliases.txt"
		if possibeAliasFile in datafilelist:
			for alias in open("blockbox/entities/%s" % possibeAliasFile):
				alias = alias.rstrip()
				if alias != '':
					entitycodedict[alias] = entitycodedict[entry]
					
	validentities = []
	for entityname in entitycodedict:
		if entityname not in unselectableentities:
			validentities.append(entityname)
	
	for entry in validentities:
		
		possibeSelectFile = entry + "_select.py"
		if possibeSelectFile in datafilelist:
			entityselectdict[entry] = open("blockbox/entities/%s" % possibeSelectFile)
			
		possibeCreateFile = entry + "_create.py"
		if possibeCreateFile in datafilelist:
			entitycreatedict[entry] = open("blockbox/entities/%s" % possibeCreateFile)
				
loadentities()
for validentity in validentities:
	if validentity not in entityblocklist:
		entityblocklist[validentity] = [(0,0,0)]

class EntityPlugin(ProtocolPlugin):
	
	commands = {
		"entity": "commandEntity",
		"entityclear": "commandEntityclear",
		"numentities": "commandNumentities",
		"entities": "commandEntities",
		"mob": "commandEntity",
		"mobclear": "commandEntityclear",
		"nummobs": "commandNumentities",
		"mobs": "commandEntities",
		"item": "commandEntity",
		"itemclear": "commandEntityclear",
		"numitems": "commandNumentities",
		"items": "commandEntities",
		"epicentity": "commandEpicEntity",
		"epicmob": "commandEpicEntity",
	}

	hooks = {
		"blockchange": "blockChanged",
		"poschange": "posChanged",
		"newworld": "newWorld",
	}

	def gotClient(self):
		self.var_entityselected = "None"
		self.var_entityparts = []

	def newWorld(self, world):
		"Hook to reset entity making in new worlds."
		self.var_entityselected = "None"

	def blockChanged(self, x, y, z, block, selected_block, byuser):
		if not byuser:
			#People shouldnt be blbing mobs :P
			return
		"Hook trigger for block changes."
		world = self.client.world
		px,py,pz,ph,pp = self.client.x>>5,self.client.y>>5,self.client.z>>5,self.client.h,self.client.p
		world.entities_worldblockchangesdict[self.client] = ((x,y,z,time(),selected_block,block),(px,py,pz,ph,pp))
		entitylist = world.entitylist
		dellist = []
		for index in range(len(entitylist)):
			entity = entitylist[index]
			identity = entity[0]
			i,j,k = entity[1]
			if (i,j,k) == (x,y,z) or (identity in twoblockhighentities and (i,j+1,k) == (x,y,z)):
				dellist.append(index)
		dellist.reverse()
		for index in dellist:
			del entitylist[index]
			self.client.sendServerMessage("The entity is now deleted.")
		if block != 0:
			if self.var_entityselected != "None":
				if self.var_entityselected == "Superbomb":
					if world.entities_epicentity == []:
						world.entities_epicentity = ["Superbomb",(x,y,z),2,2,True,0,80]
						self.client.sendServerMessage("%s was created." % self.var_entityselected)
						return
					else:
						self.client.sendServerMessage("There can only be one epic entity on a map.")
						return
				if len(entitylist) >= maxentitiespermap:
					self.client.sendServerMessage("Max entities per map exceeded.")
					return
				if self.var_entityselected in entitycreatedict:
					exec entitycreatedict[self.var_entityselected]
					entitycreatedict[self.var_entityselected].seek(0)
				else:
					entitylist.append([self.var_entityselected,(x,y,z),8,8])
					self.client.sendServerMessage("The entity was created.")

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
			world.var_entities_keyuser = username
			keyuser = username
		if username == keyuser:
			entitylist = world.entitylist
			worldblockchangesdict = world.entities_worldblockchangesdict
			entities_childerenlist = world.entities_childerenlist
			worldblockchangedellist = []
			var_dellist = []
			var_abstime = time()
			userpositionlist = []
			for user in clients:
				userpositionlist.append((user,(user.x >> 5,user.y >> 5,user.z >> 5)))
			epicentity = world.entities_epicentity
			if epicentity != []:
				var_epicId = epicentity[0]
				x,y,z = epicentity[1]
				var_delete = False
				epicentity[2] -= 1
				if epicentity[2] < 0:
					epicentity[2] = epicentity[3]
					try:
						if not (0 <= x < world.x and 0 <= y < world.y and 0 <= z < world.z):
							var_delete = True
						if not var_delete:
							if var_epicId == "Superbomb":
								epicentity[6] -= 1
								if epicentity[6] <= 0:
									var_check = epicentity[4]
									epicentity[5] += 1
									radius = epicentity[5]
									var_userkillist = []
									var_userkillist2 = []
									for user in clients:
										tx,ty,tz = (user.x >> 5,user.y >> 5,user.z >> 5)
										distance = ((tx-x)**2+(ty-y)**2+(tz-z)**2)**0.5
										if var_check and distance <= radius:
											var_userkillist.append(user)
									for user in var_userkillist:
										if user not in var_userkillist2:
											var_userkillist2.append(user)
									for user in var_userkillist2:
										sx,sy,sz,sh = world.spawn
										user.teleportTo(sx,sy,sz,sh)
										self.client.sendWorldMessage("%s has been vaporized." % user.username)
									for index in range(len(entitylist)):
										rx,ry,rz = entitylist[index][1]
										distance = ((rx-x)**2+(ry-y)**2+(rz-z)**2)**0.5
										if distance <= radius:
											var_dellist.append(index)
									if var_check:
										block = '\x17'
									else:
										block = '\x00'
									for i,j,k in var_superbombtuple[radius]:
										try:
											world[x+i, y+j, z+k] = block
											self.client.queueTask(TASK_BLOCKSET, (x+i, y+j, z+k, block), world=world)
											self.client.sendBlock(x+i, y+j, z+k, block)
										except:
											pass
									if radius >= 10:
										if var_check:
											epicentity[4] = False
											block = '\x00'
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
											epicentity[5] = 0
										else:
											var_delete = True
							if var_delete:
								world.entities_epicentity = []
							else:
								epicentity[1] = (x,y,z)
						else:
							world.entities_epicentity = []
					except:
						self.client.sendWorldMessage("Internal Server Error")
						exc_type, exc_value, exc_traceback = sys.exc_info()
						traceback.print_exception(exc_type, exc_value, exc_traceback)
						world.entities_epicentity = []
						return
			var_num = len(entitylist)
			if var_num > maxentitiystepsatonetime:
				var_num = maxentitiystepsatonetime
			for index in range(var_num):
				entity = entitylist[index]
				var_type = entity[0]
				var_position = entity[1]
				entity[2] -= 1
				if entity[2] < 0:
					try:
						entity[2] = entity[3]
						x,y,z = var_position
						if not (0 <= x < world.x and 0 <= y < world.y and 0 <= z < world.z):
							var_dellist.append(index)
							if var_type in var_childrenentities:
								del entities_childerenlist[entities_childerenlist.index(entity[5])]
						elif (var_type in twoblockhighentities or var_type == "spawner" or var_type in twoblockhighshootingentities) and not (0 <= x < world.x and 0 <= y+1 < world.y and 0 <= z < world.z):
							var_dellist.append(index)
						elif var_type == "cannon":
							#these variables also used later
							var_orientation = entity[5]
							x,y,z = var_position
							if var_orientation == 0:
								var_sensorblocksoffsets = ((0,1,-2),(0,2,-2))
								var_loadblockoffset = (0,0,-1)
							elif var_orientation == 1:
								var_sensorblocksoffsets = ((2,1,0),(2,2,0))
								var_loadblockoffset = (1,0,0)
							elif var_orientation == 2:
								var_sensorblocksoffsets = ((0,1,2),(0,2,2))
								var_loadblockoffset = (0,0,1)
							elif var_orientation == 3:
								var_sensorblocksoffsets = ((-2,1,0),(-2,2,0))
								var_loadblockoffset = (-1,0,0)
							n,m,o = var_loadblockoffset
							if not (0 <= x+n < world.x and 0 <= y+m < world.y and 0 <= z+o < world.z):
								var_dellist.append(index)
							else:
								for q,r,s in var_sensorblocksoffsets:
									if not (0 <= x+q < world.x and 0 <= y+r < world.y and 0 <= z+s < world.z):
										var_dellist.append(index)
						if index not in var_dellist:
							if var_type in entitycodedict:
								exec entitycodedict[var_type]
								entitycodedict[var_type].seek(0)
							else:
								self.client.sendWorldMessage("UNKOWN ENTITY IN WORLD - FIX THIS!")
					except:
						self.client.sendWorldMessage("Internal Server Error")
						exc_type, exc_value, exc_traceback = sys.exc_info()
						traceback.print_exception(exc_type, exc_value, exc_traceback)
						world.entitylist = []
						return
				entity[1] = var_position
			var_dellist2 = []
			for index in var_dellist:
				if index not in var_dellist2:
						var_dellist2.append(index)
			var_dellist2.sort()
			var_dellist2.reverse()
			for index in var_dellist2:
				del entitylist[index]
			worldblockchangedellist2 = []
			for index in worldblockchangedellist:
				if index not in worldblockchangedellist2:
						worldblockchangedellist2.append(index)
			for index in worldblockchangedellist2:
				del worldblockchangesdict[index]
			if len(entitylist) > maxentitiystepsatonetime:
				for i in range(maxentitiystepsatonetime):
					entitylist.append(entitylist.pop(0))

	@op_only
	def commandEntity(self, parts, byuser, overriderank):
		"/entity entityname - Op\nAliases: item, mob\nCreates the specified entity."
		if len(parts) < 2:
			if self.var_entityselected == "None":
				self.client.sendServerMessage("Please enter an entity name (type /entities for a list)")
			else:
				self.var_entityselected = "None"
				self.client.sendServerMessage("The entity has been deselected.")
		else:
			world = self.client.world
			entity = parts[1]
			var_continue = True
			if entity in validentities:
				if entity in entityselectdict:
					exec entityselectdict[entity]
					entityselectdict[entity].seek(0)
				else:
					self.var_entityselected = entity
			else:
				self.client.sendServerMessage("%s is not a valid entity." % entity)
				return
			if var_continue:
				self.client.sendServerMessage("The entity %s has been selected." % entity)
				self.client.sendServerMessage("To deselect just type /entity")

	@op_only
	def commandNumentities(self, parts, byuser, overriderank):
		"/numentities - Op\nAliases: numitems, nummobs\nTells you the number of entities in the map."
		world = self.client.world
		entitylist = world.entitylist
		self.client.sendServerMessage(str(len(entitylist)))
		
	@op_only
	def commandEntityclear(self, parts, byuser, overriderank):
		"/entityclear - Op\nAliases: itemclear, mobclear\nClears the entities from the map."
		world = self.client.world
		for entity in self.client.world.entitylist:
			var_id = entity[0]
			x,y,z = entity[1]
			if var_id in entityblocklist:
				for offset in entityblocklist[var_id]:
					ox,oy,oz = offset
					rx,ry,rz = x+ox,y+oy,z+oz
					block = '\x00'
					world[rx, ry, rz] = block
					self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
					self.client.sendBlock(rx, ry, rz, block)
			elif var_id == "cannon":
				var_orientation = entity[5]
				if var_orientation == 0:
					var_sensorblocksoffsets = ((0,1,-2),(0,2,-2))
					var_loadblockoffset = (0,0,-1)
				elif var_orientation == 1:
					var_sensorblocksoffsets = ((2,1,0),(2,2,0))
					var_loadblockoffset = (1,0,0)
				elif var_orientation == 2:
					var_sensorblocksoffsets = ((0,1,2),(0,2,2))
					var_loadblockoffset = (0,0,1)
				elif var_orientation == 3:
					var_sensorblocksoffsets = ((-2,1,0),(-2,2,0))
					var_loadblockoffset = (-1,0,0)
				block = '\x00'
				world[x, y, z] = block
				self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
				self.client.sendBlock(x, y, z, block)
				i,j,k = var_loadblockoffset
				rx,ry,rz = x+i,y+j,z+k
				world[rx, ry, rz] = block
				self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
				self.client.sendBlock(rx, ry, rz, block)
				for i,j,k in var_sensorblocksoffsets:
					rx,ry,rz = x+i,y+j,z+k
					world[rx, ry, rz] = block
					self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
					self.client.sendBlock(rx, ry, rz, block)
			else:
				self.client.sendServerMessage("Entity not registered in the entityblocklist.")
		self.client.world.entitylist = []
		self.client.sendWorldMessage("The entities have been cleared.")
		
	@op_only
	def commandEntities(self, parts, byuser, overriderank):
		"/entities - Op\nAliases: items, mobs\nDisplays available entities."
		varsorted_validentities = validentities[:]
		varsorted_validentities.sort()
		self.client.sendServerList(["Available entities:"] + varsorted_validentities)
		self.client.sendServerList(["Epic entities: "] + ["Superbomb"])

	@mod_only
	def commandEpicEntity(self, parts, byuser, overriderank):
		"/epicentity entityname - Op\nAliases: epicmob\nCreates the specified entity"
		if len(parts) < 2:
			if self.var_entityselected == "None":
				self.client.sendServerMessage("Please enter an epic entity name (type /entities for a list)")
			else:
				self.var_entityselected = "None"
				self.client.sendServerMessage("entity deselected")
		else:
			world = self.client.world
			entity = parts[1]
			if entity == "Superbomb":
				self.var_entityselected = "Superbomb"
			else:
				self.client.sendServerMessage("%s is not a valid epic entity." % entity)
				return
			self.client.sendServerMessage("The epic entity %s has been selected." % entity)
			self.client.sendServerMessage("To deselect just type /entity")
