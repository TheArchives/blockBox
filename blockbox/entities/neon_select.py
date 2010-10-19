# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

if len(parts) < 3:
	self.client.sendServerMessage("Please give a color(blue,red,white,green)")
	var_continue = False
if var_continue:
	color = parts[2]
	if color not in ["blue","red","white","green"]:
		self.client.sendServerMessage("%s is not a valid color for neon" % color)
		var_continue = False
	if var_continue:
		self.var_entityparts = [color]
		self.var_entityselected = "neon"
