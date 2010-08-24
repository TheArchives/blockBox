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

import threading
import time

class ResettableTimer(threading.Thread):
    """
    The ResettableTimer class is a timer whose counting loop can be reset
    arbitrarily. Its duration is configurable. Commands can be specified
    for both expiration and update. Its update resolution can also be
    specified. Resettable timer keeps counting until the "run" method
    is explicitly killed with the "kill" method.
    """

    def __init__(self, maxtime,inc, expire , update=None):
        """
        @param maxtime: time in seconds before expiration after resetting
                        in seconds
        @param expire: function called when timer expires
        @param inc: amount by which timer increments before
                    updating in seconds, default is maxtime/2
        @param expire: function called when timer completes
        @param update: function called when timer updates
        """
        self.maxtime = maxtime
        self.expire = expire
        self.inc = inc
        if update:
            self.update = update
        else:
            self.update = lambda c : None
        self.counter = 0
        self.stop = False
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def set_counter(self, t):
        """
        Set self.counter to t.
        @param t: new counter value
        """
        self.counter = t

    def kill(self):
        """
        Will stop the counting loop before next update.
        """
        self.stop = True
        self.counter = self.maxtime

    def reset(self):
        """
        Fully rewinds the timer and makes the timer active, such that
        the expire and update commands will be called when appropriate.
        """
        self.counter = 0
        self.stop = False
        
    def run(self):
        """
        Run the timer loop.
        """
        self.counter = 0
        while self.counter < self.maxtime and not self.stop:
            self.counter += self.inc
            time.sleep(self.inc)
            self.update(self.counter)
        if not self.stop:
            self.expire()
