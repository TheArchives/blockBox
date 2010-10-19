# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

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
	pass
if var_cango:
	block = 8
	self.client.queueTask(TASK_BLOCKSET, (x,y,z, block), world=world)
	self.client.sendBlock(x,y,z, block)
	if entity[6]:
		block = randint(22,36)
	else:
		block = 22
	self.client.queueTask(TASK_BLOCKSET, (x+l,y+m,z+n, block), world=world)
	self.client.sendBlock(x+l,y+m,z+n, block)
	var_position = (x+l,y+m,z+n)
	x,y,z = var_position
