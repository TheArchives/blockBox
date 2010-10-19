# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

if ph >= 224 or ph < 32:
	var_orientation = 0
elif 32 <= ph < 96:
	var_orientation = 1
elif 96 <= ph < 160:
	var_orientation = 2
elif 160 <= ph < 224:
	var_orientation = 3
entitylist.append(["cannon",(x,y,z),8,8,None,var_orientation,False])
self.client.sendSplitServerMessage("This cannon was created, load it by placing tnt on the obsidian block.")
