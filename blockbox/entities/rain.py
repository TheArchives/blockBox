# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

x,y,z = var_position
i = x
j = -1 + y
k = z
var_cango = True
block = chr(0)
try:
	world[x, y, z] = block
except:
	world[x, y, z] = block
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
		world[x, y, z] = block
	self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
	self.client.sendBlock(x, y, z, block)
else:
	blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)])
	if blocktocheck != 0:
		var_cango = False
		var_dellist.append(index)
