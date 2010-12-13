# blockBox is Copyright 2009-2010 of the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import sys
import datetime
import os
import struct
from ConfigParser import SafeConfigParser as ConfigParser
import urllib
import urllib2
import cookielib
import re

from twisted.internet import reactor, protocol

from blockbox.protocol import MyneServerProtocol, TYPE_FORMATS
from blockbox.constants import *

class RipClient(MyneServerProtocol):
	"""Once connected, send a message, then print the result."""

	def connectionMade(self):
		print ("Identifying to server...")
		self.buffer = ""
		self.name = None
		self.gzipped = ""
		self.sendPacked(TYPE_INITIAL, 7, self.factory.username, self.factory.mppass, 0)

	def connectionLost(self, reason):
		pass

	def dataReceived(self, data):
		# First, add the data we got onto our internal buffer
		self.buffer += data
		# While there's still data there...
		while self.buffer:
			# Examine the first byte, to see what the command is
			type = ord(self.buffer[0])
			try:
				format = TYPE_FORMATS[type]
			except KeyError:
				self.transport.loseConnection()
			# See if we have all its data
			if len(self.buffer) - 1 < len(format):
				# Nope, wait a bit
				break
			# OK, decode the data
			parts = list(format.decode(self.buffer[1:]))
			self.buffer = self.buffer[len(format)+1:]
			if type == TYPE_INITIAL:
				protocol, name, desc, naff = parts
				print ("Server identifies as '%s'" % name)
				self.lolname = name.replace("/", "")
				self.name = self.lolname.replace(" ", "_")
		
			if type == TYPE_PRECHUNK:
				print ("Receiving level data...")
			elif type == TYPE_CHUNK:
				# Grab the chunked data
				length, chunk, progress = parts
				print ("...%i%%" % progress)
				self.gzipped += chunk[:length]
			elif type == TYPE_LEVELSIZE:
				# Store level size
				self.sx, self.sy, self.sz = parts
				print ("Done. Got %i bytes of level." % len(self.gzipped))
				print ("Level size (%s, %s, %s)" % (self.sx, self.sy, self.sz))
			elif type == TYPE_SPAWNPOINT and self.name:
				naff, nick, x, y, z, h, nafftoo = parts
				basename = "mapdata/archives/"+"/".join([self.name, datetime.datetime.utcnow().strftime("%Y-%m-%d_%H_%M")])
				#basename = basename.replace("/", "\\")
				try:
					os.makedirs(basename)
				except OSError:
					pass
				# Write out the blocks data
				fh = open(os.path.join(basename, "blocks.gz"), mode="wb")
				fh.write(self.gzipped)
				fh.close()
				# Write out meta info
				config = ConfigParser()
				x >>= 5
				y >>= 5
				z >>= 5
				h = int(h * (360/255.0))
				config.add_section("size")
				config.add_section("spawn")
				config.set("size", "x", str(self.sx))
				config.set("size", "y", str(self.sy))
				config.set("size", "z", str(self.sz))
				config.set("spawn", "x", str(x))
				config.set("spawn", "y", str(y))
				config.set("spawn", "z", str(z))
				config.set("spawn", "h", str(h))
				fp = open(os.path.join(basename, "world.meta"), "w")
				config.write(fp)
				fp.close()
				print ("Spawn point is at (%s, %s, %s, %s)" % (x, y, z, h))
				print ("Saved as %s." % fh.name)
				self.name = None
				self.transport.loseConnection()
			elif type == TYPE_ERROR:
				print ("Error! %s" % parts[0])
				self.transport.loseConnection()

class RipFactory(protocol.ClientFactory):
	protocol = RipClient

	def __init__(self, username, mppass):
		self.username = username
		self.mppass = mppass

	def clientConnectionFailed(self, connector, reason):
		print ("Connection failed.")
		reactor.stop()

	def clientConnectionLost(self, connector, reason):
		print ("Connection terminated.")
		reactor.stop()

# this connects the protocol to a server runing on port 8000
def rip(key, username, password):
	login_url = 'http://minecraft.net/login.jsp'
	play_url = 'http://minecraft.net/play.jsp?server=%s'
	cj = cookieCookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	login_data = urlurlencode({'username': username, 'password': password})
	print ("Logging in...")
	opener.open(login_url, login_data)
	print ("Fetching server info...")
	html = opener.open(play_url % key).read()
	ip = re.search(r'param name\="server" value="([0-9.]+)"', html).groups()[0]
	port = int(re.search(r'param name\="port" value="([0-9]+)"', html).groups()[0])
	mppass = re.search(r'param name\="mppass" value="([0-9a-zA-Z]+)"', html).groups()[0]
	print ("Got details. Connecting...")
	f = RipFactory(username, mppass)
	reactor.connectTCP(ip, port, f)
	reactor.run()

def main():
	config = ConfigParser()		try:
			config.read(os.path.join(os.path.dirname(__file__), "client.conf"))		except:			logger.error("You need to rename client.example.conf to client.conf")			exit(1);
	rip(sys.argv[1], config.get("client", "username"), config.get("client", "password"))

# this only runs if the module was *not* imported
if __name__ == '__main__':
	main()