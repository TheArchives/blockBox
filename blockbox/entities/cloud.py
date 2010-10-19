# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

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
	world[x, y, z] = block
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
		world[x, y, z] = block
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
	entitylist.append(["rain",(x,y-1,z),r,r])
