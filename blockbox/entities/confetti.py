# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

var_cango = True
i = randint(-1,1) + x
j = y - 1
k = randint(-1,1) + z
try:
	blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(i, j, k)])
	if blocktocheck != 0:
		var_cango = False
except:
	var_cango = False
if var_cango:
	block = 0
	self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
	self.client.sendBlock(x, y, z, block)
	block = randint(22,36)
	var_position = (i,j,k)
	x,y,z = var_position
	self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
	self.client.sendBlock(x, y, z, block)
else:
	block = 0
	self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
	self.client.sendBlock(x, y, z, block)
	var_dellist.append(index)
	
