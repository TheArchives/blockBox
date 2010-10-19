# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

for var_index in range(len(entitylist)):
	var_entity = entitylist[var_index]
	identity = var_entity[0]
	if identity != "Forcefield":
		rx,ry,rz = var_entity[1]
		xd = rx-x
	yd = ry-y
	zd = rz-z
	distance = math.sqrt((xd*xd + yd*yd + zd*zd))
		if distance <= 10:
			var_dellist.append(var_index)
			block = 0
			self.client.queueTask(TASK_BLOCKSET, (rx, ry, rz, block), world=world)
			self.client.sendBlock(rx, ry, rz, block)
