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

import ctypes
import sys
import os
import time
from myne.constants import *

class ColoredLogger():
    def __init__(self, name):
        self.name = name
    if os.name == "nt": #windows supports the codes directly..
        STD_INPUT_HANDLE = -10
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12
        SetConsoleTextAttribute = ctypes.windll.kernel32.SetConsoleTextAttribute
        GetConsoleScreenBufferInfo = ctypes.windll.kernel32.GetConsoleScreenBufferInfo
        GetStdHandle = ctypes.windll.kernel32.GetStdHandle
        def set_color(self, color):
            std_out_handle = self.GetStdHandle(self.STD_OUTPUT_HANDLE)
            color = int(color,16) #mc codes match windows... (coincidence?)
            bool = self.SetConsoleTextAttribute(std_out_handle, color)
            return bool
    else: #ansi
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
        print time.strftime("%m/%d/%Y %I:%M:%S %p")
        msg = "&7["+time.strftime("%m/%d/%Y %I:%M:%S %p")+"] %s - %s%s&7" % (self.name, color, msg)
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
    
    def debug(self, msg):
        self.log("DEBUG - " + msg , COLOUR_DARKGREEN)
        
    def info(self, msg):
        self.log("INFO - " + msg , COLOUR_GREY)
        
    def warning(self, msg):
        self.log("WARNING - " + msg , COLOUR_YELLOW)
        
    def error(self, msg):
        self.log("ERROR - " + msg, COLOUR_DARKRED)
        
    def critical(self, msg):
        self.log("CRITICAL - " + msg, COLOUR_RED)
