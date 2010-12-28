# blockBox is Copyright 2009-2011 of the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import ctypes, logging, os, sys, time

from blockbox.constants import *

class ColoredLogger(logging.Logger):
	"Coloured Logger."
	def __init__(self, name, level=""):
		self.name = name
		if level == "critical" or level == 50:
			self.level = 50
		elif level == "error" or level == 40:
			self.level = 40
		elif level == "warning" or level == 30:
			self.level = 30
		elif level == "info" or level == 20:
			self.level = 20
		elif level == "debug" or level == 10:
			self.level = 10
		elif level == "notset" or level == 0:
			self.level = 0
		else:
			self.level = 20
		#self.handlers = list()

	if os.name == "nt": # Windows supports the codes directly
		STD_INPUT_HANDLE = -10
		STD_OUTPUT_HANDLE = -11
		STD_ERROR_HANDLE = -12
		SetConsoleTextAttribute = ctypes.windll.kernel32.SetConsoleTextAttribute
		GetConsoleScreenBufferInfo = ctypes.windll.kernel32.GetConsoleScreenBufferInfo
		GetStdHandle = ctypes.windll.kernel32.GetStdHandle
		def set_color(self, color):
			std_out_handle = self.GetStdHandle(self.STD_OUTPUT_HANDLE)
			color = int(color,16) # MC codes match windows... (coincidence?)
			bool = self.SetConsoleTextAttribute(std_out_handle, color)
			return bool
	else: # ANSI
		ctrl = chr(27)+"["
		cols = {
			"0":"0;30;0",
			"1":"0;34;0",
			"2":"0;32;0",
			"3":"0;36;0",
			"4":"0;31;0",
			"5":"0;35;0",
			"6":"0;33;0",
			"7":"0;37;0",
			"8":"0;30;1",
			"9":"0;34;1",
			"a":"0;32;1",
			"b":"0;36;1",
			"c":"0;31;1",
			"d":"0;35;1",
			"e":"0;33;1",
			"f":"0;37;1",
		}
		def set_color(self, color):
			self.col = self.cols[color]
			sys.stdout.write(self.ctrl+self.col+"m")

	def log(self, msg, color):
		msg = "&7"+time.strftime("%m/%d/%Y %H:%M:%S")+" %s - %s%s" % (self.name, color, msg)
		split = msg.split("&")
		for section in split:
			if section != "":
				col = section[0]
				if "0123456789abcdef".find(col) == -1:
					col = "f"
				self.set_color(col)
				msg = section[1:]
				sys.stdout.write(msg)
		sys.stdout.write("\n")
		msg2log = time.strftime("%m/%d/%Y %H:%M:%S")+" %s - %s" % (self.name, msg)

	def debug(self, msg):
		if self.level <= 10:
			self.log("DEBUG - " + msg , COLOUR_DARKGREEN)

	def info(self, msg):
		if self.level <= 20:
			self.log("INFO - " + msg , COLOUR_GREY)

	def warning(self, msg):
		if self.level <= 30:
			self.log("WARNING - " + msg , COLOUR_YELLOW)

	def error(self, msg):
		if self.level <= 40:
			self.log("ERROR - " + msg, COLOUR_DARKRED)

	def critical(self, msg):
		if self.level <= 50:
			self.log("CRITICAL - " + msg, COLOUR_RED)