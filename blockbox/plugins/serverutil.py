# blockBox is copyright 2009-2011 the Arc Team, the blockBox Team and other contributors.
# blockBox is licensed under the BSD 3-Clause Modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from lib.twisted.internet import reactor

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class ServerUtilPlugin(ProtocolPlugin):
    "Server Maintenance Tools and Commands."

    commands = {
        "srb": "commandSRB",
        "srs": "commandSRS",
        "u": "commandUrgent",
        "urgent": "commandUrgent",

        #"irc_cpr": "commandIRCReload",
        #"ircload": "commandIRCLoad",
        #"ircunload": "commandIRCUnload",

        "sendhb": "commandSendHeartbeat",
    }

    @config("rank", "director")
    def commandSRB(self, parts, fromloc, overriderank):
        "/srb [reason] - Director\nPrints out a reboot message."
        if len(parts) == 1:
            self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, ("[Server Reboot] Be back in a few.")))
        else:
            self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, ("[Server Reboot] Be back in a few: "+(" ".join(parts[1:])))))

    @config("rank", "director")
    def commandSRS(self, parts, fromloc, overriderank):
        "/srs [reason] - Director\nPrints out a shutdown message."
        if len(parts) == 1:
            self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, ("[Server Shutdown] See you later.")))
        else:
            self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, ("[Server Shutdown] See you later: "+(" ".join(parts[1:])))))

    @config("rank", "admin")
    def commandUrgent(self, parts, fromloc, overriderank):
        "/u message - Admin\nAliases: urgent\nPrints out message in the server color."
        if len(parts) == 1:
            self.client.sendServerMessage("Please type a message.")
        else:
            self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, "[URGENT] "+(" ".join(parts[1:]))))

    @config("rank", "admin")
    def commandIRCReload(self, parts, fromloc, overriderank):
        "/irc_cpr - Admin\nRehashes the IRC Bot."
        self.client.factory.irc_relay.disconnect()
        self.client.factory.irc_relay = None
        self.client.factory.irc_relay = ChatBotFactory(self.server)
        reactor.connectTCP(self.client.factory.conf_irc.get("irc", "server"), self.client.factory.conf_irc.getint("irc", "port"), self.client.factory.irc_relay)
        self.client.sendServerMessage("IRC Bot reloaded.")

    @config("rank", "admin")
    def commandIRCLoad(self, parts, fromloc, overriderank):
        "/icr_load - Admin\nLoads the IRC bot."
        if self.irc_relay:
            self.client.factory.sendServerMessage("IRC Bot already loaded. If it failed please use /irc_cpr!")
            return
        self.client.factory.irc_relay = ChatBotFactory(self.server)
        reactor.connectTCP(self.client.factory.conf_irc.get("irc", "server"), self.client.factory.conf_irc.getint("irc", "port"), self.client.factory.irc_relay)
        self.client.sendServerMessage("IRC Bot loaded.")

    @config("rank", "director")
    def commandIRCUnload(self, parts, fromloc, overriderank):
        "/irc_unload - Director\nUnloads the IRC bot."
        if not self.irc_relay:
            self.client.factory.sendServerMessage("IRC bot is not loaded.")
            return
        self.client.factory.irc_relay.disconnect()
        self.client.factory.irc_relay = None
        self.client.sendServerMessage("IRC Bot unloaded.")

    @config("rank", "owner")
    def commandSendHeartbeat(self, parts, fromloc, overriderank):
        "/sendhb - Owner\nSends a heartbeat to the official Minecraft server."
        self.client.factory.Heartbeat.get_url(onetime=True)
        self.client.sendServerMessage("Heartbeat sent.")