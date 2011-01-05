# blockBox is copyright 2009-2011 the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.plugins import ProtocolPlugin

class CorePlugin(ProtocolPlugin):	"Core commands which handles plugin loading/unloading, etc."
	commands = {
		"pll": "commandPluginload",
		"plu": "commandPluginunload",
		"plr": "commandPluginreload",
	}
	@admin_only
	@only_string_command("plugin name")
	def commandPluginreload(self, plugin_name, fromloc, overriderank):
		"/plr plugin - Admin\nReloads the plugin."
		try:
			self.client.factory.unloadPlugin(plugin_name)
			self.client.factory.loadPlugin(plugin_name)
		except ImportError:
			self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
		else:
			self.client.sendServerMessage("Plugin '%s' reloaded." % plugin_name)
	@director_only
	@only_string_command("plugin name")
	def commandPluginload(self, plugin_name, fromloc, overriderank):
		"/pll plugin - Director\nLoads the plugin."
		try:
			self.client.factory.loadPlugin(plugin_name)
		except ImportError:
			self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
		else:
			self.client.sendServerMessage("Plugin '%s' loaded." % plugin_name)
	@director_only
	@only_string_command("plugin name")
	def commandPluginunload(self, plugin_name, fromloc, overriderank):
		"/plu plugin - Director\nUnloads the plugin."
		try:
			self.client.factory.unloadPlugin(plugin_name)
		except:
			self.client.sendServerMessage("No such plugin '%s'." % plugin_name)
		else:
			self.client.sendServerMessage("Plugin '%s' unloaded." % plugin_name)
