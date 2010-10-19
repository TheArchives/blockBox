# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import shutil
import os
import sys, subprocess
import traceback
from lib.twisted.internet import reactor
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class IsoImage(ProtocolPlugin):

	commands = {
		"isoimage": "commandIso",
	}

	@op_only
	def commandIso(self, parts, fromloc, overriderank):
		"/isoimage [1-4] - Op\nCreates and IsoImage of the current map."
		if len(parts) == 2:
			if str(parts[1]) in "1234":
				angle = parts[1]
			else:
				self.client.sendServerMessage('You must provide 1-4 for the angle.')
				return
		else:
			angle = 1
		world = self.client.world
		pathname = os.getcwd()
		savepath = pathname + "/data/isoimage/images/"
		mapname = world.basename.split("/")[1]
		mappath = pathname + "/mapdata/worlds/" + mapname
		try:
			os.chdir(pathname + "/data/isoimage/")
			if self.checkos == "Windows":
				os.system('java -Xms512M -Xmx1024M -cp minecraft-server.jar; OrigFormat save "%s" server_level.dat'%mappath)
				os.system('java -Xms128M -Xmx1024M -cp minecraft-server.jar;IsoCraft++.jar isocraft server_level.dat tileset.png output.png %s -1 -1 -1 -1 -1 -1 visible'%str(angle))
			else:
				os.system('java -Xms512M -Xmx1024M -cp minecraft-server.jar: OrigFormat save "%s" server_level.dat'%mappath)
				os.system('java -Xms128M -Xmx1024M -cp minecraft-server.jar:IsoCraft++.jar isocraft server_level.dat tileset.png output.png %s -1 -1 -1 -1 -1 -1 visible'%str(angle))
			shutil.move("output.png", "images/%s%s.png"%(mapname,str(angle)))
			os.chdir(pathname)
			self.client.sendServerMessage('Isoimage %s has been created.' %(mapname + str(angle) + ".png"))
		except Exception, e:
			self.client.sendSplitServerMessage(traceback.format_exc().replace("Traceback (most recent call last):", ""))
			self.client.sendSplitServerMessage("Internal Server Error - Traceback (Please report this to the Server Staff or the blockBox Team, see /about for contact info)")
			self.client.logger.error(traceback.format_exc())
			os.chdir(pathname)
