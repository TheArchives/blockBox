#!/usr/bin/python2.6

import sys
if not sys.version_info[:2] == (2, 6):
	print "Python 2.6.x is required in order to run blockBox."
	exit(1)

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
