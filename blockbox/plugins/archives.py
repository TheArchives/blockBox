# blockBox is Copyright 2009-2010 of the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import datetime

from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class ArchivesPlugin(ProtocolPlugin):
	commands = {
		"aname": "commandAname",
		"atime": "commandAtime",
		"aboot": "commandAboot",
	}
	def gotClient(self):
		self.selected_archive_name = None
		self.selected_archive = None
	def commandAname(self, parts, True, False):
		"/aname searchterm - Guest\nSelects an archive name, by part or all of the name."
		if len(parts) == 1:
			self.client.sendServerMessage("Please enter a search term")
		else:
			# See how many archives match
			searchterm = parts[1].lower()
			matches = [x for x in self.client.factory.archives if searchterm in x.lower()]
			if len(matches) == 0:
				self.client.sendServerMessage("No matches for '%s'" % searchterm)
			elif len(matches) == 1:
				self.client.sendServerMessage("Selected '%s'." % matches[0])
				self.selected_archive_name = matches[0]
			else:
				self.client.sendServerMessage("%s matches! Be more specific." % len(matches))
				for match in matches[:3]:
					self.client.sendServerMessage(match)
				if len(matches) > 3:
					self.client.sendServerMessage("..and %s more." % (len(matches) - 3))
	def commandAtime(self, parts, True, False):
		"/atime yyyy/mm/dd hh_mm - Guest\nSelects the archive time to get"
		if len(parts) == 2:
			# Hackish. So sue me.
			if parts[1].lower() == "newest":
				parts[1] = "2020/1/1"
				parts.append("00_00")
			elif parts[1].lower() == "oldest":
				parts[1] = "1970/1/1"
				parts.append("00_00")
		if len(parts) < 3:
			self.client.sendServerMessage("Please enter a date and time.")
		elif not self.selected_archive_name or self.selected_archive_name not in self.client.factory.archives:
			self.client.sendServerMessage("Please select an archive name first. (/aname)")
		else:
			try:
				when = datetime.datetime.strptime(parts[1] + " " + parts[2], "%Y/%m/%d %H_%M")
			except ValueError:
				self.client.sendServerMessage("Please use the format yyyy/mm/dd hh_mm")
			else:
				# Pick the closest time
				times = []
				for awhen, filename in self.client.factory.archives[self.selected_archive_name].items():
					dt = when - awhen
					secs = abs(dt.seconds + (dt.days * 86400))
					times.append((secs, awhen, filename))
				times.sort()
				self.selected_archive = times[0][2]
				self.client.sendServerMessage("Selected archive from %s" % times[0][1].strftime("%Y/%m/%d %H_%M"))
	def commandAboot(self, parts, True, False):
		"/aboot - Guest\nBoots an archive after you've done /aname and /atime"
		if not self.selected_archive:
			if not self.selected_archive_name:
				self.client.sendServerMessage("Please select an archive name first. (/aname)")
			else:
				self.client.sendServerMessage("Please select an archive time first. (/atime)")
		else:
			world_id = self.client.factory.loadArchive(self.selected_archive)
			self.client.factory.worlds[world_id].admin_blocks = False
			self.client.sendServerMessage("Archive loaded, as %s" % world_id)
			self.client.changeToWorld(world_id)