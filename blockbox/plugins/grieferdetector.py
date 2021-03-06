# blockBox is copyright 2009-2011 the Arc Team, the blockBox Team and other contributors.
# blockBox is licensed under the BSD 3-Clause Modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import datetime, logging

from lib.twisted.internet import reactor

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class GreiferDetectorPlugin(ProtocolPlugin):
    """Class that provides possible griefer report."""

    hooks = {
        "blockchange": "blockChanged",
        "newworld": "newWorld",
    }

    def gotClient(self):
        self.var_blockchcount = 0
        self.in_publicworld = False

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        world = self.client.world
        if block is BLOCK_AIR and self.in_publicworld:
            if ord(world.blockstore.raw_blocks[world.blockstore.get_offset(x, y, z)]) != 3:
                worldname = world.id
                username = self.client.username
                def griefcheck():
                    if self.var_blockchcount >= 35:
                        self.client.factory.queue.put((self.client, TASK_STAFFMESSAGE, ("#%s%s: %s%s" % (COLOUR_DARKGREEN, 'SERVER', COLOUR_DARKGREEN, "ALERT! Possible Griefer behavior detected in"))))
                        self.client.factory.queue.put((self.client, TASK_STAFFMESSAGE, ("#%s%s: %s%s" % (COLOUR_DARKGREEN, 'SERVER', COLOUR_DARKGREEN, "'" + worldname + "'! Username: " + username))))
                        self.client.logger.info("%s was detected as a possible griefer in world %s." % (username, worldname))
                        self.client.adlog.write("%s | STAFF | %s was detected as a possible griefer in world %s.\n" % (datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M"), username, worldname))
                        self.client.adlog.flush()
                    self.var_blockchcount = 0
                if self.var_blockchcount == 0:
                    self.client.factory.loops["antigrief"] = reactor.callLater(5, griefcheck)
                self.var_blockchcount += 1

    def newWorld(self, world):
        "Hook to reset griefer blockcount abilities in new worlds if not op."
        if world.all_write == False:
            self.in_publicworld = False
            self.var_blockchcount = 0
        else:
            self.in_publicworld = True