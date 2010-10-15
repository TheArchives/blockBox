# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import os
import shutil

from lib.twisted.internet import reactor

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class BackupPlugin(ProtocolPlugin):

	commands = {
	"backup": "commandBackup",
	"backups": "commandBackups",
	"restore": "commandRestore",
	}

	@world_list
	@op_only
	def commandBackup(self, parts, fromloc, overriderank):
		"/backup worldname - Op\nMakes a backup copy of the map of the map."
		if len(parts) == 1:
			parts.append(self.client.world.basename.lstrip("mapdata/worlds"))
		world_id = parts[1]
		world_dir = ("mapdata/worlds/%s/" % world_id)
		if not os.path.exists(world_dir):
		   self.client.sendServerMessage("World %s does not exist." % (world_id))
		else:
			if not os.path.exists(world_dir+"backup/"):
				os.mkdir(world_dir+"backup/")
			folders = os.listdir(world_dir+"backup/")
			if len(parts) > 2:
				path = os.path.join(world_dir+"backup/", parts[2])
				if os.path.exists(path):
					self.client.sendServerMessage("Backup %s already exists. Pick a different name." % parts[2])
					return
			else:
				backups = list([])
				for x in folders:
					if x.isdigit():
						backups.append(x)
				backups.sort(lambda x, y: int(x) - int(y))
				path = os.path.join(world_dir+"backup/", "0")
				if backups:
					path = os.path.join(world_dir+"backup/", str(int(backups[-1])+1))
			os.mkdir(path)
			try:
				shutil.copy(world_dir + "blocks.gz", path)
			except:
				self.client.sendServerMessage("Something went wrong while backing up. Please try again.")
			if len(parts) > 2:
				self.client.sendServerMessage("Backup %s saved." % parts[2])
			else:
				try:
					self.client.sendServerMessage("Backup %s saved." % str(int(backups[-1])+1))
				except:
					self.client.sendServerMessage("Backup 0 saved.")

	@world_list
	@op_only
	def commandRestore(self, parts, fromloc, overriderank):
		"/restore worldname number - Op\nRestore map to indicated number."
		if len(parts) < 2:
			self.client.sendServerMessage("Please specify at least a world ID!")
		else:
			world_id = parts[1].lower()
			world_dir = ("mapdata/worlds/%s/" % world_id)
			if len(parts) < 3:
				try:
					backups = os.listdir(world_dir+"backup/")
				except:
					self.client.sendServerMessage("Syntax: /restore worldname number")
					return
				backups.sort(lambda x, y: int(x) - int(y))
				backup_number = str(int(backups[-1]))
			else:
				backup_number = parts[2]
			if not os.path.exists(world_dir+"backup/%s/" %backup_number):
				self.client.sendServerMessage("Backup %s does not exist." %backup_number)
			else:
				old_clients = self.client.factory.worlds[world_id].clients					
				if not os.path.exists(world_dir+"blocks.gz.new"):
					shutil.copy(world_dir+"backup/%s/blocks.gz" %backup_number,world_dir)
				else:
					reactor.callLater(1, self.commandRestore(self, parts, overriderank))
				self.client.factory.loadWorld("mapdata/worlds/%s" % world_id, world_id)
				self.client.sendServerMessage("%s has been restored to %s and booted." %(world_id,backup_number))
				self.client.factory.worlds[world_id].clients = old_clients
				for client in self.client.factory.worlds[world_id].clients:
					client.changeToWorld(world_id)

	@world_list
	@op_only
	def commandBackups(self, parts, fromloc, overriderank):
		"/backups - Op\nLists all backups this map has."
		try:
			world_dir = ("mapdata/worlds/%s/" % self.client.world.id)
			folders = os.listdir(world_dir+"backup/")
			Num_backups = list([])
			Name_backups = list([])
			for x in folders:
				if x.isdigit():
					Num_backups.append(x)
				else:
					Name_backups.append(x)
			Num_backups.sort(lambda x, y: int(x) - int(y))
			if Num_backups > 2:
				self.client.sendServerList(["Backups for %s:" % self.client.world.id] + [Num_backups[0] + "-" + Num_backups[-1]] + Name_backups)
			else:
				self.client.sendServerList(["Backups for %s:" % self.client.world.id] + Num_backups + Name_backups)
		except:
			self.client.sendServerMessage("Sorry, but there are no backups for %s." % self.client.world.id)
