# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

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
	if closestdistance < 2:
		worldh = self.client.world.y
		for blockfree in range(y,self.client.world.y):
			blocktocheck = ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x,blockfree,z)])
			if blocktocheck == 0:
				entity[4] = blockfree+1
				break
		closestclient.teleportTo(x,entity[4],z)
		
		
		
		
		
		

