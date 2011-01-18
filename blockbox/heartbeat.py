# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import logging, time, threading, traceback, urllib
from ConfigParser import RawConfigParser as ConfigParser

from lib.twisted.internet import reactor

from blockbox.constants import *

class Heartbeat(object):
	"""
	Deals with registering with the Minecraft main server every so often.
	The Salt is also used to help verify users' identities.
	"""

	def __init__(self, factory):
		self.factory = factory
		self.logger = logging.getLogger("Heartbeat")
		if self.factory.conf_options.getboolean("heartbeat", "send_heartbeat"):
			self.turl()
#		if self.factory.conf_options.getboolean("heartbeat", "use_blockbeat"):
#			self.bb_turl()

	def bb_turl(self):
		try:
			threading.Thread(target=self.bb_get_url).start()
		except:
			self.logger.error(traceback.format_exc())
			reactor.callLater(1, self.bb_turl)

	def turl(self):
		try:
			threading.Thread(target=self.get_url).start()
		except:
			self.logger.error(traceback.format_exc())
			reactor.callLater(1, self.turl)

	def get_url(self, onetime=False):
		try:
			try:
				self.factory.last_heartbeat = time.time()
				fh = urllib.urlopen("http://www.minecraft.net/heartbeat.jsp", urllib.urlencode({
				"port": self.factory.config.getint("network", "port"),
				"users": len(self.factory.clients),
				"max": self.factory.max_clients,
				"name": self.factory.server_name,
				"public": self.factory.public,
				"version": 7,
				"salt": self.factory.salt,
				}))
				self.url = fh.read().strip()
				if self.url.startswith("<html>"):
					# Minecraft Server is unstable. throw out error and pass
					self.logger.warning("Minecraft.net seems to be unstable. Heartbeat was not sent.")
				else:
					self.hash = self.url.partition("server=")[2]
					if self.factory.console_delay == self.factory.delay_count:
						self.logger.debug("%s" % self.url)
					open('data/url.txt', 'w').write(self.url)
				if not self.factory.console.is_alive():
					self.factory.console.run()
			except IOError, SystemExit:
				pass
			except:
				self.logger.warning("Minecraft.net seems to be offline. Heartbeat was not sent.")
		except IOError, SystemExit:
			pass
		except:
			self.logger.error(traceback.format_exc())
		finally:
			if not onetime:
				reactor.callLater(60, self.turl)

	def bb_get_url(self):
		try:
			try:
				self.factory.last_heartbeat = time.time()
				fh = urllib.urlopen("http://blockbox.hk-diy.net/announce.php", urllib.urlencode({
					"users": len(self.factory.clients),
					"hash": self.hash,
					"max": self.factory.max_clients,
					"port": self.factory.config.getint("network", "port"),
					"name": self.factory.server_name,
					"software": "blockbox",
					"version": VERSION,
					"public": self.factory.public,
					"motd": self.factory.config.get("server", "description"),
					"website": self.factory.config.get("info", "info_url"),
					"owner": self.factory.config.get("info", "owner"),
					"irc": self.factory.config.get("irc", "channel")+"@"+self.factory.config.get("irc", "server"),
				}))
				self.response = fh.read().strip()
				#TODO: Response handling, more info coming soon
				#if self.response == 'ERROR_'
				if not self.factory.console.is_alive():
					self.factory.console.run()
			except IOError, SystemExit:
				pass
			except:
				self.logger.error(traceback.format_exc())
		except IOError, SystemExit:
			pass
		except:
			self.logger.error(traceback.format_exc())
		finally:
			if not onetime:
				reactor.callLater(60, self.bb_turl)