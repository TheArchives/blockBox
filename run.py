#!/usr/bin/python2.6
# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import sys
if not sys.version_info[:2] == (2, 6):
	print "Python 2.6.x is required in order to run blockBox."
	sys.exit(1)

import logging
from blockbox.constants import *
from logging.handlers import SMTPHandler
from lib.twisted.internet import reactor
from blockbox.server import MyneFactory
from blockbox.api import APIFactory

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
