# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

for var_index in range(len(entitylist)):
	var_entity = entitylist[var_index]
	identity = var_entity[0]
	ownername = entity[4]
	ownerclient = self.client.factory.usernames[ownername]
	if ownername in worldusernamelist:
		x, y, z = (ownerclient.x >> 5,ownerclient.y >> 5,ownerclient.z >> 5)
		if identity != "Pfield" or "Forcefield":
			rx,ry,rz = var_entity[1]
			xd = rx-x
			yd = ry-y
			zd = rz-z
			distance = math.sqrt((xd*xd + yd*yd + zd*zd))
			if distance <= 3:
				var_dellist.append(var_index)
				block = 0
				self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
				self.client.sendBlock(rx, ry, rz, block)
	else:
		var_dellist.append(var_index)