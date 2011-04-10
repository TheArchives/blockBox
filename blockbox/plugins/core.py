# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import traceback

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class CorePlugin(ProtocolPlugin):
	"Core commands which handles plugin loading/unloading, etc."

	commands = {
		"pll": "commandPluginLoad",
		"plu": "commandPluginUnload",
		"plr": "commandPluginReload",
	}

	@config("rank", "admin")
	@only_string_command("plugin name")
	def commandPluginReload(self, plugin_name, fromloc, overriderank):
		"/plr plugin - Admin\nReloads the plugin."
		try:
			self.client.factory.unloadPlugin(plugin_name)
		except ValueError:
			self.client.sendServerMessage("Plugin '%s' was not loaded." % plugin_name)
		else:
			try:
				self.client.factory.loadPlugin(plugin_name)
			except ValueError:
				self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
			except ImportError:
				self.logger.error(traceback.format_exc())
				self.client.sendServerMessage("Error loading plugin '%s'." % plugin_name)
			else:
				self.client.sendServerMessage("Plugin '%s' reloaded." % plugin_name)

	@config("rank", "director")
	@only_string_command("plugin name")
	def commandPluginLoad(self, plugin_name, fromloc, overriderank):
		"/pll plugin - Director\nLoads the plugin."
		try:
			self.client.factory.loadPlugin(plugin_name)
		except ValueError:
			self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
		except ImportError:
			self.logger.error(traceback.format_exc())
			self.client.sendServerMessage("Error loading plugin '%s'." % plugin_name)
		else:
			self.client.sendServerMessage("Plugin '%s' loaded." % plugin_name)

	@config("rank", "director")
	@only_string_command("plugin name")
	def commandPluginUnload(self, plugin_name, fromloc, overriderank):
		"/plu plugin - Director\nUnloads the plugin."
		try:
			self.client.factory.unloadPlugin(plugin_name)
		except ValueError:
			self.client.sendServerMessage("Plugin '%s' was not loaded." % plugin_name)
		else:
			self.client.sendServerMessage("Plugin '%s' unloaded." % plugin_name)
