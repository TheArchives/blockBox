# bloc# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

if len(entitylist) <= maxentitiespermap:
	x,y,z = var_position
	randnum = randint(1,6)
	if randnum < 4:
		entitylist.append(["zombie",(x,y+1,z),8,8])
	elif randnum == 6:
		entitylist.append(["creeper",(x,y+1,z),8,8])
	else:
		entitylist.append(["blob",(x,y+1,z),8,8])