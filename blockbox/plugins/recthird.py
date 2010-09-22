
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *

class RecthirdPlugin(ProtocolPlugin):
	
	commands = {
		"recthird": "commandRecthird"
	}
	
	@build_list
	@writer_only
	def commandRecthird(self, parts, byuser, overriderank):
		"/recthird - Builder\nRecords a third block position."
		try:
			self.client.thirdcoord = self.client.last_block_changes[0]
		except IndexError:
					self.client.sendServerMessage("You have not clicked anywhere yet.")
					return
		self.client.sendServerMessage("The position has been recorded")
