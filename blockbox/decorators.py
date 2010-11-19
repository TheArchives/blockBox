# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

"""
Decorators for protocol (command) methods.
"""

def owner_only(func):
	"Decorator for owner-only command methods."
	func.owner_only = True
	return func

def director_only(func):
	"Decorator for director-only command methods."
	func.director_only = True
	return func

def admin_only(func):
	"Decorator for admin-only command methods."
	func.admin_only = True
	return func

def mod_only(func):
	"Decorator for mod-only command methods."
	func.mod_only = True
	return func

def advbuilder_only(func):
	"Decorator for advanced builder-only command methods."
	func.advbuilder_only = True
	return func

def member_only(func):
	"Decorator for advanced builder-only command methods."
	func.advbuilder_only = True
	return func

def worldowner_only(func):
	"Decorator for worldowner-only command methods."
	func.worldowner_only = True
	return func

def op_only(func):
	"Decorator for op-only command methods."
	func.op_only = True
	return func

def writer_only(func):
	"Decorator for builder-only command methods."
	func.writer_only = True
	return func

def build_list(func):
	"Decorator for build-list category methods."
	func.build_list = True
	return func

def world_list(func):
	"Decorator for world-list category methods."
	func.world_list = True
	return func

def player_list(func):
	"Decorator for player-list category methods."
	func.player_list = True
	return func

def info_list(func):
	"Decorator for info-list category methods."
	func.info_list = True
	return func

def username_command(func):
	"Decorator for commands that accept a single username parameter, and need a Client"
	def inner(self, parts, fromloc, overriderank):
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a username.")
		else:
			names = []
			user = parts[1].lower()
			for username in self.client.factory.usernames:
				if user in username:
					names.append(username)

			if len(names)==1:
				user = names[0]
			if not user in self.client.factory.usernames:
				self.client.sendServerMessage("No such Player '%s'" % user)
			else:
				if len(parts) > 2:
					try:
						func(self, self.client.factory.usernames[names[0]], fromloc, overriderank, parts[2:])
					except:
						self.client.sendServerMessage("You specificed too many arguments.")
				else:
					func(self, self.client.factory.usernames[names[0]], fromloc, overriderank)
	inner.__doc__ = func.__doc__
	return inner

def only_string_command(string_name):
	def only_inner(func):
		"Decorator for commands that accept a single username/plugin/etc parameter, and don't need it checked"
		def inner(self, parts, fromloc, overriderank):
			if len(parts) == 1:
				self.client.sendServerMessage("Please specify a %s." % string_name)
			else:
				username = parts[1].lower()
				if len(parts) > 2:
					func(self, username, fromloc, overriderank, parts[2:])
				else:
					func(self, username, fromloc, overriderank)
		inner.__doc__ = func.__doc__
		return inner
	return only_inner

only_username_command = only_string_command("username")

def username_world_command(func):
	"Decorator for commands that accept a single username parameter and possibly a world name."
	def inner(self, parts, fromloc, overriderank):
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a username.")
		else:
			username = parts[1].lower()
			if len(parts) == 3:
				try:
					world = self.client.factory.worlds[parts[2].lower()]
				except KeyError:
					self.client.sendServerMessage("Unknown world '%s'." % parts[2].lower())
					return
			else:
				world = self.client.world
			func(self, username, world, fromloc, overriderank)
	inner.__doc__ = func.__doc__
	return inner

def on_off_command(func):
	"Decorator for commands that accept a single on/off parameter"
	def inner(self, parts, fromloc, overriderank):
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify 'On' or 'Off'.")
		else:
			if parts[1].lower() not in ["on", "off"]:
				self.client.sendServerMessage("Use 'on' or 'off', not '%s'" % parts[1])
			else:
				func(self, parts[1].lower(), fromloc, overriderank)
	inner.__doc__ = func.__doc__
	return inner