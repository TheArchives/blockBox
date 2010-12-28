# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from collections import defaultdict

def Rank(self, parts, fromloc, overriderank, server=None):
	username = parts[2].lower()
	if server:
		factory = server
	else:
		factory = self.client.factory
	if parts[1] == "builder":
		if len(parts) > 3:
			try:
				world = factory.worlds[parts[3]]
			except KeyError:
				return ("Unknown world \"%s\"" %parts[3])
		else:
			if not server:
				world = self.client.world
			else:
				return "You must provide a world"
		#Make builder
		if not server:
			if not (self.client.username.lower() in world.ops or self.client.isMod() or self.client.isWorldOwner()) and not overriderank:
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				if not ((parts[-1]) in world.ops) or factory.isMod(parts[-1]):
					return ("You are not high enough rank!")
		world.writers.add(username)
		if username in factory.usernames:
			user = factory.usernames[username]
			if user.world == world:
				user.sendWriterUpdate()
		return ("%s is now a Builder" % username)
	elif parts[1] == "op":
		if len(parts) > 3:
			try:
				world = factory.worlds[parts[3]]
			except KeyError:
				return ("Unknown world \"%s\"" %parts[3])
		else:
			if not server:
				world = self.client.world
			else:
				return "You must provide a world"
		if not server:
			if self.client.isWorldOwner()==False and not overriderank:
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				return ("You are not high enough rank!")
		world.ops.add(username)
		return ("Opped %s" % username)
		#make op
	elif parts[1] == "worldowner":
		if len(parts) > 3:
			try:
				world = factory.worlds[parts[3]]
			except KeyError:
				return ("Unknown world \"%s\"" %parts[3])
		else:
			if not server:
				world = self.client.world
			else:
				return "You must provide a world"
		if not server:
			if not self.client.isMod() and not overriderank:
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				return ("You are not high enough rank!")
		world.owner = username
		return ("%s is now a world owner." % username)
	elif parts[1] == "advbuilder":
		#make them an advbuilder
		if not server:
			if not self.client.isMod():
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				if not factory.isMod(parts[-1]):
					return ("You are not high enough rank!")
		factory.advbuilders.add(username)
		if username in factory.usernames:
			factory.usernames[username].sendAdvBuilderUpdate()
		return ("%s is now an Advanced Builder." % username)
	elif parts[1] == "mod":
		#make them a mod
		if not server:
			if not self.client.isDirector():
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				if not factory.isDirector(parts[-1]):
					return ("You are not high enough rank!")
		factory.mods.add(username)
		if username in factory.usernames:
			factory.usernames[username].sendModUpdate()
		return ("%s is now a Mod." % username)
	elif parts[1] == "admin":
		#make them admin
		if not server:
			if not self.client.isDirector():
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				if not factory.isDirector(parts[-1]):
					return ("You are not high enough rank!")
		factory.admins.add(username)
		if username in factory.usernames:
			factory.usernames[username].sendAdminUpdate()
		return ("%s is now an admin." % username)
	elif parts[1] == "director":
		#make them director
		if not server:
			if not self.client.isOwner():
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				if not factory.isOwner(parts[-1]):
					return ("You are not high enough rank!")
		factory.directors.add(username)
		if username in factory.usernames:
			factory.usernames[username].sendDirectorUpdate()
		return ("%s is now an director." % username)
	else:
		return ("Unknown rank \"%s\""%parts[1])

def DeRank(self, parts, fromloc, overriderank, server=None):
	username = parts[2].lower()
	if server:
		factory = server
	else:
		factory = self.client.factory
	if parts[1] == "builder":
		if len(parts) > 3:
			try:
				world = factory.worlds[parts[3]]
			except KeyError:
				return ("Unknown world \"%s\"" %parts[3])
		else:
			if not server:
				world = self.client.world
			else:
				return "You must provide a world"
		#Make builder
		if not server:
			if not ((self.client.username in world.ops) or self.client.isMod()) and overriderank:
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				if not ((parts[-1]) in world.ops) or factory.isMod(parts[-1]):
					return ("You are not high enough rank!")
		try:
			world.writers.remove(username)
		except KeyError:
				return ("%s is not a Builder." % username)
		if username in factory.usernames:
			user = factory.usernames[username]
			if user.world == world:
				user.sendWriterUpdate()
		return ("Removed %s as Builder" % username)
	elif parts[1] == "op":
		if len(parts) > 3:
			try:
				world = factory.worlds[parts[3]]
			except KeyError:
				return ("Unknown world \"%s\"" %parts[3])
		else:
			if not server:
				world = self.client.world
			else:
				return "You must provide a world"
		if not server:
			if not self.client.isWorldOwner() and world != self.client.world:
				return ("You are not an World Owner!")
		else:
			if fromloc != "console":
				if not factory.isWorldOwner(parts[-1]):
					return ("You are not high enough rank!")
		try:
			world.ops.remove(username)
		except KeyError:
			return ("%s is not an op." % username)
		if username in factory.usernames:
			user = factory.usernames[username]
			if user.world == world:
				user.sendOpUpdate()
		return ("Deopped %s" % username)
		#make worldowner
	elif parts[1] == "worldowner":
		if len(parts) > 3:
			try:
				world = factory.worlds[parts[3]]
			except KeyError:
				return ("Unknown world \"%s\"" %parts[3])
		else:
			if not server:
				world = self.client.world
			else:
				return "You must provide a world"
		if not server:
			if not self.client.isWorldOwner() and world != self.client.world:
				return ("You are not an World Owner!")
		else:
			if fromloc != "console":
				if not factory.isWorldOwner(parts[-1]):
					return ("You are not high enough rank!")
		try:
			self.client.world.owner = ("")
		except KeyError:
			return ("%s is not a world owner." % username)
		if username in factory.usernames:
			user = factory.usernames[username]
			if user.world == world:
				user.sendWorldOwnerUpdate()
		return ("%s is no longer the world owner." % username)
		#make worldowner
	elif parts[1] == "advbuilder":
		#make them an advbuilder
		if not server:
			if not self.client.isMod():
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				if not factory.isMod(parts[-1]):
					return ("You are not high enough rank!")
		if username in factory.members:
			factory.members.remove(username)
		else:
			return ("No such member \"%s\"" % username.lower())
		if username in factory.usernames:
			factory.usernames[username].sendMemberUpdate()
		return ("%s is no longer a Member." % username.lower())
	elif parts[1] == "mod":
		#make them a mod
		if not server:
			if not self.client.isDirector():
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				if not factory.isDirector(parts[-1]):
					return ("You are not high enough rank!")
		if username in factory.mods:
			factory.mods.remove(username)
		else:
			return ("No such mod \"%s\"" % username.lower())
		if username in factory.usernames:
			factory.usernames[username].sendModUpdate()
		return ("%s is no longer a Mod." % username.lower())
	elif parts[1] == "admin":
		#make them admin
		if not server:
			if not self.client.isDirector():
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				if not factory.isDirector(parts[-1]):
					return ("You are not high enough rank!")
		if username in factory.admins:
			factory.admins.remove(username)
			if username in factory.usernames:
				factory.usernames[username].sendAdminUpdate()
			return ("%s is no longer an admin." % username.lower())
		else:
			return ("No such admin \"%s\""% username.lower())
	elif parts[1] == "director":
		#make them director
		if not server:
			if not self.client.isOwner():
				return ("You are not high enough rank!")
		else:
			if fromloc != "console":
				if not factory.isOwner(parts[-1]):
					return ("You are not high enough rank!")
		if username in factory.directors:
			factory.directors.remove(username)
			if username in factory.usernames:
				factory.usernames[username].sendDirectorUpdate()
			return ("%s is no longer an director." % username.lower())
		else:
			return ("No such director \"%s\""% username.lower())
	else:
		return ("Unknown rank \"%s\""%parts[1])

def Spec(self, username, fromloc, overriderank, server=None):
	if server:
		factory = server
	else:
		factory = self.client.factory
	if username in factory.mods:
		return ("You cannot make staff a spec!")
	factory.spectators.add(username)
	if username in factory.usernames:
		factory.usernames[username].sendSpectatorUpdate()
	return ("%s is now a spec." % username)

def Staff(self, server=None):
	Temp = []
	if server:
		factory = server
	else:
		factory = self.client.factory
	if len(factory.directors):
		Temp.append (["Directors:"] + list(factory.directors))
	if len(factory.admins):
		Temp.append (["Admins:"] + list(factory.admins))
	if len(factory.mods):
		Temp.append (["Mods:"] + list(factory.mods))
	return Temp

def Credits(self):
	Temp = []
	Temp.append ("Thanks to the following people for making blockBox possible...")
	Temp.append ("(a full list is available on the blockBox website, which can be found at blockbox.bradness.info)")
	Temp.append ("Mojang Specifications (Minecraft): Notch, dock, ez, ...")
	Temp.append ("Creators: aera (Myne), PixelEater (MyneCraft and blockBox), iKJames (iCraft)")
	#Temp.append ("Devs: Adam01, revenant, gdude2002, gothfox, AndrewPH, Varriount, erronjason, destroyerx1, ntfwc, Dwarfy, goober, willempiee")
	#Temp.append ("Others: Bidoof_King, Rils, fragmer, PyroPyro, TkTech, the Users, the Testers, the Modders, the Community, ...")
	Temp.append ("Devs: tyteen4a03, ntfwc, UberFoX")
	Temp.append ("Others: Ginger879, Gear3215")
	return Temp

def recursive_default():
	return defaultdict(recursive_default)