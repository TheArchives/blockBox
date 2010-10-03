# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class ZonesPlugin(ProtocolPlugin):

	commands = {
		"znew": "commandNewZone",
		"rbox": "commandNewZone",
		"zone": "commandZone",
		"zones": "commandZones",
		"zlist": "commandListZones",
		"zshow": "commandZshow",
		"zremove": "commandDeZone",
		"zclear": "commandClearZone",
		"zdelall": "commandZdelall",
		"zwho": "commandZoneWho",
		"zrename": "commandRename",
	}

	@op_only
	@on_off_command
	def commandZones(self,onoff, byuser, overriderank):
		"/zones on|off - Op\nEnables or disables building zones in this world."
		if onoff == "on":
			if self.client.world.zoned:
				self.client.sendWorldMessage("Building zones is already on here.")
			else:
				self.client.world.zoned = True
				self.client.sendWorldMessage("This world now has building zones enabled.")
		else:
			if not self.client.world.zoned:
				self.client.sendWorldMessage("Building zones is already off here.")
			else:
				self.client.world.zoned = False
				self.client.sendWorldMessage("This world now has building zones disabled.")

	@op_only
	def commandNewZone(self, parts, byuser, overriderank):
		"/znew zonename user|rank [creator/rankname] - Op\nAliases: rbox\nCreates a new zone with the name you gave.\nUsers are added with /zone name player1 player2 ...\nRank Example: '/znew GuestArea rank all'\nUser Example: '/znew hotel1 user'. then '/zone hotel1 add <player1> <player2>'"
		parts = parts.lower()
		if len(parts) < 3:
			self.client.sendServerMessage("Info missing. Usage - /znew name user|rank [rank]")
			return
		try:
			if not self.client.world.zoned and not parts[3].lower() == "all":
				self.client.sendServerMessage("Zones must be turned on to use except for an 'all' ranked zone.")
				return
		except IndexError:
			if not self.client.world.zoned:
				self.client.sendServerMessage("Zones must be turned on to use except for an 'all' ranked zone.")
				return
		for id, zone in self.client.world.userzones.items():
			if zone[0] == parts[1]:
				self.client.sendServerMessage("Zone %s already exists. Pick a new name."%parts[1])
				return
		for id, zone in self.client.world.rankzones.items():
			if zone[0] == parts[1]:
				self.client.sendServerMessage("Zone %s already exists. Pick a new name."%parts[1])
				return
		try:
			x, y, z = self.client.last_block_changes[0]
			x2, y2, z2 = self.client.last_block_changes[1]
			world = self.client.world
			world[x, y, z]=chr(0)
			world[x2, y2, z2]= chr(0)
			self.client.queueTask(TASK_BLOCKSET, (x, y, z, chr(0)), world=world)
			self.client.queueTask(TASK_BLOCKSET, (x2, y2, z2, chr(0)), world=world)
		except IndexError:
			self.client.sendServerMessage("You have not clicked two corners yet.")
			return
		if x > x2:
			x, x2 = x2, x
		if y > y2:
			y, y2 = y2, y
		if z > z2:
			z, z2 = z2, z
		x-=1
		y-=1
		z-=1
		x2+=1
		y2+=1
		z2+=1
		if parts[2].lower()=="rank":
			if len(parts) < 4:
				self.client.sendServerMessage("Info missing. Usage - /znew name rank [rank]")
				return
			if parts[3].lower() == "all" or  parts[3].lower() == "builder" or  parts[3].lower() == "op" or  parts[3].lower() == "worldowner" or  parts[3].lower() == "mod" or  parts[3].lower() == "advbuilder" or  parts[3].lower() == "admin" or  parts[3].lower() == "director" or  parts[3].lower() == "owner":
				i=1
				while True:
					if not i in self.client.world.rankzones:
						self.client.world.rankzones[i] = parts[1].lower(), x, y, z, x2, y2, z2,parts[3].lower()
						break
					else:
						i+=1
				self.client.sendServerMessage("Zone %s for rank %s has been created."%(parts[1].lower(),parts[3].lower()))
			else:
				self.client.sendServerMessage("You must provide a proper rank.")
				self.client.sendServerMessage("all|builder|op|worldowner|advbuilder|mod|admin|director|owner")
				return
		elif parts[2].lower() == "user":
			i=1
			while True:
				if len(parts) == 4:
					owner = parts[3]
				else:
					owner = self.client.username

				if not i in self.client.world.userzones:
					self.client.world.userzones[i] = [parts[1].lower(), x, y, z, x2, y2, z2, owner]
					break
				else:
					i+=1

			self.client.sendServerMessage("User zone %s has been created."%parts[1].lower())
			self.client.sendServerMessage("Now use /zone name add|remove [player1 player2 ...]")
		else:
			self.client.sendServerMessage("You need to provide a zone type. (ie user or rank)")

	@op_only
	def commandZone(self,parts, byuser, overriderank):
		"/zone name - Op\nShows users assigned to this zone\n'/zone name add|remove [player1 player2 ...]' to edit users."
		parts = parts.lower()
		if len(parts)== 2:
			for id, zone in self.client.world.userzones.items():
				if zone[0] == parts[1]:
					try:
						self.client.sendServerMessage("Zone %s users: %s" %(zone[0],", ".join(map(str,zone[7:]))))
					except:
						self.client.sendServerMessage("There are no users assigned to %s." %(zone[0]))
					return
			self.client.sendServerMessage("There is no zone with that name")
		elif len(parts)> 3:
			if parts[2] == "add":
				for id, zone in self.client.world.userzones.items():
					if zone[0] == parts[1]:
						if self.client.username in zone[6:] or self.client.isAdmin() or self.client.world.owner == self.client.username:
							for user in parts[3:]:
								if not user.lower() in zone[6:]:
									self.client.world.userzones[id] += [user.lower()]
								else:
									self.client.sendServerMessage("%s is already assigned to %s."%(user.lower(),zone[0]))
									return
							self.client.sendServerMessage("Zone %s added user(s): %s." %(zone[0],", ".join(map(str,parts[3:]))))
							return
						else:
							self.client.sendSplitServerMessage("You are not a member of %s. You must be one of its users to add users." %zone[0])
							return
			if parts[2] == "remove":
				for id, zone in self.client.world.userzones.items():
					if zone[0] == parts[1]:
						if self.client.username in zone[6:] or self.client.isAdmin() or self.client.world.owner == self.client.username:
							for user in parts[3:]:
								try:
									self.client.world.userzones[id].remove(user.lower())
								except:
									self.client.sendServerMessage("User %s is not assigned to %s"%(user.lower(),zone[0]))
									return
							self.client.sendServerMessage("Zone %s removed user(s): %s" %(zone[0],", ".join(map(str,parts[3:]))))
							return
						else:
							self.client.sendSplitServerMessage("You are not a member of %s. You must be one of its users to remove users." %zone[0])
							return
			else:
				self.client.sendServerMessage("%s is an unknown command. Please try again."%parts[2])
		else:
			self.client.sendServerMessage("You must at least provide a zone name.")

	@op_only
	def commandDeZone(self, parts, byuser, overriderank):
		"/zremove name - Op\nRemoves a zone"
		parts = parts.lower()
		if len(parts)==2:
			match = False
			for id, zone in self.client.world.userzones.items():
				if zone[0] == parts[1]:
					if self.client.username in zone[6:] or self.client.isAdmin() or self.client.world.owner == self.client.username:
						match = True
						del self.client.world.userzones[id]
						self.client.sendServerMessage("%s has been removed."%zone[0])
						return
					else:
						self.client.sendSplitServerMessage("You are not a member of %s. You must be one of its users to remove it." %zone[0])
						return
			for id, zone in self.client.world.rankzones.items():
				if zone[0] == parts[1]:
					if zone[7] == "worldowner" and not self.client.isWorldOwner():
						self.client.sendServerMessage("You can not remove a zone higher then you")
						return
					if zone[7] == "mod" and not self.client.isMod():
						self.client.sendServerMessage("You can not remove a zone higher then you")
						return
					if zone[7] == "admin" and not self.client.isAdmin():
						self.client.sendServerMessage("You can not remove a zone higher then you")
						return			 
					if zone[7] == "director" and not self.client.isDirector():
						self.client.sendServerMessage("You can not remove a zone higher then you")
						return
					if zone[7] == "owner" and not self.client.isOwner():
						self.client.sendServerMessage("You can not remove a zone higher then you")
						return
					match = True
					del self.client.world.rankzones[id]
					self.client.sendServerMessage("%s has been removed."%zone[0])
					return
			if not match:
				self.client.sendServerMessage("There is not a zone with that name.")

		else:
			self.client.sendServerMessage("You must provide a zone name.")

	def commandListZones(self, parts, byuser, overriderank):
		"zlist - Guest\nLists all the zones on this map."
		self.client.sendServerList(["User Zones:"] + [zone[0] for id, zone in self.client.world.userzones.items()])
		self.client.sendServerList(["Rank Zones:"] + [zone[0] for id, zone in self.client.world.rankzones.items()])

	def commandZshow(self, parts, byuser, overriderank):
		"/zshow [all|name] - Guest\nOutlnes the zone in water temporary."
		parts = parts.lower()
		if not len(parts)==2:
			self.client.sendServerMessage("Please provide a zone to show")
			self.client.sendServerMessage("[or 'all' to show all zones]")
		elif parts[1].lower() == "all":
			match = False
			user = parts[1].lower()
			block = chr(globals()['BLOCK_STILLWATER'])
			for id,zone in self.client.world.userzones.items():
				x , y, z, x2, y2, z2 = zone[1:7]
				if x > x2:
					x, x2 = x2, x
				if y > y2:
					y, y2 = y2, y
				if z > z2:
					z, z2 = z2, z
				x+=1
				y+=1
				z+=1
				x2-=1
				y2-=1
				z2-=1
				for i in range(x, x2+1):
					self.client.sendPacked(TYPE_BLOCKSET, i, y, z, block)
					self.client.sendPacked(TYPE_BLOCKSET, i, y2, z, block)
					self.client.sendPacked(TYPE_BLOCKSET, i, y, z2, block)
					self.client.sendPacked(TYPE_BLOCKSET, i, y2, z2, block)
				for j in range(y, y2+1):
					self.client.sendPacked(TYPE_BLOCKSET, x, j, z, block)
					self.client.sendPacked(TYPE_BLOCKSET, x2, j, z, block)
					self.client.sendPacked(TYPE_BLOCKSET, x, j, z2, block)
					self.client.sendPacked(TYPE_BLOCKSET, x2, j, z2, block)
				for k in range(z, z2+1):
					self.client.sendPacked(TYPE_BLOCKSET, x, y, k, block)
					self.client.sendPacked(TYPE_BLOCKSET, x2, y, k, block)
					self.client.sendPacked(TYPE_BLOCKSET, x, y2, k, block)
					self.client.sendPacked(TYPE_BLOCKSET, x2, y2, k, block)
			for id,zone in self.client.world.rankzones.items():
				x , y, z, x2, y2, z2 = zone[1:7]
				if x > x2:
					x, x2 = x2, x
				if y > y2:
					y, y2 = y2, y
				if z > z2:
					z, z2 = z2, z
				x+=1
				y+=1
				z+=1
				x2-=1
				y2-=1
				z2-=1
				for i in range(x, x2+1):
					self.client.sendPacked(TYPE_BLOCKSET, i, y, z, block)
					self.client.sendPacked(TYPE_BLOCKSET, i, y2, z, block)
					self.client.sendPacked(TYPE_BLOCKSET, i, y, z2, block)
					self.client.sendPacked(TYPE_BLOCKSET, i, y2, z2, block)
				for j in range(y, y2+1):
					self.client.sendPacked(TYPE_BLOCKSET, x, j, z, block)
					self.client.sendPacked(TYPE_BLOCKSET, x2, j, z, block)
					self.client.sendPacked(TYPE_BLOCKSET, x, j, z2, block)
					self.client.sendPacked(TYPE_BLOCKSET, x2, j, z2, block)
				for k in range(z, z2+1):
					self.client.sendPacked(TYPE_BLOCKSET, x, y, k, block)
					self.client.sendPacked(TYPE_BLOCKSET, x2, y, k, block)
					self.client.sendPacked(TYPE_BLOCKSET, x, y2, k, block)
					self.client.sendPacked(TYPE_BLOCKSET, x2, y2, k, block)
			self.client.sendServerMessage("all zones in this map are showen temporarily by a water border.")
		else:
			match = False
			user = parts[1].lower()
			block = chr(globals()['BLOCK_STILLWATER'])
			for id,zone in self.client.world.userzones.items():
				if user == zone[0]:
					match=True
					x , y, z, x2, y2, z2 = zone[1:7]
					if x > x2:
						x, x2 = x2, x
					if y > y2:
						y, y2 = y2, y
					if z > z2:
						z, z2 = z2, z
					x+=1
					y+=1
					z+=1
					x2-=1
					y2-=1
					z2-=1
			if not match:
				for id,zone in self.client.world.rankzones.items():
					if user == zone[0]:
						match=True
						x , y, z, x2, y2, z2 = zone[1:7]
						if x > x2:
							x, x2 = x2, x
						if y > y2:
							y, y2 = y2, y
						if z > z2:
							z, z2 = z2, z
						x+=1
						y+=1
						z+=1
						x2-=1
						y2-=1
						z2-=1
			if match:
				def generate_changes():
					for i in range(x, x2+1):
						self.client.sendPacked(TYPE_BLOCKSET, i, y, z, block)
						self.client.sendPacked(TYPE_BLOCKSET, i, y2, z, block)
						self.client.sendPacked(TYPE_BLOCKSET, i, y, z2, block)
						self.client.sendPacked(TYPE_BLOCKSET, i, y2, z2, block)

					for j in range(y, y2+1):
						self.client.sendPacked(TYPE_BLOCKSET, x, j, z, block)
						self.client.sendPacked(TYPE_BLOCKSET, x2, j, z, block)
						self.client.sendPacked(TYPE_BLOCKSET, x, j, z2, block)
						self.client.sendPacked(TYPE_BLOCKSET, x2, j, z2, block)
					for k in range(z, z2+1):
						self.client.sendPacked(TYPE_BLOCKSET, x, y, k, block)
						self.client.sendPacked(TYPE_BLOCKSET, x2, y, k, block)
						self.client.sendPacked(TYPE_BLOCKSET, x, y2, k, block)
						self.client.sendPacked(TYPE_BLOCKSET, x2, y2, k, block)
					yield
				# Now, set up a loop delayed by the reactor
				block_iter = iter(generate_changes())
				def do_step():
					# Do 10 blocks
					try:
						for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
							block_iter.next()
						reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
					except StopIteration:
						pass
				do_step()
				self.client.sendServerMessage("%s is showing temporarily by a water border." % user)
			else:
				self.client.sendServerMessage("That zone does not exist.")

	@op_only
	def commandClearZone(self,parts, byuser, overriderank):
		"/zclear name - Op\nClears everything within the zone."
		parts = parts.lower()
		if not len(parts)==2:
			self.client.sendServerMessage("Please provide a zone to remove")
		else:
			match = False
			user = parts[1].lower()
			block = chr(globals()['BLOCK_AIR'])
			for id,zone in self.client.world.userzones.items():
				if user == zone[0]:
					if self.client.username in zone[6:] or self.client.isAdmin() or self.client.world.owner == self.client.username:
						match=True
						x , y, z, x2, y2, z2 = zone[1:7]
						if x > x2:
							x, x2 = x2, x
						if y > y2:
							y, y2 = y2, y
						if z > z2:
							z, z2 = z2, z
						x+=1
						y+=1
						z+=1
						x2-=1
						y2-=1
						z2-=1
					else:
						self.client.sendSplitServerMessage("You are not a member of %s. You must be one of its users to clear it." %zone[0])
						return
			if not match:
				for id,zone in self.client.world.rankzones.items():
					if user == zone[0]:
						if zone[7] == "advbuilder" and not self.client.isAdvBuilder():
							self.client.sendServerMessage("You can not remove a zone higher then you")
							return
						if zone[7] == "mod" and not self.client.isMod():
							self.client.sendServerMessage("You can not remove a zone higher then you")
							return
						if zone[7] == "admin" and not self.client.isAdmin():
							self.client.sendServerMessage("You can not remove a zone higher then you")
							return
						if zone[7] == "director" and not self.client.isDirector():
							self.client.sendServerMessage("You can not remove a zone higher then you")
							return
						if zone[7] == "owner" and not self.client.isOwner():
							self.client.sendServerMessage("You can not remove a zone higher then you")
							return
						match=True
						x , y, z, x2, y2, z2 = zone[1:7]
						if x > x2:
							x, x2 = x2, x
						if y > y2:
							y, y2 = y2, y
						if z > z2:
							z, z2 = z2, z
						x+=1
						y+=1
						z+=1
						x2-=1
						y2-=1
						z2-=1
			if match:
				world = self.client.world
				def generate_changes():
					for i in range(x, x2+1):
						for j in range(y, y2+1):
							for k in range(z, z2+1):
								try:
									world[i, j, k] = block
								except AssertionError:
									self.client.sendServerMessage("Really?! You got this error?")
									return
								self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
								self.client.sendBlock(i, j, k, block)
								yield
				# Now, set up a loop delayed by the reactor
				block_iter = iter(generate_changes())
				def do_step():
					# Do 10 blocks
					try:
						for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
							block_iter.next()
						reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
					except StopIteration:
						if byuser:
							count = ((1+(x2 - x)) * (1+(y2 - y)) * (1+(z2 - z))/3)
							self.client.finalizeMassCMD('zone clear', count)
						pass
				do_step()
			else:
				self.client.sendServerMessage("That zone does not exist.")

	def InZone(self,zone):
		x, y, z = self.client.last_block_changes[0]
		x1,y1,z1,x2,y2,z2 = zone[1:]
		if x1 < x < x2:
			if y1 < y < y2:
				if z1 < z < z2:
					return True
		return False

	@op_only
	def commandZdelall(self, parts, byuser, overriderank):
		"/zdelall - Op\nRemoves all zones in a map (if you can delete them)"
		parts = parts.lower()
		match = False
		for id, zone in self.client.world.userzones.items():
			if self.client.username in zone[6:] or self.client.isAdmin() or self.client.world.owner == self.client.username:
				del self.client.world.userzones[id]
			else:
				self.client.sendSplitServerMessage("You are not a member of %s. You must be one of its users to delete this zone." %zone[0])
				return
		self.client.sendServerMessage("userzones deleted")
		for id, zone in self.client.world.rankzones.items():
			try:
				if zone[7] == "worldowner" and not self.client.isWorldOwner():
					self.client.sendServerMessage("You can not remove a zone higher then you")
					return
				if zone[7] == "mod" and not self.client.isMod():
					self.client.sendServerMessage("You can not remove a zone higher then you")
					return
				if zone[7] == "admin" and not self.client.isAdmin():
					self.client.sendServerMessage("You can not remove a zone higher then you")
					return			 
				if zone[7] == "director" and not self.client.isDirector():
					self.client.sendServerMessage("You can not remove a zone higher then you")
					return
				if zone[7] == "owner" and not self.client.isOwner():
					self.client.sendServerMessage("You can not remove a zone higher then you")
					return
			except:
				pass
			del self.client.world.rankzones[id]
		self.client.sendServerMessage("All Rank Zones have been deleted.")

	@info_list
	@op_only
	def commandZoneWho(self, parts, byuser, overriderank):
		"/zwho - Op\nTells you whose zone you're currently in, if any."
		parts = parts.lower()
		x = self.client.x >> 5
		y = self.client.y >> 5
		z = self.client.z >> 5
		found = False
		for id, zone in self.client.world.userzones.items():
			x1,y1,z1,x2,y2,z2 = zone[1:7]
			if x1 < x < x2:
				if y1 < y < y2:
					if z1 < z < z2:
						self.client.sendServerMessage("User Zone: %s [%d]" % (zone[0], id))
						found = True
		for id, zone in self.client.world.rankzones.items():
			x1,y1,z1,x2,y2,z2 = zone[1:7]
			if x1 < x < x2:
				if y1 < y < y2:
					if z1 < z < z2:
						self.client.sendServerMessage("Rank Zone: %s [%d]" % (zone[0], id))
						found = True
		if not found:
			self.client.sendServerMessage("Zone is unclaimed!")


	@op_only
	def commandRename(self,parts, byuser, overriderank):
		"/zrename oldname newname - Op\nRenames a zone."
		parts = parts.lower()
		if not len(parts)==3:
			self.client.sendServerMessage("Please provide an old and new zone name.")
		else:
			oldname = parts[1].lower()
			newname = parts[2].lower()
			if oldname == newname:
				self.client.sendServerMessage("Old and new names are the same.")
			for id, zone in self.client.world.userzones.items():
				if zone[0] == newname:
					self.client.sendServerMessage("Zone %s already exists. Pick a new name."%newname)
					return
			for id, zone in self.client.world.rankzones.items():
				if zone[0] == newname:
					self.client.sendServerMessage("Zone %s already exists. Pick a new name."%newname)
					return

			for id,zone in self.client.world.userzones.items():
				if oldname == zone[0]:
					if self.client.username in zone[6:] or self.client.isAdmin() or self.client.world.owner == self.client.username:
						zone[0] = newname
						self.client.sendServerMessage("The zone %s has been renamed to %s" %(oldname,newname))
						return
					else:
						self.client.sendSplitServerMessage("You are not a member of %s. You must be one of its users to rename it." %zone[0])
						return
			for id,zone in self.client.world.rankzones.items():
				if oldname == zone[0]:
					if zone[7] == "member" and not self.client.isMember():
						self.client.sendServerMessage("You can not rename a zone higher then you")
						return
					if zone[7] == "mod" and not self.client.isMod():
						self.client.sendServerMessage("You can not rename a zone higher then you")
						return
					if zone[7] == "admin" and not self.client.isAdmin():
						self.client.sendServerMessage("You can not rename a zone higher then you")
						return
					if zone[7] == "director" and not self.client.isDirector():
						self.client.sendServerMessage("You can not rename a zone higher then you")
						return
					if zone[7] == "owner" and not self.client.isOwner():
						self.client.sendServerMessage("You can not rename a zone higher then you")
						return

					zone[0] = newname
					self.client.sendServerMessage("The zone %s has been renamed to %s" %(oldname,newname))
					return
			self.client.sendServerMessage("The zone '%s' doesnt exist." %oldname)