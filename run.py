#!/usr/bin/python2.6
#	iCraft is Copyright 2010 both
#
#	The Archives team:
#				   <Adam Guy> adam@adam-guy.com AKA "Adam01"
#				   <Andrew Godwin> andrew@aeracode.org AKA "Aera"
#				   <Dylan Lukes> lukes.dylan@gmail.com AKA "revenant"
#				   <Gareth Coles> colesgareth2@hotmail.com AKA "gdude2002"
#
#	And,
#
#	The iCraft team:
#				   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#				   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#				   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#				   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#				   <James Kirslis> james@helplarge.com AKA "iKJames"
#				   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#				   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
#				   <Nick Tolrud> ntolrud@yahoo.com AKA "ntfwc"
#				   <Noel Benzinger> ronnygmod@gmail.com AKA "Dwarfy"
#				   <Randy Lyne> qcksilverdragon@gmail.com AKA "goober"
#				   <Willem van der Ploeg> willempieeploeg@live.nl AKA "willempiee"
#
#	iCraft is licensed under the Creative Commons
#	Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
#	To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#	Or, send a letter to Creative Commons, 171 2nd Street,
#	Suite 300, San Francisco, California, 94105, USA.

import sys
if not sys.version_info[:2] == (2, 6):
	print "Python 2.6.x is required in order to run blockBox."
	exit(1)

import logging
from myne.constants import *
from logging.handlers import SMTPHandler
from lib.twisted.internet import reactor
from myne.server import MyneFactory
from myne.api import APIFactory

logging.basicConfig(
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
	level=("--debug" in sys.argv) and logging.DEBUG or logging.INFO,
	datefmt="%m/%d/%Y %H:%M:%S",
)

logger = logging.getLogger("blockBox")
logger.info("Starting up blockBox %s..." % VERSION)

factory = MyneFactory()
api = APIFactory(factory)
reactor.listenTCP(factory.config.getint("network", "port"), factory)
reactor.listenTCP(factory.config.getint("network", "api_port"), api)

rotate = logging.handlers.TimedRotatingFileHandler(
	filename="logs/console/console.log", when="H",
	interval=6, backupCount=14,
)
logging.root.addHandler(rotate)

if factory.config.getboolean("email", "use_email"):
	if factory.config.getboolean("email", "need_auth"):
		email = logging.handlers.SMTPHandler(
			(factory.config.get("email", "host"),factory.config.get("email", "port")),
			factory.config.get("email", "from"),
			[factory.config.get("email", "to")],
			factory.config.get("email", "subject"),
			(factory.config.get("email", "user"), factory.config.get("email", "pass")),
		)
	else:
		email = logging.handlers.SMTPHandler(
			(factory.config.get("email", "host"),factory.config.get("email", "port")),
			factory.config.get("email", "from"),
			[factory.config.get("email", "to")],
			factory.config.get("email", "subject"),
		)
	emh.setLevel(logging.ERROR)
	logging.root.addHandler(email)

money_logger = logging.getLogger('TransactionLogger')
fh = logging.FileHandler('logs/server.log')
formatter = logging.Formatter("%(asctime)s: %(message)s")
fh.setFormatter(formatter)
#Add the handler
money_logger.addHandler(fh)

try:
	reactor.run()
finally:
	# Make sure worlds are flushed
	logger.info("Saving server meta...")
	factory.saveMeta()
	logger.info("Flushing worlds to disk...")
	for world in factory.worlds.values():
		logger.info("Saving: %s" % world.basename);
		world.stop()
		world.save_meta()
	logger.info("Done flushing...")
	logger.info("Thanks for using blockBox!")
	logger.info("Press enter to exit.")
	factory.console.stop = True
