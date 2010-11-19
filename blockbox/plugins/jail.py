# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from time import *
import cPickle

from lib.twisted.internet import reactor

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

# jail constants for jail.dat
J_USERS = 0
J_ZONE = 1
J_WORLD = 2

class JailPlugin(ProtocolPlugin):

	def loadJail(self):
		file = open('data/jail.dat', 'r')
		dic = cPickle.load(file)
		file.close()
		return dic

	def dumpJail(self, dic):
		file = open('data/jail.dat', 'w')
		cPickle.dump(dic, file)
		file.close()

	commands = {
		"jail": "commandJail",
		"free": "commandFree",
		"setjail": "commandSetJail",
		"prisoners": "commandPrisoners",
	}

	hooks = {
		"poschange": "posChanged",
		"playerjoined": "playerJoined",
		"newworld": "newWorld",
	}

	def gotClient(self):
		self.jailed = False
		self.jailed_until = -1
		self.jail_zone = ""
		self.jail_world = ""

	def prepJail(self):
		jail = self.loadJail()
		user = self.client.username.lower()
		changed = False

		if J_USERS not in jail:
			jail[J_USERS] = {}
			changed = True
		if J_ZONE not in jail:
			jail[J_ZONE] = ""
			changed = True
		if J_WORLD not in jail:
			jail[J_WORLD] = ""
			changed = True

		if user in jail[J_USERS]:
			self.jailed = True
			self.jailed_until = jail[J_USERS][user]
		else:
			self.jailed = False
			self.jailed_until = -1

		self.jail_world = jail[J_WORLD]
		self.jail_zone = jail[J_ZONE]

		if changed:
			self.dumpJail(jail)

	def playerJoined(self, user):
		self.prepJail()

	def newWorld(self, world):
		self.prepJail()

	def posChanged(self, x, y, z, h, p):
		"Hook trigger for when the player moves"
		rx = x >> 5
		ry = y >> 5
		rz = z >> 5
		
		if self.jailed:
			user = self.client.username.lower()
			injail = False

			if self.jail_world == "" or self.jail_zone == "":
				return

			if clock() >= self.jailed_until and self.jailed_until > 0:				
				self.client.sendWorldMessage("%s has served their sentence and is free." % user)
				self.jailed = False
				self.jailed_until = -1

				jail = self.loadJail()
				jail[J_USERS].pop(user)
				self.dumpJail(jail)

				self.client.changeToWorld(self.jail_world)
				return

			if self.client.world.id != self.jail_world:
				self.client.changeToWorld(self.jail_world)

			for id, zone in self.client.world.userzones.items():
				if zone[0] == self.jail_zone:
					x1, y1, z1, x2, y2, z2 = zone[1:7]
					found = True
					break

			for id, zone in self.client.world.rankzones.items():
				if zone[0] == self.jail_zone:
					x1, y1, z1, x2, y2, z2 = zone[1:7]
					found = True
					break

			if not found:
				jail = self.loadJail()
				jail[J_USERS][J_ZONE] = ""
				self.dumpJail(jail)
				return

			if x1 < rx < x2:
				if y1 < ry < y2:
					if z1 < rz < z2:
						injail = True

			if not injail:
				jx = int((x1 + x2) / 2)
				jy = int((y1 + y2) / 2)
				jz = int((z1 + z2) / 2)
				self.client.teleportTo(jx, jy, jz)

	@op_only
	def commandSetJail(self, parts, fromloc, overriderank):
		"/setjail zonename - Op\nSpecifies the jails zone name"

		if len(parts) != 2:
			self.client.sendServerMessage("Usage: /setjail zonename")
			return

		zonename = parts[1]
		exists = False
		
		for id, zone in self.client.world.userzones.items():
			if zone[0] == zonename:
				exists = True

		for id, zone in self.client.world.rankzones.items():
			if zone[0] == zonename:
				exists = True

		if not exists:
			self.client.sendServerMessage("Zone '%s' doesn't exist in this world!" % zonename)
			return

		self.prepJail()
		jail = self.loadJail()

		jail[J_ZONE] = zonename
		jail[J_WORLD] = self.client.world.id

		self.client.sendServerMessage("Set jail zone as '%s' in %s!" % (zonename, self.client.world.id))
		self.dumpJail(jail)

	@op_only
	def commandJail(self, parts, fromloc, overriderank):
		"/jail user [minutes] - Op\nPuts a user in jail\nYou can specify a time limit, or leave blank for permajail!"

		if len(parts) == 3:
			if not parts[2].isdigit():
				self.client.sendServerMessage("You must specify a positive numerical value for minutes!")
				return
			
			time = int(parts[2])
			seconds = int(parts[2]) * 60

		elif len(parts) == 2:
			seconds = 0
			time = 0
		else:
			self.client.sendServerMessage("Usage: /jail user [minutes]")
			return

		self.prepJail()
		jail = self.loadJail()
		found = False

		if jail[J_ZONE] == "":
			self.client.sendServerMessage("You must set a jail zone up first with /znew!")
			self.client.sendServerMessage("Use /setjail zone_name to set one up!")
			return

		names = []
		name = parts[1].lower()

		for id, zone in self.client.factory.worlds[self.jail_world].userzones.items():
			if zone[0] == self.jail_zone:
				x1, y1, z1, x2, y2, z2 = zone[1:7]
				found = True
				break

		for id, zone in self.client.factory.worlds[self.jail_world].rankzones.items():
			if zone[0] == self.jail_zone:
				x1, y1, z1, x2, y2, z2 = zone[1:7]
				found = True
				break

		if not found:
			self.client.sendServerMessage("Jail zone '%s' has been removed!" % jail[J_ZONE])
			self.client.sendServerMessage("Use /znew and /setjail zonename to set one up!")
			jail[J_ZONE] = ""
			self.dumpJail(jail)
			return

		if seconds == 0:
			jail[J_USERS][name] = 0
		else:
			jail[J_USERS][name] = int(clock() + seconds)

		self.dumpJail(jail)

		for username in self.client.factory.usernames:
			if name in username:
				names.append(username)

		if len(names) == 1:
			user = self.client.factory.usernames[names[0]]
			user.jailed = True

			jx = int((x1 + x2) / 2)
			jy = int((y1 + y2) / 2)
			jz = int((z1 + z2) / 2)
			
			user.changeToWorld(self.jail_world, position=(jx, jy, jz))

		if time == 1:
			jailtime = "for " + str(time) + " minute"
		elif time > 1:
			jailtime = "for " + str(time) + " minutes"
		else:
			jailtime = "indefinitely"

		self.client.sendWorldMessage("%s has been jailed %s." % (name, jailtime))

	@op_only
	def commandFree(self, parts, fromloc, overriderank):
		"/free username - Op\nLets a user out of jail"

		self.prepJail()
		jail = self.loadJail()

		names = []
		name = parts[1].lower()

		if name in jail[J_USERS]:
			jail[J_USERS].pop(name)
			self.dumpJail(jail)
		else:
			self.client.sendServerMessage("%s isn't jailed!" % name)
			return

		for username in self.client.factory.usernames:
			if name in username:
				names.append(username)

		if len(names) == 1:
			user = self.client.factory.usernames[names[0]]
			user.changeToWorld(jail[J_WORLD])

		self.client.sendWorldMessage("%s has been set free." % name)

	@op_only
	def commandPrisoners(self, parts, fromloc, overriderank):
		"/prisoners - Op\nLists prisoners and their sentences."

		self.prepJail()
		jail = self.loadJail()
		found = False

		self.client.sendServerMessage("Listing prisoners:")

		for name in jail[J_USERS]:
			if jail[J_USERS][name] > 1:
				remaining = int(jail[J_USERS][name] - clock())
				self.client.sendServerMessage("%s - %d seconds remaining" % (name, remaining))
			else:
				self.client.sendServerMessage("%s - Life" % name)

			found = True

		if not found:
			self.client.sendServerMessage("Currently no prisoners in jail.")
