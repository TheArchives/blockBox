# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import math, sys, traceback
from random import randint
from time import time

from lib.twisted.internet import reactor

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

"""
Here is a rundown of how the mobs file works. Mobs are dynamic lists of data that are themselves stored in another list.
The various mob data is looped and rerun,though the mobs themselves have a built in delay which prevents them from running too fast
Mobs are typically bits of code which place blocks inaccordance to their code. This means you
will have to use other means to delay any mobs. There are three main parts of code a mob must have before it will run, as
stated below

--- Blockchange code ---
This code is run each time a player places a mob. It adds the mob to an internal list. Any variables
or statements included in each mobs elif statement are run as well.it adds a mob to the plugins mob list, and sets any other
variables that are included.

---Poschanged code ---
This code is essentially the movement or reaction code that runs the mob. Without this code the mob
will not do anything. Any variables defined in the poschanged code are unassigned each time a mob moves,so if you want any
constant data to carry over between loops, store it in the poschanged code or in the mob's list.

--- Command entity code ---
This code determines what can be selected by the /mob or /entity commands in-game. You will also
have to add the mob's string name to a single line, which is run when a player uses /mobs or /entities, and tells the player
what mobs are available

--- Other notes /quirks ---
Note that all blockcheck code must be run within a try/except statement.  Note that because all
mobs are run in each loop, any delays, such as sleep(), reactor.callater, or any loops will stop the enitre mob code until
done. Note, Entityblocklist and other similar lists are needed for the mobclear code. They place air at the mobs locations.
Each mobs list in this code represents the blocks, and the numbers are the offsets of its x, y and z
"""

explosionblocklist = [[-3, -1, 0], [-3, 0, -1], [-3, 0, 0], [-3, 0, 1], [-3, 1, 0], [-2, -2, -1], [-2, -2, 0], [-2, -2, 1], [-2, -1, -2], [-2, -1, -1], [-2, -1, 0], [-2, -1, 1], [-2, -1, 2], [-2, 0, -2], [-2, 0, -1], [-2, 0, 0], [-2, 0, 1], [-2, 0, 2], [-2, 1, -2], [-2, 1, -1], [-2, 1, 0], [-2, 1, 1], [-2, 1, 2], [-2, 2, -1], [-2, 2, 0], [-2, 2, 1], [-1, -3, 0], [-1, -2, -2], [-1, -2, -1], [-1, -2, 0], [-1, -2, 1], [-1, -2, 2], [-1, -1, -2], [-1, -1, -1], [-1, -1, 0], [-1, -1, 1], [-1, -1, 2], [-1, 0, -3], [-1, 0, -2], [-1, 0, -1], [-1, 0, 0], [-1, 0, 1], [-1, 0, 2], [-1, 0, 3], [-1, 1, -2], [-1, 1, -1], [-1, 1, 0], [-1, 1, 1], [-1, 1, 2], [-1, 2, -2], [-1, 2, -1], [-1, 2, 0], [-1, 2, 1], [-1, 2, 2], [-1, 3, 0], [0, -3, -1], [0, -3, 0], [0, -3, 1], [0, -2, -2], [0, -2, -1], [0, -2, 0], [0, -2, 1], [0, -2, 2], [0, -1, -3], [0, -1, -2], [0, -1, -1], [0, -1, 0], [0, -1, 1], [0, -1, 2], [0, -1, 3], [0, 0, -3], [0, 0, -2], [0, 0, -1], [0, 0, 1], [0, 0, 2], [0, 0, 3], [0, 1, -3], [0, 1, -2], [0, 1, -1], [0, 1, 0], [0, 1, 1], [0, 1, 2], [0, 1, 3], [0, 2, -2], [0, 2, -1], [0, 2, 0], [0, 2, 1], [0, 2, 2], [0, 3, -1], [0, 3, 0], [0, 3, 1], [1, -3, 0], [1, -2, -2], [1, -2, -1], [1, -2, 0], [1, -2, 1], [1, -2, 2], [1, -1, -2], [1, -1, -1], [1, -1, 0], [1, -1, 1], [1, -1, 2], [1, 0, -3], [1, 0, -2], [1, 0, -1], [1, 0, 0], [1, 0, 1], [1, 0, 2], [1, 0, 3], [1, 1, -2], [1, 1, -1], [1, 1, 0], [1, 1, 1], [1, 1, 2], [1, 2, -2], [1, 2, -1], [1, 2, 0], [1, 2, 1], [1, 2, 2], [1, 3, 0], [2, -2, -1], [2, -2, 0], [2, -2, 1], [2, -1, -2], [2, -1, -1], [2, -1, 0], [2, -1, 1], [2, -1, 2], [2, 0, -2], [2, 0, -1], [2, 0, 0], [2, 0, 1], [2, 0, 2], [2, 1, -2], [2, 1, -1], [2, 1, 0], [2, 1, 1], [2, 1, 2], [2, 2, -1], [2, 2, 0], [2, 2, 1], [3, -1, 0], [3, 0, -1], [3, 0, 0], [3, 0, 1], [3, 1, 0]]
maxentitiystepsatonetime = 20
twoblockhighentities = ["creeper","zombie","noob","person","aquabie"]
twoblockhighshootingentities = ["bckchngdetector","testbow","paintballgun"]
maxentitiespermap = 40
entityblocklist = {"entity1":[(0,0,0)], "blob":[(0,0,0)],"passiveblob":[(0,0,0)],"petblob":[(0,0,0)],"jumpingshroom":[(0,0,0)],"trippyshroom":[(0,0,0)],"smoke":[(0,0,0)],"zombie":[(0,0,0),(0,1,0)],"creeper":[(0,0,0),(0,1,0)],"tnt":[(0,0,0)],"person":[(0,0,0),(0,1,0)],"noob":[(0,0,0),(0,1,0)],"proxmine":[(0,0,0)],"var":[(0,0,0)],"spawner":[(0,0,0)],"bckchngdetector":[(0,0,0),(0,1,0)],"testbow":[(0,0,0),(0,1,0)],"testarrow":[(0,0,0)],"paintballgun":[(0,0,0),(0,1,0)],"paintball":[(0,0,0)],"cloud":[(0,0,0),(1,0,0),(-1,0,0),(0,0,1),(0,0,-1)],"fish":[(0,0,0)],"rainbowfish":[(0,0,0)]}
colorblocks = [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]
var_unpainablelist = [7,20,42,41,49,40,44,43,39,38,6,37,38]
var_unbreakables = ['\x07', '*', ')', '.', '1']
var_childrenentities = ["testarrow","paintball","cannonball"]
runonce = True

class EntityPlugin(ProtocolPlugin):	"Class for mobs handling."
	commands = {
		"entity": "commandEntity",
		"entityclear": "commandEntityclear",
		"numentities": "commandNumentities",
		"entities": "commandEntities",
		"mob": "commandEntity",
		"mobclear": "commandEntityclear",
		"nummobs": "commandNumentities",
		"mobs": "commandEntities",
	}

	hooks = {
		"preblockchange": "blockChanged",
		"poschange": "posChanged",
		"newworld": "newWorld",
	}

	def gotClient(self):
		self.var_entityselected = "None"
		self.var_entityparts = []

	def newWorld(self, world):
		"Hook to reset entity making in new worlds."
		self.var_entityselected = "None"

	def blockChanged(self, x, y, z, block, selected_block, fromloc):
		if fromloc != 'user':
			#People shouldn't be blbing mobs :P
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
			self.client.sendServerMessage("Entity was deleted.")
		if block != 0:
			if self.var_entityselected != "None":
				if len(entitylist) >= maxentitiespermap:
					self.client.sendServerMessage("Max entities per map was exceeded.")
					return
				if self.var_entityselected == "cloud":
					entitylist.append(["cloud",(x,y,z),15,15,1,2,3])
					self.client.sendServerMessage("Cloud was created.")
					self.runonce = None
				#elif self.var_entityselected == "entity1":
				#	entitylist.append(["entity1",(x,y,z),2,2])
				#	self.client.sendServerMessage("Entity1 was created.")
				elif self.var_entityselected == "rain":
					entitylist.append(["rain",(x,y,z),2,2])
					self.client.sendServerMessage("Rain was created.")
				elif self.var_entityselected == "bird":
					entitylist.append(["bird",(x,y,z),8,8])
					self.client.sendServerMessage("Bird was created.")
				elif self.var_entityselected == "blob":
					entitylist.append(["blob",(x,y,z),8,8])
					self.client.sendServerMessage("Blob was created.")
				#elif self.var_entityselected == "passiveblob":
				#	entitylist.append(["passiveblob",(x,y,z),8,8])
				#	self.client.sendServerMessage("Passive Blob was created.")
				#elif self.var_entityselected == "petblob":
				#	entitylist.append(["petblob",(x,y,z),8,8,self.client.username.lower()])
				#	self.client.sendServerMessage("Pet Blob was created.")
				elif self.var_entityselected == "pet":
					entitylist.append(["pet",(x,y,z),8,8,self.client])
					self.client.sendServerMessage("A Pet was created.")
				elif self.var_entityselected == "jumpingshroom":
					entitylist.append(["jumpingshroom",(x,y,z),8,8])
					self.client.sendServerMessage("Jumping Shroom was created.")
				elif self.var_entityselected == "trippyflower":
					entitylist.append(["trippyflower",(x,y,z),8,8,self.client])
					self.client.sendServerMessage("Trippy Flower was created.")
				elif self.var_entityselected == "trippyshroom":
					entitylist.append(["trippyshroom",(x,y,z),4,4,True])
					self.client.sendServerMessage("Trippy Shroom was created.")
				elif self.var_entityselected == "slime":
					entitylist.append(["slime",(x,y,z),8,8,self.client])
					self.client.sendServerMessage("Slime was created.")
				elif self.var_entityselected == "smoke":
					entitylist.append(["smoke",(x,y,z),4,4,True])
					self.client.sendServerMessage("Smoke was created.")
				elif self.var_entityselected == "zombie":
					entitylist.append(["zombie",(x,y,z),8,8])
					self.client.sendServerMessage("Zombie was created.")
				elif self.var_entityselected == "aquabie":
					entitylist.append(["aquabie",(x,y,z),8,8,True])
					self.client.sendServerMessage("Aqua Zombie was created.")
				#elif self.var_entityselected == "piranna":
				#	entitylist.append(["piranna",(x,y,z),4,4,True])
				#	self.client.sendServerMessage("Piranna was created.")
				elif self.var_entityselected == "creeper":
					entitylist.append(["creeper",(x,y,z),8,8])
					self.client.sendServerMessage("Creeper was created.")
				elif self.var_entityselected == "tnt":
					if block == 46:
						entitylist.append(["tnt",(x,y,z),1,1,True,24,5])
						self.client.sendServerMessage("TNT was created.")
					else:
						self.client.sendServerMessage("Please place TNT blocks.")
				elif self.var_entityselected == "fastzombie":
					entitylist.append(["zombie",(x,y,z),6,6])
					self.client.sendServerMessage("Fast Zombie was created.")
				elif self.var_entityselected == "fish":
					(i,j,k) = (x,y,z)
					entitylist.append(["fish",(x,y,z),7,7,(i,j,k),3])
					self.client.sendServerMessage("A fish was created.")
				elif self.var_entityselected == "rainbowfish":
					(i,j,k) = (x,y,z)
					entitylist.append(["rainbowfish",(x,y,z),7,7,(i,j,k),3])
					self.client.sendServerMessage("A rainbow fish was created.")
				elif self.var_entityselected == "person":
					entitylist.append(["person",(x,y,z),8,8])
					self.client.sendServerMessage("A person was created.")
				elif self.var_entityselected == "noob":
					entitylist.append(["noob",(x,y,z),8,8])
					self.client.sendServerMessage("A noob was created.")
				elif self.var_entityselected == "proxmine":
					entitylist.append(["proxmine",(x,y,z),8,8,24])
					self.client.sendServerMessage("Proxmine was created.")
				elif self.var_entityselected == "var":
					entitylist.append(["var",(x,y,z),8,8,self.client.username.lower()] + self.var_entityparts)
					self.client.sendServerMessage("Your Make-a-Mod has been created.")
				elif self.var_entityselected == "spawner":
					entitylist.append(["spawner",(x,y,z),160,160])
					self.client.sendServerMessage("You've made a Mob Spawner.")
				elif self.var_entityselected == "bckchngdetector":
					entitylist.append(["bckchngdetector",(x,y,z),8,8])
					self.client.sendServerMessage("Block Change Detector was created.")
				#elif self.var_entityselected == "testbow":
				#	entitylist.append(["testbow",(x,y,z),8,8,None])
				#	self.client.sendServerMessage("Test Bow was created.")
				elif self.var_entityselected == "paintballgun":
					entitylist.append(["paintballgun",(x,y,z),8,8,None])
					self.client.sendServerMessage("Paint Ball Gun was created.")
				elif self.var_entityselected == "cannon":
					if ph >= 224 or ph < 32:
						var_orientation = 0
					elif 32 <= ph < 96:
						var_orientation = 1
					elif 96 <= ph < 160:
						var_orientation = 2
					elif 160 <= ph < 224:
						var_orientation = 3
					entitylist.append(["cannon",(x,y,z),8,8,None,var_orientation,False])
					self.client.sendServerMessage("Cannon was created.")

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
						x,y,z = var_position
						if not (0 <= x < world.x and 0 <= y < world.y and 0 <= z < world.z):
							var_dellist.append(index)
							if var_type in var_childrenentities:
								del entities_childerenlist[entities_childerenlist.index(entity[5])]
						if (var_type in twoblockhighentities or var_type == "spawner" or var_type in twoblockhighshootingentities) and not (0 <= x < world.x and 0 <= y+1 < world.y and 0 <= z < world.z):
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
							#elif var_type == "entity1":
							#	x,y,z = var_position
							#	var_cango = True
							#	try:
							#		blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x, y, z+1)])
							#		if blocktocheck != 0:
							#			var_cango = False
							#	except:
							#		var_cango = False
							#	if var_cango:
							#		block = '\x00'
							#		world[x, y, z] = block
							#		self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#		self.client.sendBlock(x, y, z, block)
							#		var_position = (x,y,z+1)
							#		z += 1
							#		block = chr(11) 
							#		world[x, y, z] = block
							#		self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#		self.client.sendBlock(x, y, z, block)
							#	else:
							#		var_dellist.append(index)
							elif var_type == "blob":
								var_cango = True
								try:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
									if blocktocheck != 0:
										var_cango = False
								except:
									var_cango = False
								if var_cango:
									block = '\x00'
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									var_position = (x,y-1,z)
									x,y,z = var_position
									block = chr(11)
									world[x, y, z] = block
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
										self.client.sendPlainWorldMessage("%s%s has died from a blob." % (COLOUR_DARKRED, closestclient.username))
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
											block = '\x00'
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
											var_position = target
											x,y,z = var_position
											block = chr(11)
											world[x, y, z] = block
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
												block = '\x00'
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												var_position = target
												x,y,z = var_position
												block = chr(11)
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
							#elif var_type == "passiveblob":
							#	x,y,z = var_position
							#	var_cango = True
							#	try:
							#		blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
							#		if blocktocheck != 0:
							#			var_cango = False
							#	except:
							#		var_cango = False
							#	if var_cango:
							#		block = '\x00'
							#		world[x, y, z] = block
							#		self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#		self.client.sendBlock(x, y, z, block)
							#		var_position = (x,y-1,z)
							#		x,y,z = var_position
							#		block = chr(9)
							#		world[x, y, z] = block
							#		self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#		self.client.sendBlock(x, y, z, block)
							#	else:
							#		userpositionlist = []
							#		for user in clients:
							#			userpositionlist.append((user.x >> 5,user.y >> 5,user.z >> 5))
							#		closestposition = (0,0)
							#		closestclient = None
							#		closestdistance = None
							#		for var_pos in userpositionlist:
							#			i,j,k = var_pos
							#			distance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
							#			if closestdistance == None:
							#				closestdistance = distance
							#				closestposition = (var_pos[0],var_pos[2])
							#			else:
							#				if distance < closestdistance:
							#					closestdistance = distance
							#					closestposition = (var_pos[0],var_pos[2])
							#		i,k = closestposition
							#		distance = ((i-x)**2+(k-z)**2)**0.5
							#		if distance != 0 and distance > 3:
							#			target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
							#			i,j,k = target
							#			var_cango = True
							#			try:
							#				blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
							#				if blocktocheck != 0:
							#					var_cango = False
							#			except:
							#				var_cango = False
							#			if var_cango:
							#				block = '\x00'
							#				world[x, y, z] = block
							#				self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#				self.client.sendBlock(x, y, z, block)
							#				var_position = target
							#				x,y,z = var_position
							#				block = chr(9)
							#				world[x, y, z] = block
							#				self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#				self.client.sendBlock(x, y, z, block)
							#			else:
							#				var_cango = True
							#				target[1] = target[1] + 1
							#				j = target[1]
							#				try:
							#					blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
							#					if blocktocheck != 0:
							#						var_cango = False
							#				except:
							#					var_cango = False
							#				if var_cango:
							#					block = '\x00'
							#					world[x, y, z] = block
							#					self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#					self.client.sendBlock(x, y, z, block)
							#					var_position = target
							#					x,y,z = var_position
							#					block = chr(9)
							#					world[x, y, z] = block
							#					self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#					self.client.sendBlock(x, y, z, block)
							elif var_type == "fish":
								var_cango = True
								
								if entity[5] >= 3:
									i = randint(-1,1)
									k = randint(-1,1)
									j = randint(-1,1)
									entity[4] = (i,j,k)
									entity[5] = 0
								entity[5] = randint(1,5)
								l, m, n = entity[4]
								try:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x+l,y+m,z+n)])
									if blocktocheck != 8:
										var_cango = False
								except:
									return
								if var_cango:
									block = '\x08'
									self.client.queueTask(TASK_BLOCKSET, (x,y,z, block), world=world)
									self.client.sendBlock(x,y,z, block)
									block = '\x20'
									self.client.queueTask(TASK_BLOCKSET, (x+l,y+m,z+n, block), world=world)
									self.client.sendBlock(x+l,y+m,z+n, block)
									var_position = (x+l,y+m,z+n)
									x,y,z = var_position

							elif var_type == "rainbowfish":
								var_cango = True
								
								if entity[5] >= 3:
									i = randint(-1,1)
									k = randint(-1,1)
									j = randint(-1,1)
									entity[4] = (i,j,k)
									entity[5] = 0
								entity[5] = randint(1,5)
								l, m, n = entity[4]
								try:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x+l,y+m,z+n)])
									if blocktocheck != 8:
										var_cango = False
								except:
									return
								if var_cango:
									block = '\x08'
									self.client.queueTask(TASK_BLOCKSET, (x,y,z, block), world=world)
									self.client.sendBlock(x,y,z, block)
									w = randint(21,36)
									block = chr(w)
									self.client.queueTask(TASK_BLOCKSET, (x+l,y+m,z+n, block), world=world)
									self.client.sendBlock(x+l,y+m,z+n, block)
									var_position = (x+l,y+m,z+n)
									x,y,z = var_position


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
							#	x,y,z = var_position
							#	var_cango = True
							#	try:
							#		blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
							#		if blocktocheck != 0:
							#			var_cango = False
							#	except:
							#		var_cango = False
							#	if var_cango:
							#		block = '\x00'
							#		world[x, y, z] = block
							#		self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#		self.client.sendBlock(x, y, z, block)
							#		var_position = (x,y-1,z)
							#		x,y,z = var_position
							#		block = chr(9)
							#		world[x, y, z] = block
							#		self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#		self.client.sendBlock(x, y, z, block)
							#	else:
							#		ownername = entity[4]
							#		ownerclient = self.client.factory.usernames[ownername]
							#		if ownername in worldusernamelist:
							#			i,j,k = (ownerclient.x >> 5,ownerclient.y >> 5,ownerclient.z >> 5)
							#			distance = ((i-x)**2+(k-z)**2)**0.5
							#			if distance != 0 and distance > 2:
							#				target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
							#				i,j,k = target
							#				var_cango = True
							#				try:
							#					blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
							#					if blocktocheck != 0:
							#						var_cango = False
							#				except:
							#					var_cango = False
							#				if var_cango:
							#					block = '\x00'
							#					world[x, y, z] = block
							#					self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#					self.client.sendBlock(x, y, z, block)
							#					var_position = target
							#					x,y,z = var_position
							#					block = chr(9)
							#					world[x, y, z] = block
							#					self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#					self.client.sendBlock(x, y, z, block)
							#				else:
							#					var_cango = True
							#					target[1] = target[1] + 1
							#					j = target[1]
							#					try:
							#						blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
							#						if blocktocheck != 0:
							#							var_cango = False
							#					except:
							#						var_cango = False
							#					if var_cango:
							#						block = '\x00'
							#						world[x, y, z] = block
							#						self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#						self.client.sendBlock(x, y, z, block)
							#						var_position = target
							#						x,y,z = var_position
							#						block = chr(9)
							#						world[x, y, z] = block
							#						self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#						self.client.sendBlock(x, y, z, block)
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
									block = '\x00'
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									var_position = (x,y-1,z)
									y -= 1
									block = chr(39) 
									world[x, y, z] = block
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
										block = '\x00'
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
										var_position = (x,y+1,z)
										y += 1
										block = chr(39) 
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)

							elif var_type == "confetti":
								x,y,z = var_position
								i = randint(-1,1) + x
								j = 1 - y
								k = randint(-1,1) + z
								var_cango = True
								if entity[4]:
									entity[4] = False
									if world.blockstore.raw_blocks[world.blockstore.get_offset(x,y,z)] not in var_unbreakables:
										block = '\x00'
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
								else:
									block = '\x00'
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
								try:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)])
									if blocktocheck != 0:
										var_cango = False
								except:
									var_cango = False
								if var_cango and randint(0,15) != 10:
									var_position = (i,j,k)
									x,y,z = var_position
									block = chr(36) 
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
								else:
									var_dellist.append(index)

							elif var_type == "smoke":
								x,y,z = var_position
								i = randint(-1,1) + x
								j = 1 + y
								k = randint(-1,1) + z
								var_cango = True
								if entity[4]:
									entity[4] = False
									if world.blockstore.raw_blocks[world.blockstore.get_offset(x,y,z)] not in var_unbreakables:
										block = '\x00'
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
								else:
									block = '\x00'
									world[x, y, z] = block
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
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
								else:
									var_dellist.append(index)
							elif var_type == "trippyshroom":
								x,y,z = var_position
								if entity[4]:
									entity[4] = False
									block = chr(39)
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
								else:
									entity[4] = True
									block = chr(40)
									world[x, y, z] = block
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
							elif var_type == "cloud":
								x,y,z = var_position
								i = randint(-1,1) + x
								j = randint(-1,1) + y
								k = randint(-1,1) + z
								r = randint(3,13)
								var_cango = True
								block = chr(0)
								try:
									world[x, y, z] = block
								except:
									return
								self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
								self.client.sendBlock(x, y, z, block)
								self.client.queueTask(TASK_BLOCKSET, (x-1, y, z, block), world=world)
								self.client.sendBlock(x-1, y, z, block)
								self.client.queueTask(TASK_BLOCKSET, (x+1, y, z, block), world=world)
								self.client.sendBlock(x+1, y, z, block)
								self.client.queueTask(TASK_BLOCKSET, (x, y, z-1, block), world=world)
								self.client.sendBlock(x, y, z-1, block)
								self.client.queueTask(TASK_BLOCKSET, (x, y, z+1, block), world=world)
								self.client.sendBlock(x, y, z+1, block) 
								try:
									#if self.runonce == None:
									#	self.runonce = 0
									#	entity[4] = x
									#	entity[5] = y
									#	entity[6] = z
									#dx = abs(x - entity[4])
									#dy = abs(y - entity[5])
									#dz = abs(z - entity[6])
									#print(dy)
									#if entity[4] + 6 < dx or entity[5] + 6 < dy or entity[6] + 6 < dz:
									#	var_cango = False
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)])
									if blocktocheck != 0:
										var_cango = False
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i-1, j, k)])
									if blocktocheck != 0:
										var_cango = False
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i+1, j, k)])
									if blocktocheck != 0:
										var_cango = False
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k-1)])
									if blocktocheck != 0:
										var_cango = False
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k+1)])
									if blocktocheck != 0:
										var_cango = False
								except:
									var_cango = False
								if var_cango and randint(0,2) != 2:
									var_position = (i,j,k)
									x,y,z = var_position
									block = chr(36) 
									try:
										world[x, y, z] = block
									except:
										return
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									self.client.queueTask(TASK_BLOCKSET, (x-1, y, z, block), world=world)
									self.client.sendBlock(x-1, y, z, block)
									self.client.queueTask(TASK_BLOCKSET, (x+1, y, z, block), world=world)
									self.client.sendBlock(x+1, y, z, block)
									self.client.queueTask(TASK_BLOCKSET, (x, y, z-1, block), world=world)
									self.client.sendBlock(x, y, z-1, block)
									self.client.queueTask(TASK_BLOCKSET, (x, y, z+1, block), world=world)
									self.client.sendBlock(x, y, z+1, block)
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j-1, k)])
									if blocktocheck == 0 and randint(-1,2) == 0:
										entitylist.append(["rain",(x,y-1,z),r,r])
								else:
									return
									entitylist.append(["rain",(x,y-1,z),r,r])
							elif var_type == "rain":
								x,y,z = var_position
								i = x
								j = -1 + y
								k = z
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
								if var_cango and randint(0,45) != 45:
									var_position = (i,j,k)
									x,y,z = var_position
									block = chr(9) 
									try:
										world[x, y, z] = block
									except:
										return
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
								else:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)])
									if blocktocheck != 0:
										var_cango = False
										var_dellist.append(index)
							elif var_type == "zombie":
								x,y,z = var_position
								var_cango = True
								try:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
									if blocktocheck != 0:
										var_cango = False
								except:
									var_cango = False
								if var_cango:
									block = '\x00'
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									world[x, y+1, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
									self.client.sendBlock(x, y+1, z, block)
									var_position = (x,y-1,z)
									x,y,z = var_position
									block = chr(35)
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									block = chr(25)
									world[x, y+1, z] = block
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
										self.client.sendPlainWorldMessage("%s%s has died from a Zombie." % (COLOUR_DARKRED, closestclient.username))
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
											block = '\x00'
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
											world[x, y+1, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
											self.client.sendBlock(x, y+1, z, block)
											var_position = target
											x,y,z = var_position
											block = chr(35)
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
											block = chr(25)
											world[x, y+1, z] = block
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
												block = '\x00'
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												world[x, y+1, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
												self.client.sendBlock(x, y+1, z, block)
												var_position = target
												x,y,z = var_position
												block = chr(35)
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												block = chr(25)
												world[x, y+1, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
												self.client.sendBlock(x, y+1, z, block)
							elif var_type == "aquabie":
								x,y,z = var_position
								var_cango = True
								try:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
									if blocktocheck != 8:
										var_cango = False
								except:
									var_cango = False
								if var_cango:
									block = '\x08'
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									world[x, y+1, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
									self.client.sendBlock(x, y+1, z, block)
									var_position = (x,y-1,z)
									x,y,z = var_position
									block = chr(35)
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									block = chr(25)
									world[x, y+1, z] = block
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
										self.client.sendPlainWorldMessage("%s%s has died from a Aqua Zombie." % (COLOUR_DARKRED, closestclient.username))
									i,k = closestposition
									distance = ((i-x)**2+(k-z)**2)**0.5
									if distance != 8:
										target = [int((i-x)/(distance/1.75)) + x,y,int((k-z)/(distance/1.75)) + z]
										i,j,k = target
										var_cango = True
										try:
											blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
											if blocktocheck != 8:
												var_cango = False
											blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j+1,k)])
											if blocktocheck != 8:
												var_cango = False
										except:
											var_cango = False
										if var_cango:
											block = '\x08'
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
											world[x, y+1, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
											self.client.sendBlock(x, y+1, z, block)
											var_position = target
											x,y,z = var_position
											block = chr(35)
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
											block = chr(25)
											world[x, y+1, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
											self.client.sendBlock(x, y+1, z, block)
										else:
											var_cango = True
											target[1] = target[1] + 1
											j = target[1]
											try:
												blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
												if blocktocheck != 8:
													var_cango = False
												blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j+1,k)])
												if blocktocheck != 8:
													var_cango = False
											except:
												var_cango = False
											if var_cango:
												block = '\x08'
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												world[x, y+1, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
												self.client.sendBlock(x, y+1, z, block)
												var_position = target
												x,y,z = var_position
												block = chr(35)
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												block = chr(25)
												world[x, y+1, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
												self.client.sendBlock(x, y+1, z, block)
							#if var_type == "piranna":
							#	x,y,z = var_position
							#	userpositionlist = []
							#	for user in clients:
							#		userpositionlist.append((user.x >> 5,user.y >> 5,user.z >> 5))
							#	closestposition = (0,0)
							#	closestclient = None
							#	closestdistance = None
							#	for var_pos in userpositionlist:
							#		i,j,k = var_pos
							#		distance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
							#		if closestdistance == None:
							#			closestdistance = distance
							#			closestposition = (var_pos[0],var_pos[2])
							#		else:
							#			if distance < closestdistance:
							#				closestdistance = distance
							#				closestclient = client
							#				closestposition = (var_pos[0],var_pos[2])
							#		if closestdistance < 2:
							#			sx,sy,sz,sh = world.spawn
							#			closestclient.teleportTo(sx,sy,sz,sh)
							#			self.client.sendPlainWorldMessage("%s%s has died from a Piranna." % (COLOUR_DARKRED, closestclient.username))
							#		if closestdistance != 0:
							#			i,k = closestposition
							#			target = [int((i-x)/(closestdistance/1.75)) + x,y,int((k-z)/(closestdistance/1.75)) + z]
							#			i,j,k = target
							#			var_cango = True
							#			try:
							#				blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
							#				if blocktocheck != 5:
							#					var_cango = False
							#			except:
							#				var_cango = False
							#			if var_cango:
							#				block = '\x00'
							#				world[x, y, z] = block
							#				self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#				self.client.sendBlock(x, y, z, block)
							#				var_position = target
							#				x,y,z = var_position
							#				block = chr(23)
							#				world[x, y, z] = block
							#				self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#				self.client.sendBlock(x, y, z, block)
							#			else:
							#				var_cango = True
							#				target[1] = target[1] + 1
							#				j = target[1]
							#				try:
							#					blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
							#					if blocktocheck != 0:
							#						var_cango = False
							#				except:
							#					var_cango = False
							#				if var_cango:
							#					block = '\x00'
							#					world[x, y, z] = block
							#					self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#					self.client.sendBlock(x, y, z, block)
							#					var_position = target
							#					x,y,z = var_position
							#					block = chr(23)
							#					world[x, y, z] = block
							#					self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#					self.client.sendBlock(x, y, z, block)
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
									block = '\x00'
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									world[x, y+1, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
									self.client.sendBlock(x, y+1, z, block)
									var_position = (x,y-1,z)
									x,y,z = var_position
									block = chr(25)
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									block = chr(24)
									world[x, y+1, z] = block
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
									if closestdistance < 3:
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
												block = '\x00'
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												world[x, y+1, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
												self.client.sendBlock(x, y+1, z, block)
												var_position = target
												x,y,z = var_position
												block = chr(25)
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												block = chr(24)
												world[x, y+1, z] = block
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
													block = '\x00'
													world[x, y, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
													self.client.sendBlock(x, y, z, block)
													world[x, y+1, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
													self.client.sendBlock(x, y+1, z, block)
													var_position = target
													x,y,z = var_position
													block = chr(25)
													world[x, y, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
													self.client.sendBlock(x, y, z, block)
													block = chr(24)
													world[x, y+1, z] = block
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
										block = '\x0b'
										for i,j,k in explosionblocklist:
											for index in range(len(entitylist)):
												var_entity = entitylist[index]
												identity = var_entity[0]
												if identity != "tnt" and identity != "smoke":
													rx,ry,rz = var_entity[1]
													dx,dy,dz = (i+x,j+y,k+z)
													if (rx,ry,rz) == (dx,dy,dz) or (identity in twoblockhighentities and (rx,ry+1,rz) == (dx,dy,dz)):
														var_dellist.append(index)
											for user in clients:
												tx,ty,tz = (user.x >> 5,user.y >> 5,user.z >> 5)
												distance = ((tx-x)**2+(ty-y)**2+(tz-z)**2)**0.5
												if distance < 4:
													var_userkillist.append(user)
											ax,ay,az = (i+x,j+y,k+z)
											try:
												if world.blockstore.raw_blocks[world.blockstore.get_offset(ax,ay,az)] not in var_unbreakables:
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
											self.client.sendPlainWorldMessage("%s%s has died from TNT." % (COLOUR_DARKRED, user.username))
									if bombfinaldelay <=0:
										var_dellist.append(index)
										block = '\x00'
										for i,j,k in explosionblocklist:
											ax,ay,az = (i+x,j+y,k+z)
											try:
												if world.blockstore.raw_blocks[world.blockstore.get_offset(ax,ay,az)] not in var_unbreakables:
													world[ax,ay, az] = block
													self.client.queueTask(TASK_BLOCKSET, (ax, ay, az, block), world=world)
													self.client.sendBlock(ax, ay, az, block)
											except:
												pass
										world[x,y,z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
										entitylist.append(["smoke",(x,y,z),4,4,True])
										entitylist.append(["smoke",(x,y+2,z),4,4,True])
										entitylist.append(["smoke",(x,y+1,z+1),4,4,True])
										entitylist.append(["smoke",(x+1,y+1,z),4,4,True])
										entitylist.append(["smoke",(x+1,y-1,z),4,4,True])
										entitylist.append(["smoke",(x,y-1,z-1),4,4,True])
										entitylist.append(["smoke",(x,y-1,z+1),4,4,True])
									else:
										bombfinaldelay -= 1
								else:
									bombintialdelay -= 1
								entity[5] = bombintialdelay
								entity[6] = bombfinaldelay
							elif var_type == "person":
								x,y,z = var_position
								var_cango = True
								try:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
									if blocktocheck != 0:
										var_cango = False
								except:
									var_cango = False
								if var_cango:
									block = '\x00'
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									world[x, y+1, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
									self.client.sendBlock(x, y+1, z, block)
									var_position = (x,y-1,z)
									x,y,z = var_position
									block = chr(29)
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									block = chr(12)
									world[x, y+1, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
									self.client.sendBlock(x, y+1, z, block)
								else:
									target = [randint(-1,1) + x,y,randint(-1,1) + z]
									if target != [x,y,z]:
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
											block = '\x00'
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
											world[x, y+1, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
											self.client.sendBlock(x, y+1, z, block)
											var_position = target
											x,y,z = var_position
											block = chr(29)
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
											block = chr(12)
											world[x, y+1, z] = block
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
												block = '\x00'
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												world[x, y+1, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
												self.client.sendBlock(x, y+1, z, block)
												var_position = target
												x,y,z = var_position
												block = chr(29)
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												block = chr(12)
												world[x, y+1, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
												self.client.sendBlock(x, y+1, z, block)
							elif var_type == "noob":
								x,y,z = var_position
								var_cango = True
								try:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
									if blocktocheck != 0:
										var_cango = False
								except:
									var_cango = False
								if var_cango:
									block = '\x00'
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									world[x, y+1, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
									self.client.sendBlock(x, y+1, z, block)
									var_position = (x,y-1,z)
									x,y,z = var_position
									block = chr(29)
									world[x, y, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
									self.client.sendBlock(x, y, z, block)
									block = chr(12)
									world[x, y+1, z] = block
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
									if closestdistance < 3:
										closestclient.sendServerMessage("CAN I HAS OP PLOX?")
										
									i,k = closestposition
									distance = ((i-x)**2+(k-z)**2)**0.5
									if distance != 0 and distance > 2:
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
											block = '\x00'
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
											world[x, y+1, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
											self.client.sendBlock(x, y+1, z, block)
											var_position = target
											x,y,z = var_position
											block = chr(29)
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
											block = chr(12)
											world[x, y+1, z] = block
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
												block = '\x00'
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												world[x, y+1, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
												self.client.sendBlock(x, y+1, z, block)
												var_position = target
												x,y,z = var_position
												block = chr(29)
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												block = chr(12)
												world[x, y+1, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
												#self.client.sendBlock(x, y+1, z, block)
							elif var_type == "proxmine":
								x,y,z = var_position
								proxintialdelay = entity[4]
								if proxintialdelay <= 0:
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
									if closestdistance < 3:
										entitylist.append(["tnt",(x,y,z),1,1,True,0,5])
										var_dellist.append(index)
								else:
									proxintialdelay -= 1
									entity[4] = proxintialdelay
							elif var_type == "var":
								x,y,z = var_position
								varblock,movementbehavior,nearbehavior = entity[5:]
								def checknearbehavior():
									if nearbehavior == "kill":
										if closestdistance < 2:
											sx,sy,sz,sh = world.spawn
											closestclient.teleportTo(sx,sy,sz,sh)
											self.client.sendPlainWorldMessage("%s%s has died from a Mob." % (COLOUR_DARKRED, closestclient.username))
									elif nearbehavior == "explode":
										if closestdistance < 3:
											entitylist.append(["tnt",(x,y,z),1,1,True,0,5])
											var_dellist.append(index)
								if movementbehavior == "follow":
									var_cango = True
									try:
										blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
										if blocktocheck != 0:
											var_cango = False
									except:
										var_cango = False
									if var_cango:
										block = '\x00'
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
										var_position = (x,y-1,z)
										x,y,z = var_position
										block = chr(varblock)
										world[x, y, z] = block
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
										checknearbehavior()
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
												block = '\x00'
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												var_position = target
												x,y,z = var_position
												block = chr(varblock)
												world[x, y, z] = block
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
													block = '\x00'
													world[x, y, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
													self.client.sendBlock(x, y, z, block)
													var_position = target
													x,y,z = var_position
													block = chr(varblock)
													world[x, y, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
													self.client.sendBlock(x, y, z, block)
								elif movementbehavior == "engulf":
									var_cango = True
									try:
										blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
										if blocktocheck != 0:
											var_cango = False
									except:
										var_cango = False
									if var_cango:
										block = '\x00'
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
										var_position = (x,y-1,z)
										x,y,z = var_position
										block = chr(varblock)
										world[x, y, z] = block
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
										checknearbehavior()
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
												block = '\x00'
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												var_position = target
												x,y,z = var_position
												block = chr(varblock)
												world[x, y, z] = block
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
													block = '\x00'
													world[x, y, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
													self.client.sendBlock(x, y, z, block)
													var_position = target
													x,y,z = var_position
													block = chr(varblock)
													world[x, y, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
													self.client.sendBlock(x, y, z, block)
								elif movementbehavior == "pet":
									var_cango = True
									try:
										blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
										if blocktocheck != 0:
											var_cango = False
									except:
										var_cango = False
									if var_cango:
										block = '\x00'
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
										var_position = (x,y-1,z)
										x,y,z = var_position
										block = chr(varblock)
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
									else:
										ownername = entity[4]
										ownerclient = self.client.factory.usernames[ownername]
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
											subdistance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
											if closestdistance == None:
												closestdistance = subdistance
												closestclient = client
												closestposition = (var_pos[0],var_pos[2])
											else:
												if subdistance < closestdistance:
													closestdistance = subdistance
													closestclient = client
													closestposition = (var_pos[0],var_pos[2])
										checknearbehavior()
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
													block = '\x00'
													world[x, y, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
													self.client.sendBlock(x, y, z, block)
													var_position = target
													x,y,z = var_position
													block = chr(varblock)
													world[x, y, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
													self.client.sendBlock(x, y, z, block)
													userpositionlist = []
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
														block = '\x00'
														world[x, y, z] = block
														self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
														self.client.sendBlock(x, y, z, block)
														var_position = target
														x,y,z = var_position
														block = chr(varblock)
														world[x, y, z] = block
														self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
														self.client.sendBlock(x, y, z, block)
								elif movementbehavior == "random":
									x,y,z = var_position
									var_cango = True
									try:
										blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y-1,z)])
										if blocktocheck != 0:
											var_cango = False
									except:
										var_cango = False
									if var_cango:
										block = '\x00'
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
										var_position = (x,y-1,z)
										x,y,z = var_position
										block = chr(varblock)
										world[x, y, z] = block
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
											subdistance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
											if closestdistance == None:
												closestdistance = subdistance
												closestclient = client
												closestposition = (var_pos[0],var_pos[2])
											else:
												if subdistance < closestdistance:
													closestdistance = subdistance
													closestclient = client
													closestposition = (var_pos[0],var_pos[2])
										checknearbehavior()
										target = [randint(-1,1) + x,y,randint(-1,1) + z]
										if target != [x,y,z]:
											i,j,k = target
											var_cango = True
											try:
												blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i,j,k)])
												if blocktocheck != 0:
													var_cango = False
											except:
												var_cango = False
											if var_cango:
												block = '\x00'
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
												var_position = target
												x,y,z = var_position
												block = chr(varblock)
												world[x, y, z] = block
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
													block = '\x00'
													world[x, y, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
													self.client.sendBlock(x, y, z, block)
													var_position = target
													x,y,z = var_position
													block = chr(varblock)
													world[x, y, z] = block
													self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
													self.client.sendBlock(x, y, z, block)
								elif movementbehavior == "none":
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
										subdistance = ((i-x)**2+(j-y)**2+(k-z)**2)**0.5
										if closestdistance == None:
											closestdistance = subdistance
											closestclient = client
											closestposition = (var_pos[0],var_pos[2])
										else:
											if subdistance < closestdistance:
												closestdistance = subdistance
												closestclient = client
												closestposition = (var_pos[0],var_pos[2])
									checknearbehavior()
							elif var_type == "spawner":
								if len(entitylist) <= maxentitiespermap:
									x,y,z = var_position
									randnum = randint(1,6)
									if randnum < 4:
										entitylist.append(["zombie",(x,y+1,z),8,8])
									elif randnum == 6:
										entitylist.append(["creeper",(x,y+1,z),8,8])
									else:
										entitylist.append(["blob",(x,y+1,z),8,8])
							elif var_type == "bckchngdetector":
								x,y,z = var_position
								if world.blockstore.raw_blocks[world.blockstore.get_offset(x,y+1,z)] != '\x14':
									block = chr(20)
									world[x, y+1, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
									self.client.sendBlock(x, y+1, z, block)
								for client in worldblockchangesdict:
									cx,cy,cz,var_timeofchange = worldblockchangesdict[client][0][:4]
									if (cx,cy,cz) == (x,y+1,z) and time()- var_timeofchange < 2:
										worldblockchangedellist.append(client)
										px,py,pz,ph,pp = worldblockchangesdict[client][1]
										client.sendServerMessage("your (x,y,z,h,p) is: " + str((px,py,pz,ph,pp)))
										h = math.radians(ph*360.0/256.0)
										p = math.radians(pp*360.0/256.0)
										rx,ry,rz = math.sin(h)*math.cos(p),-math.sin(p),-math.cos(h)*math.cos(p)
										client.sendServerMessage("you are facing the ray:")
										client.sendServerMessage(str((rx,ry,rz)))
										client.sendServerMessage("test: " + str(math.sqrt(math.pow(rx,2) + math.pow(ry,2) + math.pow(rz,2))))
							#elif var_type == "testbow":
							#	x,y,z = var_position
							#	if world.blockstore.raw_blocks[world.blockstore.get_offset(x,y+1,z)] != '\x14':
							#		block = '\x14'
							#		world[x, y+1, z] = block
							#		self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
							#		self.client.sendBlock(x, y+1, z, block)
							#	if entity[4] not in entities_childerenlist:
							#		for client in worldblockchangesdict:
							#			cx,cy,cz,var_timeofchange = worldblockchangesdict[client][0][:4]
							#			if (cx,cy,cz) == (x,y+1,z) and time()- var_timeofchange < 2:
							#				worldblockchangedellist.append(client)
							#				i = world.entities_childerenlist_index
							#				world.entities_childerenlist_index += 1
							#				entities_childerenlist.append(i)
							#				entity[4] = i
							#				px,py,pz,ph,pp = worldblockchangesdict[client][1]
							#				distancebetween = ((x-px)**2+(y+1-py)**2+(z-pz)**2)**0.5
							#				h = math.radians(ph*360.0/256.0)
							#				p = math.radians(pp*360.0/256.0)
							#				rx,ry,rz = math.sin(h)*math.cos(p),-math.sin(p),-math.cos(h)*math.cos(p)
							#				entitylist.append(["testarrow",(rx*distancebetween+rx+px,ry*distancebetween+ry+py,rz*distancebetween+rz+pz),2,2,(rx,ry,rz),i])
							#elif var_type == "testarrow":
							#	vx,vy,vz = entity[4]
							#	rx,ry,rz = var_position
							#	x,y,z = int(round(rx)),int(round(ry)),int(round(rz))
							#	rx,ry,rz = rx+vx,ry+vy,rz+vz
							#	var_position = rx,ry,rz
							#	cx,cy,cz = int(round(rx)),int(round(ry)),int(round(rz))
							#	var_cango = True
							#	try:
							#		blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(cx,cy,cz)])
							#		if blocktocheck != 0:
							#			var_cango = False
							#	except:
							#		var_cango = False
							#	if (x,y,z) != (cx,cy,cz):
							#		if var_cango:
							#			if world.blockstore.raw_blocks[world.blockstore.get_offset(x,y,z)] == "'":
							#				block = '\x00'
							#				world[x, y, z] = block
							#				self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#				self.client.sendBlock(x, y, z, block)
							#			x,y,z = cx,cy,cz
							#			block = "'"
							#			world[x, y, z] = block
							#			self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
							#			self.client.sendBlock(x, y, z, block)
							#		else:
							#			del entities_childerenlist[entities_childerenlist.index(entity[5])]
							#			var_dellist.append(index)
							elif var_type == "paintballgun":
								x,y,z = var_position
								if world.blockstore.raw_blocks[world.blockstore.get_offset(x,y+1,z)] != '\x14':
									block = '\x14'
									world[x, y+1, z] = block
									self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
									self.client.sendBlock(x, y+1, z, block)
								if entity[4] not in entities_childerenlist:
									for client in worldblockchangesdict:
										cx,cy,cz,var_timeofchange,userblock = worldblockchangesdict[client][0][:5]
										if (cx,cy,cz) == (x,y+1,z) and time()- var_timeofchange < 2:
											worldblockchangedellist.append(client)
											if userblock in colorblocks:
												i = world.entities_childerenlist_index
												world.entities_childerenlist_index += 1
												entities_childerenlist.append(i)
												entity[4] = i
												px,py,pz,ph,pp = worldblockchangesdict[client][1]
												distancebetween = ((x-px)**2+(y+1-py)**2+(z-pz)**2)**0.5
												h = math.radians(ph*360.0/256.0)
												p = math.radians(pp*360.0/256.0)
												rx,ry,rz = math.sin(h)*math.cos(p),-math.sin(p),-math.cos(h)*math.cos(p)
												entitylist.append(["paintball",(rx*distancebetween+rx+px,ry*distancebetween+ry+py,rz*distancebetween+rz+pz),2,2,(rx,ry,rz),i,userblock])
											else:
												client.sendServerMessage("Please select a color block to use this paintballgun")
							elif var_type == "paintball":
								vx,vy,vz = entity[4]
								rx,ry,rz = var_position
								x,y,z = int(round(rx)),int(round(ry)),int(round(rz))
								rx,ry,rz = rx+vx,ry+vy,rz+vz
								var_position = rx,ry,rz
								cx,cy,cz = int(round(rx)),int(round(ry)),int(round(rz))
								var_cango = True
								try:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(cx,cy,cz)])
									if blocktocheck != 0:
										var_cango = False
								except:
									var_cango = False
								if (x,y,z) != (cx,cy,cz):
									if var_cango:
										if world.blockstore.raw_blocks[world.blockstore.get_offset(x,y,z)] == '(':
											block = '\x00'
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
										x,y,z = cx,cy,cz
										block = chr(40)
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
									else:
										del entities_childerenlist[entities_childerenlist.index(entity[5])]
										var_dellist.append(index)
										if ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,y,z)]) in [0,40]:
											block = '\x00'
											world[x, y, z] = block
											self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
											self.client.sendBlock(x, y, z, block)
										x,y,z = cx,cy,cz
										block = chr(entity[6])
										try:
											if ord(world.blockstore.raw_blocks[world.blockstore.get_offset(cx,cy,cz)]) not in var_unpainablelist:
												world[x, y, z] = block
												self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
												self.client.sendBlock(x, y, z, block)
										except:
											pass
							elif var_type == "cannon":
								lx,ly,lz = x+n,y+m,z+o
								if world.blockstore.raw_blocks[world.blockstore.get_offset(lx,ly,lz)] != '1':
									block = '1'
									world[lx, ly, lz] = block
									self.client.queueTask(TASK_BLOCKSET, (lx, ly, lz, block), world=world)
									self.client.sendBlock(lx, ly, lz, block)
								for i,j,k in var_sensorblocksoffsets:
									ax,ay,az = x+i,y+j,z+k
									if world.blockstore.raw_blocks[world.blockstore.get_offset(ax,ay,az)] != '\x14':
										block = '\x14'
										world[ax, ay, az] = block
										self.client.queueTask(TASK_BLOCKSET, (ax, ay, az, block), world=world)
										self.client.sendBlock(ax, ay, az, block)
								
								for client in worldblockchangesdict:
									cx,cy,cz,var_timeofchange = worldblockchangesdict[client][0][:4]
									if (cx,cy,cz) == (lx,ly+1,lz) and time()- var_timeofchange < 2:
										if not entity[6]:
											blockset = worldblockchangesdict[client][0][5]
											if blockset == 46:
												worldblockchangedellist.append(client)
												block = '\x00'
												world[lx, ly+1, lz] = block
												self.client.queueTask(TASK_BLOCKSET, (lx, ly+1, lz, block), world=world)
												self.client.sendBlock(lx, ly+1, lz, block)
												client.sendServerMessage("Cannon loaded.")
												entity[6] = True
											else:
												worldblockchangedellist.append(client)
												client.sendServerMessage("Please load this cannon with tnt.")
									for i,j,k in var_sensorblocksoffsets:
										ax,ay,az = x+i,y+j,z+k
										if entity[4] not in entities_childerenlist:
											if (cx,cy,cz) == (ax,ay,az) and time()- var_timeofchange < 2:
												if entity[6]:
													entity[6] = False
													worldblockchangedellist.append(client)
													i = world.entities_childerenlist_index
													world.entities_childerenlist_index += 1
													entities_childerenlist.append(i)
													entity[4] = i
													px,py,pz,ph,pp = worldblockchangesdict[client][1]
													distancebetween = ((x+2*n-px)**2+(y+1-py)**2+(z+2*o-pz)**2)**0.5
													h = math.radians(ph*360.0/256.0)
													p = math.radians(pp*360.0/256.0)
													rx,ry,rz = math.sin(h)*math.cos(p),-math.sin(p),-math.cos(h)*math.cos(p)
													ix,iy,iz = int(round(rx*distancebetween+rx+px)),int(round(ry*distancebetween+ry+py)),int(round(rz*distancebetween+rz+pz))
													entitylist.append(["cannonball",(rx*distancebetween+2*rx+px,ry*distancebetween+2*ry+py,rz*distancebetween+2*rz+pz),2,2,[rx,ry,rz],i])
													entitylist.append(["smoke",(ix+1,iy,iz),4,4,True])
													entitylist.append(["smoke",(ix-1,iy,iz),4,4,True])
													entitylist.append(["smoke",(ix-1,iy+1,iz),4,4,True])
												else:
													client.sendServerMessage("Cannon is not loaded.")
													worldblockchangedellist.append(client)
							elif var_type == "cannonball":
								entity[4][1] = entity[4][1] - 0.02
								vx,vy,vz = entity[4]
								rx,ry,rz = var_position
								x,y,z = int(round(rx)),int(round(ry)),int(round(rz))
								rx,ry,rz = rx+vx,ry+vy,rz+vz
								var_position = rx,ry,rz
								cx,cy,cz = int(round(rx)),int(round(ry)),int(round(rz))
								var_cango = True
								try:
									blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(cx,cy,cz)])
									if blocktocheck != 0:
										var_cango = False
								except:
									var_cango = False
								if (x,y,z) != (cx,cy,cz):
									if var_cango:
										block = '\x00'
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
										x,y,z = cx,cy,cz
										block = '1'
										world[x, y, z] = block
										self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
										self.client.sendBlock(x, y, z, block)
									else:
										del entities_childerenlist[entities_childerenlist.index(entity[5])]
										var_dellist.append(index)
										entitylist.append(["tnt",(x,y,z),1,1,True,0,5])
					except:
						self.client.sendWorldMessage("Internal Server Error")
						exc_type, exc_value, exc_traceback = sys.exc_info()
						traceback.print_exception(exc_type, exc_value, exc_traceback)
						world.entitylist = []
						return
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
	def commandEntity(self, parts, fromloc, overriderank):
		"/entity entityname- Op\nAliases: mob\nCreates the specified entity."
		if len(parts) < 2:
			if self.var_entityselected == "None":
				self.client.sendServerMessage("Please enter an entity name (type /entities for a list)")
			else:
				self.var_entityselected = "None"
				self.client.sendServerMessage("Entity was deselected.")
		else:
			world = self.client.world
			entity = parts[1]
			if entity == "cloud":
				self.var_entityselected = "cloud"
			elif entity == "rain":
				self.var_entityselected = "rain"
			elif entity == "bird":
				self.var_entityselected = "bird"
			elif entity == "blob":
				self.var_entityselected = "blob"
			#elif entity == "entity1":
			#	self.var_entityselected = "entity1"
			#elif entity == "passiveblob":
			#	self.var_entityselected = "passiveblob"
			#elif entity == "petblob":
			#	self.var_entityselected = "petblob"
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
			elif entity == "aquabie":
				self.var_entityselected = "aquabie"
			#elif entity == "piranna":
			#	self.var_entityselected = "piranna"
			elif entity == "creeper":
				self.var_entityselected = "creeper"
			elif entity == "fish":
				self.var_entityselected = "fish"
			elif entity == "rainbowfish":
				self.var_entityselected = "rainbowfish"
			elif entity == "tnt":
				self.var_entityselected = "tnt"
			elif entity == "fastzombie":
				self.var_entityselected = "fastzombie"
			elif entity == "person":
				self.var_entityselected = "person"
			elif entity == "noob":
				self.var_entityselected = "noob"
			elif entity == "proxmine":
				self.var_entityselected = "proxmine"
			elif entity == "var":
				if len(parts) < 5:
					self.client.sendServerMessage("For this entity please use the following:")
					self.client.sendServerMessage("/entity var blocktype movementbehavior nearbehavior")
					self.client.sendServerMessage("Movement Behavior: follow, engulf, pet, random or none.")
					self.client.sendServerMessage("Near Behavior: kill, explode or none.")
					return
				else:
					if parts[2] == 0 or parts[2].lower() == "air" or parts[2].lower() == "blank" or parts[2].lower() == "clear":
						self.client.sendServerMessage("Sorry, no invisible entities are allowed.")
						return
					try:
						block = int(parts[2])
					except ValueError:
						try:
							block = globals()['BLOCK_%s' % parts[2].upper()]
						except KeyError:
							self.client.sendServerMessage("'%s' is not a valid block type." % parts[2])
							return
					validmovebehaviors = ["follow","engulf","pet","random","none"]
					movementbehavior = parts[3]
					if movementbehavior not in validmovebehaviors:
						self.client.sendServerMessage("'%s' is not a valid movementbehavior." % movementbehavior)
						return
					validnearbehaviors = ["kill","explode","none"]
					nearbehavior = parts[4]
					if nearbehavior not in validnearbehaviors:
						self.client.sendServerMessage("'%s' is not a valid nearbehavior." % nearbehavior)
						return
					self.var_entityselected = "var"
					self.var_entityparts = [block,movementbehavior,nearbehavior]
			elif entity == "spawner":
				self.var_entityselected = "spawner"
			elif entity == "bckchngdetector":
				self.var_entityselected = "bckchngdetector"
			#elif entity == "testbow":
			#	self.var_entityselected = "testbow"
			elif entity == "paintballgun":
				self.var_entityselected = "paintballgun"
			elif entity == "cannon":
				self.var_entityselected = "cannon"
			else:
				self.client.sendServerMessage("%s is not a valid entity." % entity)
				return
			self.client.sendServerMessage("Entity %s selected." % entity)
			self.client.sendServerMessage("To deselect just type /entity")

	@op_only
	def commandNumentities(self, parts, fromloc, overriderank):
		"/numentities - Op\nAliases: nummobs\nTells you the number of entities in the map"
		world = self.client.world
		entitylist = world.entitylist
		self.client.sendServerMessage(str(len(entitylist)))

	@op_only
	def commandEntityclear(self, parts, fromloc, overriderank):
		"/entityclear - Op\nAliases: mobclear\nClears the entities from the map"
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
				self.client.sendServerMessage("Entity not registered in entityblocklist.")
		self.client.world.entitylist = []
		self.client.sendWorldMessage("Entities cleared.")

	@op_only
	def commandEntities(self, parts, fromloc, overriderank):
		"/entities - Op\nAliases: mobs\nDisplays available entities"
		var_listofvalidentities = ["blob","jumpingshroom","trippyshroom","zombie","aquabie","fastzombie","creeper","tnt","person","proxmine","var","spawner","paintballgun","cannon","cloud","bird","slime","trippyflower","fish","rainbowfish","noob"]
		self.client.sendServerList(["Available entities:"] + var_listofvalidentities)
