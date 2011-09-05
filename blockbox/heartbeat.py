# blockBox is copyright 2009-2011 the Arc Team, the blockBox Team and other contributors.
# blockBox is licensed under the BSD 3-Clause Modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import logging, time, threading, traceback, urllib, urllib2
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
        self.hash = "na" # Another hacky way to fix a bug.
        if self.factory.config["send_heartbeat"]:
            self.turl()
        if self.factory.config["use_blockbeat"]:
            self.bb_turl()

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

    def get_url(self, noisy=False, onetime=False):
        try:
            try:
                self.factory.last_heartbeat = time.time()
                fh = urllib2.urlopen("http://www.minecraft.net/heartbeat.jsp", urllib.urlencode({
                "port": self.factory.conf_main.getint("network", "port"),
                "users": len(self.factory.clients),
                "max": self.factory.config["max_clients"],
                "name": self.factory.config["server_name"],
                "public": self.factory.config["public"],
                "version": 7,
                "salt": self.factory.config["salt"],
                }))
                self.url = fh.read().strip()
                if self.url.startswith("<html>"):
                    # Minecraft Server is unstable. throw out error and pass
                    self.logger.warning("Minecraft.net seems to be unstable. Heartbeat was not sent.")
                else:
                    self.hash = self.url.partition("server=")[2]
                    if noisy:
                        self.logger.info("%s" % self.url)
                    else:
                        self.logger.debug("%s" % self.url)
                    open('data/url.txt', 'w').write(self.url)
                if not self.factory.console.is_alive():
                    self.factory.console.run()
            except IOError, SystemExit:
                pass
            except:
                print (traceback.format_exc())
                self.logger.error("Minecraft.net seems to be offline.")
        except IOError, SystemExit:
            pass
        except:
            self.logger.error(traceback.format_exc())
        finally:
            if not onetime:
                reactor.callLater(60, self.turl)

    def bb_get_url(self, noisy=False, onetime=False):
        try:
            try:
                self.factory.last_heartbeat = time.time()
                fh = urllib2.urlopen("http://blockbeat.tk/heartbeat.php", urllib.urlencode({
                    "authkey": self.factory.config["blockbeat_authkey"],
                    "passphrase": self.factory.config["blockbeat_passphrase"],
                    "users": len(self.factory.clients),
                    "hash": self.hash,
                    "max": self.factory.config["max_clients"],
                    "port": self.factory.conf_main.getint("network", "port"),
                    "name": self.factory.config["server_name"],
                    "software": "blockbox",
                    "version": VERSION,
                    "gamemode": "classic",
                    "protocol": 7,
                    "public": self.factory.config["public"],
                    "motd": self.factory.config["server_message"],
                    "website": self.factory.config["info_url"],
                    "owner": self.factory.config["owner"],
                    "irc": (self.factory.config["irc_channel"]+"@"+self.factory.conf_irc.get("irc", "server") if self.factory.config["use_irc"] else ""),
                }))
                response = fh.read().strip()
                # Response handling
                if response == "ERR_CANNOT_CONNECT_TO_DATABASE_1" or response == "ERR_CANNOT_CONNECT_TO_DATABASE_2":
                    # Database error of blockBeat server
                    self.logger.warning("blockBeat seems to be unstable.")
                    pass
                elif response == "ERR_NOTHING_IS_SENT":
                    # Should never reach here
                    self.logger.error("blockBeat did not receive heartbeat information from server, please report this to the blockBox team.")
                    pass
                elif response == "ERR_CRITICAL_FAILED_TO_QUERY_ID_AFTER_HEARTBEAT":
                    # Could not query serverid after saving heartbeat. Sanity check, though it should never reach here
                    self.logger.error("blockBeat returned a critical unknown error, please report this to the blockBeat team.")
                    pass
                elif response == "ERR_NAME_EMPTY":
                    # Name is empty, should never reach here
                    self.logger.error("blockBeat did not receive server name properly, please report this to the blockBox team.")
                    pass
                elif response == "ERR_PORT_OUT_OF_RANGE":
                    # Port is out of range, should never reach here
                    self.logger.error("blockBeat did not receive port properly, please report this to the blockBox team.")
                    pass
                elif response == "ERR_PORT_EMPTY":
                    # Port is empty, should never reach here
                    self.logger.error("blockBeat did not receive port properly, please report this to the blockBox team.")
                    pass
                elif response == "ERR_OWNER_EMPTY":
                    # Owner is empty, should never reach here
                    self.logger.error("blockBeat did not receive server owner properly, please report this to the blockBox team.")
                    pass
                elif response == "ERR_GAMEMODE_EMPTY":
                    # Game mode is empty, should never reach here
                    self.logger.error("blockBeat did not receive server type properly, please report this to the blockBox team.")
                    pass
                elif response == "ERR_PROTOCOL_EMPTY":
                    # Protocol is empty, should never reach here
                    self.logger.error("blockBeat did not receive protocol version properly, please report this to the blockBeat team.")
                    pass
                elif response == "ERR_AUTH_FAILED_AUTHKEY_NOT_FOUND":
                    # Could not find authkey in auth database
                    self.logger.error("blockBeat could not find the authkey in the database. Please check if you have any typos in your authkey.")
                    pass
                elif response == "ERR_AUTH_FAILED_GAMEMODE_NOT_MATCH":
                    # Game mode does not match the authkey
                    self.logger.error("The authkey specified is for SMP servers, please get one for classic servers.")
                    pass
                elif response == "ERR_AUTH_FAILED_PASSPHRASE_NOT_MATCH":
                    # Passphrase does not match the authkey
                    self.logger.error("Passphrase specified was incorrect.")
                    pass
                elif response == "ERR_AUTH_FAILED_AUTHKEY_NOT_MATCH":
                    # Authkey specified does not match the authkey in database
                    self.logger.error("Authkey specified was incorrect.")
                    pass
                elif response == "ERR_UNABLE_TO_SAVE_HEARTBEAT_TO_DATABASE":
                    # Unable to save heartbeat in database
                    self.logger.error("blockBeat could not save heartbeat to database successfully, please report this to the blockBeat team.")
                    pass
                elif response == "ERR_LOG_FAILED":
                    # Unable to log this heartbeat
                    self.logger.error("blockBeat could not log this heartbeat to the database, please report this to the blockBeat team.")
                    pass
                elif response == "HEARTBEAT_RECEIVED":
                    # Heartbeat received
                    if noisy:
                        self.logger.info("Query to blockBeat successful.")
                    else:
                        self.logger.info("Query to blockBeat successful.")
                    pass
                else:
                    self.logger.error("blockBeat returned unknown error: %s" % response)
                    pass
                if not self.factory.console.is_alive():
                    self.factory.console.run()
            except IOError, SystemExit:
                pass
            except:
                self.logger.error(traceback.format_exc())
                self.logger.error("blockBeat seems to be offline.")
        except IOError, SystemExit:
            pass
        except:
            self.logger.error(traceback.format_exc())
        finally:
            if not onetime:
                reactor.callLater(60, self.bb_turl)
