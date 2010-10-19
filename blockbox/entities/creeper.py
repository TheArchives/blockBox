# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

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
	closestposition = (0,0)
	closestdistance = None
	for entry in userpositionlist:
		var_pos = entry[1]
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
