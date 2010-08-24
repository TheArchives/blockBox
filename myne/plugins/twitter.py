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

import sys
import urllib
from os import popen
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *

class TwitterPlugin(ProtocolPlugin):
    
    commands = {
        "tlog": "commandTlogin",
        "tdetails": "commandDetails",
        "tweet": "commandTweet",
    }

    tuser = ""
    tpass = ""
    twlog = open("logs/twitter.log", "a")

    @info_list
    def commandTlogin(self, parts, byuser, overriderank):
        "/tlog username password - Guest\nReplace username and password to login to Twitter."
        if not overriderank:
            try:
                if len(parts[1]) < 1:
                    self.client.sendServerMessage("Please input a username and password.")
                else:
                    self.tuser = str(parts[1])
                    if len(parts[2]) < 1:
                        self.client.sendServerMessage("Please input a username and password.")
                    else:
                        self.tpass = str(parts[2])
                        self.client.sendServerMessage("Username: "+COLOUR_RED+self.tuser)
                        self.client.sendServerMessage("Password: "+COLOUR_RED+self.tpass)
                        self.twlog.write(self.tuser+"("+self.client.username+")"+" Has logged into twitter.")
                        self.twlog.flush()
            except IndexError:
                self.client.sendServerMessage("Please input both a username and password.")
        else:
            self.client.sendServerMessage("You can't use twitter from a cmdblock!")

    @info_list
    def commandTweet(self, parts, byuser, overriderank):
        "/tweet tweet - Guest\nSend a tweet to Twitter after using /tlog."
        if not overriderank:
            if len(self.tuser) < 1:
                self.client.sendServerMessage("Please do /tlog first.")
            else:
                msg = urllib.quote(" ".join(parts[1:]) + " #iCraft")
                data = urllib.urlencode({"status": " ".join(parts[1:]) + " #iCraft"})
                urllib.urlopen(("http://%s:%s@twitter.com/statuses/update.xml" % (self.tuser,self.tpass)), data)
                self.client.sendServerMessage("You have successfully tweeted.")
                self.twlog.write(self.tuser+"("+self.client.username+")"+" Has tweeted: "+msg)
                self.twlog.flush()
        else:
            self.client.sendServerMessage("You can't use twitter from a cmdblock!")

    @info_list
    def commandDetails(self, parts, byuser, overriderank):
        "/tdetails - Guest\nGives you your Twitter login details, from /tlog."
        if not overriderank:
            if len(self.tuser) < 1:
                self.client.sendServerMessage("Username: "+COLOUR_RED+"Not entered!")
            else:
                self.client.sendServerMessage("Username: "+COLOUR_RED+self.tuser)
            if len(self.tpass) < 1:
                self.client.sendServerMessage("Password: "+COLOUR_RED+"Not entered!")
            else:
                self.client.sendServerMessage("Password: "+COLOUR_RED+self.tpass)
                self.twlog.write(self.tuser+"("+self.client.username+")"+" Has checked their Twitter details.")
                self.twlog.flush()
        else:
            self.client.sendServerMessage("You can't use twitter from a cmdblock!")
