# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

color = self.var_entityparts[0]
colorlist = []
if color == "blue":
	c1,c2,c3,c4,c5 = ['\x1b', '\x1c', '\x1d', '#', '"']
if color == "red":
	c1,c2,c3,c4,c5 = ['\x15', '!', '\x1f', '#', '"']
if color == "white":
	c1,c2,c3,c4,c5 = ['$', '#', '#', '"', '"']
if color == "green":
	c1,c2,c3,c4,c5 = ['\x1a', '\x19', '\x19', '#', '"']
entitylist.append(["neon",(x,y,z),2,2,5,c1,c2,c3,c4,c5])
self.client.sendServerMessage("Neon has been created.")
