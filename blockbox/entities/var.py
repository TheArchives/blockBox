# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

varblock,movementbehavior,nearbehavior = entity[5:]
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
					
		if nearbehavior == "kill":
			if closestdistance < 2:
				sx,sy,sz,sh = world.spawn
				closestclient.teleportTo(sx,sy,sz,sh)
				self.client.sendWorldMessage("%s has died" % closestclient.username)
		elif nearbehavior == "explode":
			if closestdistance < 3:
				entitylist.append(["tnt",(x,y,z),1,1,True,0,5])
				var_dellist.append(index)
		
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

		if nearbehavior == "kill":
			if closestdistance < 2:
				sx,sy,sz,sh = world.spawn
				closestclient.teleportTo(sx,sy,sz,sh)
				self.client.sendWorldMessage("%s has died" % closestclient.username)
		elif nearbehavior == "explode":
			if closestdistance < 3:
				entitylist.append(["tnt",(x,y,z),1,1,True,0,5])
				var_dellist.append(index)
			
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
						
		if nearbehavior == "kill":
			if closestdistance < 2:
				sx,sy,sz,sh = world.spawn
				closestclient.teleportTo(sx,sy,sz,sh)
				self.client.sendWorldMessage("%s has died" % closestclient.username)
		elif nearbehavior == "explode":
			if closestdistance < 3:
				entitylist.append(["tnt",(x,y,z),1,1,True,0,5])
				var_dellist.append(index)
		
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
						
		if nearbehavior == "kill":
			if closestdistance < 2:
				sx,sy,sz,sh = world.spawn
				closestclient.teleportTo(sx,sy,sz,sh)
				self.client.sendWorldMessage("%s has died" % closestclient.username)
		elif nearbehavior == "explode":
			if closestdistance < 3:
				entitylist.append(["tnt",(x,y,z),1,1,True,0,5])
				var_dellist.append(index)
						
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
					
	if nearbehavior == "kill":
		if closestdistance < 2:
			sx,sy,sz,sh = world.spawn
			closestclient.teleportTo(sx,sy,sz,sh)
			self.client.sendWorldMessage("%s has died" % closestclient.username)
	elif nearbehavior == "explode":
		if closestdistance < 3:
			entitylist.append(["tnt",(x,y,z),1,1,True,0,5])
			var_dellist.append(index)
