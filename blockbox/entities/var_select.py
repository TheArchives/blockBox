# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

if len(parts) < 5:
	self.client.sendServerMessage("for the var entity please use the form")
	self.client.sendServerMessage("/entity var <blocktype> <movementbehavior> <nearbehavior>")
	self.client.sendServerMessage("for movementbehavior you can use follow,engulf,pet,random,none")
	self.client.sendServerMessage("for nearbehavior you can use kill,explode,none")
	var_continue = False
else:
	if parts[2] == 0 or parts[2].lower() == "air" or parts[2].lower() == "blank" or parts[2].lower() == "clear":
		self.client.sendServerMessage("sorry no invisible entities")
		var_continue = False
	if var_continue:
		try:
			block = int(parts[2])
		except ValueError:
			try:
				block = globals()['BLOCK_%s' % parts[2].upper()]
			except KeyError:
				self.client.sendServerMessage("'%s' is not a valid block type." % parts[2])
				var_continue = False
		if var_continue:
			validmovebehaviors = ["follow","engulf","pet","random","none"]
			movementbehavior = parts[3]
			if movementbehavior not in validmovebehaviors:
				self.client.sendServerMessage("'%s' is not a valid movementbehavior." % movementbehavior)
				var_continue = False
			if var_continue:
				validnearbehaviors = ["kill","explode","none"]
				nearbehavior = parts[4]
				if nearbehavior not in validnearbehaviors:
					self.client.sendServerMessage("'%s' is not a valid nearbehavior." % nearbehavior)
					var_continue = False
				if var_continue:
					self.var_entityselected = "var"
					self.var_entityparts = [block,movementbehavior,nearbehavior]
