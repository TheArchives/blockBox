# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import struct
from constants import *

class Format(object):
	
	def __init__(self, format):
		self.format = format
	
	def __len__(self):
		length = 0
		for char in self.format:
			length += FORMAT_LENGTHS[char]
		return length
	
	def decode(self, data):
		for char in self.format:
			if char == "b":
				yield struct.unpack("!B", data[0])[0]
			elif char == "a":
				yield data[:1024]
			elif char == "s":
				yield data[:64].strip()
			elif char == "h":
				yield struct.unpack("!h", data[:2])[0]
			elif char == "i":
				yield struct.unpack("!i", data[:4])[0]
			data = data[FORMAT_LENGTHS[char]:]
	
	def encode(self, *args):
		assert len(self.format) == len(args)
		data = ""
		for char, arg in zip(self.format, args):
			if char == "a": # Array, 1024 long
				data += self.packString(arg[:1024], length=1024, packWith="\0")
			elif char == "s": # String, 64 long
				data += self.packString(arg[:64])
			elif char == "h": # Short
				data += struct.pack("!h", arg)
			elif char == "i": # Integer
				data += struct.pack("!i", arg)
			elif char == "b": # Byte
				if isinstance(arg, int):
					data += chr(arg)
				elif isinstance(arg, str):
					data += arg
				else:
					raise ValueError("Invalid value for byte: %r" % arg)
		return data
	
	def packString(self, string, length=64, packWith=" "):
		return string + (packWith*(length-len(string)))
