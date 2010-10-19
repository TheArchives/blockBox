# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

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
		world[x, y, z] = block
	self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
	self.client.sendBlock(x, y, z, block)
	var_position = (x,y-1,z)
	x,y,z = var_position
	block = chr(49)
	try:
		world[x, y, z] = block
	except:
		world[x, y, z] = block
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
					world[x, y, z] = block
				self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
				self.client.sendBlock(x, y, z, block)
				var_position = target
				x,y,z = var_position
				block = chr(49)
				try:
					world[x, y, z] = block
				except:
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
					block = chr(0)
					try:
						world[x, y, z] = block
					except:
						world[x, y, z] = block
					self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
					self.client.sendBlock(x, y, z, block)
					var_position = target
					x,y,z = var_position
					block = chr(49)
					try:
						world[x, y, z] = block
					except:
						world[x, y, z] = block
					self.client.queueTask(TASK_BLOCKSET, (x, y, z, block), world=world)
					self.client.sendBlock(x, y, z, block)
