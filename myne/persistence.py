from ConfigParser import RawConfigParser as ConfigParser
from twisted.internet import reactor

class PersistenceEngine(object):
	def __init__(self, username):
		self.ini = ConfigParser()
		self.ini.read("persist/%s.ini" % username.lower())
		self.fp = open("persist/%s.ini", "w")
		reactor.callLater(30, save)
	
	def string(self, section, name, default=None):
		if self.config.has_option(section, name):
			return self.config.get(self, name)
		return default
	
	def int(self, section, name, default=None):
		if self.config.has_option(section, name):
			return self.config.getint(self, name)
		return default
		
	def bool(self, section, name, default=None):
		if self.config.has_option(section, name):
			return self.config.getboolean(self, name)
		return default
	
	def set(self, section, name, value):
		self.config.set(section, name, str(value))
		self.write(self.fp)