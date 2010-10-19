# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

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
