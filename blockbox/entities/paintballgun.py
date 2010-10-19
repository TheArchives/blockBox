# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

if world.blockstore.raw_blocks[world.blockstore.get_offset(x,y+1,z)] != '\x14':
	block = '\x14'
	world[x, y+1, z] = block
	self.client.queueTask(TASK_BLOCKSET, (x, y+1, z, block), world=world)
	self.client.sendBlock(x, y+1, z, block)
if entity[4] not in entities_childerenlist:
	for client in worldblockchangesdict:
		cx,cy,cz,var_timeofchange,userblock = worldblockchangesdict[client][0][:5]
		if (cx,cy,cz) == (x,y+1,z) and time()- var_timeofchange < 2:
			worldblockchangedellist.append(client)
			if userblock in colorblocks:
				i = world.entities_childerenlist_index
				world.entities_childerenlist_index += 1
				entities_childerenlist.append(i)
				entity[4] = i
				px,py,pz,ph,pp = worldblockchangesdict[client][1]
				distancebetween = ((x-px)**2+(y+1-py)**2+(z-pz)**2)**0.5
				h = math.radians(ph*360.0/256.0)
				p = math.radians(pp*360.0/256.0)
				rx,ry,rz = math.sin(h)*math.cos(p),-math.sin(p),-math.cos(h)*math.cos(p)
				entitylist.append(["paintball",(rx*distancebetween+rx+px,ry*distancebetween+ry+py,rz*distancebetween+rz+pz),2,2,(rx,ry,rz),i,userblock])
			else:
				client.sendServerMessage("Please select a color block to use this paintballgun")
