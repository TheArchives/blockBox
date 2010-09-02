from ConfigParser import RawConfigParser as ConfigParser
from lib.twisted.internet import reactor

class PersistenceEngine(object):
	def __init__(self, username):
		self.username = username
		self.ini = ConfigParser()
		self.ini.read("persist/%s.ini" % username.lower())
	
	def string(self, section, name, default=None):
		try:
			ret = self.ini.get(section, name)
		except:
			if default is not None:
				self.set(section, name, default)
				ret = default
			else:
				ret = ""
		return ret
	
	def int(self, section, name, default=None):
		try:
			ret = self.ini.getint(section, name)
		except:
			if default is not None:
				self.set(section, name, default)
				ret = default
			else:
				ret = 0
		return ret
		
	def bool(self, section, name, default=None):
		try:
			ret = self.ini.getboolean(section, name)
		except:
			if default is not None:
				self.set(section, name, default)
				ret = default
			else:
				ret = False
		return ret
	
	def set(self, section, name, value):
		if not self.ini.has_section(section):
			self.ini.add_section(section)
		self.ini.set(section, name, str(value))
		with open("persist/%s.ini" % self.username.lower(), "w") as fp:
			self.ini.write(fp)
