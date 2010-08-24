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
