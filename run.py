#!/usr/bin/python2.6
# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import time, sys

if "--run" not in sys.argv and sys.platform == "win32":
	# They did not use the start.bat. Boot them out
	print ("Please use the start.bat that comes with the blockBox package to run blockBox.")
	time.sleep(5)
	exit(1);

try:
	if sys.version_info[0] == (2): # Python 2.x?
		if not sys.version_info[:2] == (2, 6): # 2.6
			print ("ATTENTION: Do you need help with blockBox? http://blockbox.bradness.info/forum or #blockBox@irc.esper.net")
			if sys.version_info[:2] == (2, 5): # 2.5
				print ("WARNING: The blockBox team do not guantee that blockBox will work without bugs in Python 2.5, but if you have found any bugs please still report to the blockBox team. \nThank you for the effort.")
			elif sys.version_info[:2] == (2, 7): # 2.7
				print ("WARNING: The blockBox team do not guantee that blockBox will work without bugs in Python 2.7, but if you have found any bugs please still report to the blockBox team. \nThank you for the effort.")
			else: # 2.0-2.4
				try:
					print ("NOTICE: Sorry, but you need Python 2.6.x (Zope, Twisted and SimpleJSON) to run blockBox; http://www.python.org/download/releases/2.6.6/")
				except:
					print ("NOTICE: Sorry, but you need Python 2.6.x (Zope, Twisted and SimpleJSON) to run blockBox; http://www.python.org/download/releases/2.6.6/")
				finally:
					print ("blockBox will exit in 10 seconds.")
					time.sleep(10)
					exit(1);
	else: # Python 3.x or better
		print ("ATTENTION: Do you need help with blockBox? http://blockbox.bradness.info/forum or #blockBox@irc.esper.net")
		print ("NOTICE: Sorry, but blockBox does not support Python 3.x or better. Please use Python 2.6.x instead; http://www.python.org/download/releases/2.6.6/")
		print ("blockBox will exit in 10 seconds.")
		time.sleep(10)
		exit(1);
except: # Python 1.x doesn't have the version_info method
	# Oh dear they are still using Python 1.x
	print ("ATTENTION: Do you need help with blockBox? http://blockbox.bradness.info/forum or #blockBox@irc.esper.net")
	print ("NOTICE: Sorry, but blockBox does not support Python 3.x. Please use Python 2.6.x instead; http://www.python.org/download/releases/2.6.6/")
	print ("blockBox will exit in 10 seconds.")
	time.sleep(10)
	exit(1);

import logging
from logging.handlers import SMTPHandler
from ConfigParser import RawConfigParser as ConfigParser

from lib.twisted.internet import reactor

from blockbox.api import APIFactory
from blockbox.constants import *
from blockbox.logger import ColoredLogger
from blockbox.server import BlockBoxFactory

logging.basicConfig(
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
	level=("--debug" in sys.argv) and logging.DEBUG or logging.INFO,
	datefmt="%m/%d/%Y %H:%M:%S",
)

logger = logging.getLogger("blockBox")
logger.info("Starting up blockBox %s..." % VERSION)

factory = BlockBoxFactory()
api = APIFactory(factory)
reactor.listenTCP(factory.config.getint("network", "port"), factory)
reactor.listenTCP(factory.config.getint("network", "api_port"), api)

factory.create_if_not("logs/console/console.log")

rotate = logging.handlers.TimedRotatingFileHandler(
	filename="logs/console/console.log", when="H",
	interval=6, backupCount=14,
)
logging.root.addHandler(rotate)

if factory.use_email:
	if factory.conf_email.getboolean("email", "need_auth"):
		email = logging.handlers.SMTPHandler(
			(factory.conf_email.get("email", "host"),factory.conf_email.get("email", "port")),
			factory.conf_email.get("email", "from"),
			[factory.conf_email.get("email", "to")],
			factory.conf_email.get("email", "subject"),
			(factory.conf_email.get("email", "user"), factory.conf_email.get("email", "pass")),
		)
	else:
		email = logging.handlers.SMTPHandler(
			(factory.conf_email.get("email", "host"),factory.conf_email.get("email", "port")),
			factory.conf_email.get("email", "from"),
			[factory.conf_email.get("email", "to")],
			factory.conf_email.get("email", "subject"),
		)
	email.setLevel(logging.ERROR)
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