#    iCraft is Copyright 2010 both
#
#    The Archives team:
#                   <Adam Guy> adam@adam-guy.com AKA "Adam01"
#                   <Andrew Godwin> andrew@aeracode.org AKA "Aera"
#                   <Dylan Lukes> lukes.dylan@gmail.com AKA "revenant"
#                   <Gareth Coles> colesgareth2@hotmail.com AKA "gdude2002"
#
#    And,
#
#    The iCraft team:
#                   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#                   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#                   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#                   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#                   <James Kirslis> james@helplarge.com AKA "iKJames"
#                   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#                   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
#                   <Nick Tolrud> ntolrud@yahoo.com AKA "ntfwc"
#                   <Noel Benzinger> ronnygmod@gmail.com AKA "Dwarfy"
#                   <Randy Lyne> qcksilverdragon@gmail.com AKA "goober"
#                   <Willem van der Ploeg> willempieeploeg@live.nl AKA "willempiee"
#
#    iCraft is licensed under the Creative Commons
#    Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
#    To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#    Or, send a letter to Creative Commons, 171 2nd Street,
#    Suite 300, San Francisco, California, 94105, USA.

import sys
if not sys.version_info[:2] == (2, 6):
    print "Sorry, but you need Python 2.6.x to run iCraft 2"
    exit(1)

import os.path
import time

#!/usr/bin/python

import logging
import os,shutil
from myne.constants import *
from logging.handlers import SMTPHandler
from twisted.internet import reactor
from myne.server import MyneFactory
from myne.controller import ControllerFactory
def LogTimestamp():
    if os.path.exists("logs/console/console.log"):
        shutil.copy("logs/console/console.log", "logs/console/console" +time.strftime("%Y%m%d%H%M%S",time.localtime(time.time())) +".log")
        f=open("logs/console/console.log",'w')
        f.close()
    reactor.callLater(6*60*60, LogTimestamp)#24hours*60minutes*60seconds
LogTimestamp()
logging.basicConfig(
    format="%(asctime)s - %(levelname)7s - %(message)s",
    level=("--debug" in sys.argv) and logging.DEBUG or logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",  filename="logs/console/console.log",
)

# define a Handler which writes DEBUG messages or higher to the sys.stderr
console = logging.StreamHandler()
# set a format which is simpler for console use
formatter = logging.Formatter("%(asctime)s - %(levelname)7s - %(message)s")
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

logging.log(logging.INFO, "Starting up iCraft %s" % VERSION)
logging.log(logging.INFO, "Please don't forget to check for updates.")
logging.log(logging.INFO, "http://hlmc.net/ | irc.esper.net #iCraft")

factory = MyneFactory()
controller = ControllerFactory(factory)
reactor.listenTCP(factory.config.getint("network", "port"), factory)
reactor.listenTCP(factory.config.getint("network", "controller_port"), controller)
money_logger = logging.getLogger('TransactionLogger')
fh = logging.FileHandler('logs/server.log')
formatter = logging.Formatter("%(asctime)s: %(message)s")
fh.setFormatter(formatter)
#Add the handler
money_logger.addHandler(fh)

# Setup email handler
if factory.config.has_section("email"):
    emh = SMTPHandler(
        factory.config.get("email", "host"),
        factory.config.get("email", "from"),
        [factory.config.get("email", "to")],
        factory.config.get("email", "subject"),
    )
    emh.setLevel(logging.ERROR)
    logging.root.addHandler(emh)

try:
    reactor.run()
finally:
    # Make sure worlds are flushed
    logging.log(logging.INFO, "Saving server meta...")
    factory.saveMeta()
    logging.log(logging.INFO, "Flushing worlds to disk...")
    for world in factory.worlds.values():
        logging.log(logging.INFO, "Saving: %s" % world.basename);
        world.stop()
        world.save_meta()
    logging.log(logging.INFO, "Done flushing...")
    logging.log(logging.INFO, "Please don't forget to check for updates.")
    logging.log(logging.INFO, "http://hlmc.net/ | irc.esper.net #iCraft")
    if os.name is not "nt":
        sys.stdout.write(chr(27)+"[m")
    exit(1);
