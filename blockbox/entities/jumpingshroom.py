# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

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
	block = "'"
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
		block = "'"
		world[x, y, z] = block
		self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
		self.client.sendBlock(x, y, z, block)
