# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

explosionblocklist = [[-3, -1, 0], [-3, 0, -1], [-3, 0, 0], [-3, 0, 1], [-3, 1, 0], [-2, -2, -1], [-2, -2, 0], [-2, -2, 1], [-2, -1, -2], [-2, -1, -1], [-2, -1, 0], [-2, -1, 1], [-2, -1, 2], [-2, 0, -2], [-2, 0, -1], [-2, 0, 0], [-2, 0, 1], [-2, 0, 2], [-2, 1, -2], [-2, 1, -1], [-2, 1, 0], [-2, 1, 1], [-2, 1, 2], [-2, 2, -1], [-2, 2, 0], [-2, 2, 1], [-1, -3, 0], [-1, -2, -2], [-1, -2, -1], [-1, -2, 0], [-1, -2, 1], [-1, -2, 2], [-1, -1, -2], [-1, -1, -1], [-1, -1, 0], [-1, -1, 1], [-1, -1, 2], [-1, 0, -3], [-1, 0, -2], [-1, 0, -1], [-1, 0, 0], [-1, 0, 1], [-1, 0, 2], [-1, 0, 3], [-1, 1, -2], [-1, 1, -1], [-1, 1, 0], [-1, 1, 1], [-1, 1, 2], [-1, 2, -2], [-1, 2, -1], [-1, 2, 0], [-1, 2, 1], [-1, 2, 2], [-1, 3, 0], [0, -3, -1], [0, -3, 0], [0, -3, 1], [0, -2, -2], [0, -2, -1], [0, -2, 0], [0, -2, 1], [0, -2, 2], [0, -1, -3], [0, -1, -2], [0, -1, -1], [0, -1, 0], [0, -1, 1], [0, -1, 2], [0, -1, 3], [0, 0, -3], [0, 0, -2], [0, 0, -1], [0, 0, 1], [0, 0, 2], [0, 0, 3], [0, 1, -3], [0, 1, -2], [0, 1, -1], [0, 1, 0], [0, 1, 1], [0, 1, 2], [0, 1, 3], [0, 2, -2], [0, 2, -1], [0, 2, 0], [0, 2, 1], [0, 2, 2], [0, 3, -1], [0, 3, 0], [0, 3, 1], [1, -3, 0], [1, -2, -2], [1, -2, -1], [1, -2, 0], [1, -2, 1], [1, -2, 2], [1, -1, -2], [1, -1, -1], [1, -1, 0], [1, -1, 1], [1, -1, 2], [1, 0, -3], [1, 0, -2], [1, 0, -1], [1, 0, 0], [1, 0, 1], [1, 0, 2], [1, 0, 3], [1, 1, -2], [1, 1, -1], [1, 1, 0], [1, 1, 1], [1, 1, 2], [1, 2, -2], [1, 2, -1], [1, 2, 0], [1, 2, 1], [1, 2, 2], [1, 3, 0], [2, -2, -1], [2, -2, 0], [2, -2, 1], [2, -1, -2], [2, -1, -1], [2, -1, 0], [2, -1, 1], [2, -1, 2], [2, 0, -2], [2, 0, -1], [2, 0, 0], [2, 0, 1], [2, 0, 2], [2, 1, -2], [2, 1, -1], [2, 1, 0], [2, 1, 1], [2, 1, 2], [2, 2, -1], [2, 2, 0], [2, 2, 1], [3, -1, 0], [3, 0, -1], [3, 0, 0], [3, 0, 1], [3, 1, 0]]
maxentitiystepsatonetime = 20
twoblockhighentities = ["creeper","zombie","noob","person"]
twoblockhighshootingentities = ["bckchngdetector","testbow","paintballgun"]
maxentitiespermap = 40
entityblocklist = {"zombie":[(0,0,0),(0,1,0)],"creeper":[(0,0,0),(0,1,0)],"person":[(0,0,0),(0,1,0)],"noob":[(0,0,0),(0,1,0)],"bckchngdetector":[(0,0,0),(0,1,0)],"testbow":[(0,0,0),(0,1,0)],"paintballgun":[(0,0,0),(0,1,0)]}
colorblocks = [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]
var_unpainablelist = [7,20,42,41,49,40,44,43,39,38,6,37,38]
var_unbreakables = ['\x07', '*', ')', '.', '1']
var_childrenentities = ["testarrow","paintball","cannonball"]
def getsuperbombtuple():
	var_list = []
	var_sublist2 = ()
	for radius in range(1,12):
		var_sublist = []
		for i in range(-radius-1, radius):
			for j in range(-radius-1, radius):
				for k in range(-radius-1, radius):
					if radius - 1 < (i**2 + j**2 + k**2)**0.5 + 0.691 < radius:
						if (i,j,k) not in var_sublist2:
							var_sublist.append((i,j,k))
						var_sublist2 = var_sublist
		var_sublist = tuple(var_sublist)
		var_list.append(var_sublist)
	var_list = tuple(var_list)
	return var_list
var_superbombtuple = getsuperbombtuple()
unselectableentities = ["testarrow","paintball","cannonball","bckchngdetector","entity1","passiveblob","petblob","smoke"]
