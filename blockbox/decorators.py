# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.globals import *

"""
Decorators for protocol (command) methods.
"""

def config(key, value):
	"Decorator that writes to the configuration of the command."
	def config_inner(func):
		if getattr(func, "config", None) is None:
			func.config = recursive_default()
		func.config[key] = value
		return func
	return config_inner

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

			if len(names) == 1:
				user = names[0]
			if not user in self.client.factory.usernames:
				self.client.sendServerMessage("No such player '%s'" % user)
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
				self.client.sendServerMessage("Please specify a/an %s." % string_name)
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