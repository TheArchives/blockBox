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

from twisted.internet import reactor
from myne.plugins import ProtocolPlugin
from myne.decorators import *
from myne.constants import *
import Image
import urllib
import StringIO

class ImagedrawPlugin(ProtocolPlugin):

    commands = {
        "rec_url": "commandRec_url",
        "imagedraw": "commandImagedraw",
    }

    @build_list
    @admin_only
    def commandRec_url(self, parts, byuser, overriderank):
        "/rec_url URL - Builder\nRecords an url to later imagedraw it."
        if len(parts) == 1:
            self.client.sendServerMessage("Please specify an url (and '//' in the beginning to")
            self.client.sendServerMessage("extend an existing url)")
            return
        else:
            if parts[0] == '//rec_url':
                try:
                    self.client.url = self.client.url + (" ".join(parts[1:])).strip()
                except:
                    self.client.sendServerMessage("You have not started recording and url yet")
                    return
            else:
                self.client.url = (" ".join(parts[1:])).strip()
        var_divisions64 = int(len(self.client.url)/64)
        self.client.sendServerMessage("The url has been recorded as")
        for i in range(var_divisions64):
            self.client.sendServerMessage(self.client.url[i*64:(i+1)*64])
        self.client.sendServerMessage(self.client.url[var_divisions64*64:])

    @build_list
    @admin_only
    def commandImagedraw(self, parts, byuser, overriderank):
        "/imagedraw [x y z x2 y2 z2] - Builder\nSets all blocks in this area to image."
        if len(parts) < 8 and len(parts) != 2 and len(parts) != 3:
            self.client.sendServerMessage("Please enter whether to flip? (rotation)")
            self.client.sendServerMessage("(and possibly two coord triples)")
        else:
            if len(parts)==3:
                # Try getting the rotation
                try:
                    rotation = int(parts[2])
                except ValueError:
                    self.client.sendServerMessage("Rotation must be a Number.")
                    return
            else:
                rotation = 0
            #try to get flip?
            flip = parts[1]
            if flip=='true' or flip=='false':
                pass
            else:
                self.client.sendServerMessage("flip must be true or false")
                return
            #try to get url
            try:
                imageurl = self.client.url
            except:
                self.client.sendServerMessage("You have not recorded an url yet (use /rec_url).")
                return
            if imageurl.find('http:') == -1:
                self.client.sendServerMessage("You cannot access server files, only external files")
                return
            # If they only provided the type argument, use the last two block places
            if len(parts) == 2 or len(parts) == 3:
                try:
                    x, y, z = self.client.last_block_changes[0]
                    x2, y2, z2 = self.client.last_block_changes[1]
                except IndexError:
                    self.client.sendServerMessage("You have not clicked two corners yet.")
                    return
            else:
                try:
                    x = int(parts[3])
                    y = int(parts[4])
                    z = int(parts[5])
                    x2 = int(parts[6])
                    y2 = int(parts[7])
                    z2 = int(parts[8])
                except ValueError:
                    self.client.sendServerMessage("All parameters must be integers")
                    return
            if y == y2:
                height = abs(x2-x)+1
                width = abs(z2-z)+1
                orientation = 0
            elif z == z2:
                height = abs(x2-x)+1
                width = abs(y2-y)+1
                orientation = 1
            else:
                x2 = x
                height = abs(y2-y)+1
                width = abs(z2-z)+1
                orientation = 2
            try:
                u = urllib.urlopen(imageurl)
                f = StringIO.StringIO(u.read())
                image = Image.open(f)
            except:
                self.client.sendServerMessage("The url or image is invalid")
                return
            if rotation != 0:
                image = image.rotate(rotation,3,1)
            image = image.resize((width,height),1)
            image = image.convert('RGBA')
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            if z > z2:
                z, z2 = z2, z
            if self.client.isDirector() or overriderank:
                limit = 1073741824
            elif self.client.isAdmin():
                limit = 2097152
            elif self.client.isMod():
                limit = 262144
            elif self.client.isOp():
                limit = 110592
            elif self.client.isMember():
                limit = 55296
            else:
                limit = 4062
            # Stop them doing silly things
            if height*width > limit:
                self.client.sendServerMessage("Sorry, that area is too big for you to imagedraw.")
                return
            # Draw all the blocks on, I guess
            # We use a generator so we can slowly release the blocks
            # We also keep world as a local so they can't change worlds and affect the new one
            world = self.client.world
            def generate_changes():
                for i in range(x, x2+1):
                    for j in range(y, y2+1):
                        for k in range(z, z2+1):
                            if not self.client.AllowedToBuild(i, j, k) and overriderank==False:
                                return
                            if flip=='true':
                                if orientation == 0:
                                    r,g,b,a = image.getpixel((abs(k-z),abs(i-x)))
                                elif orientation == 1:
                                    r,g,b,a = image.getpixel((abs(j-y),abs(i-x)))
                                else:
                                    r,g,b,a = image.getpixel((abs(k-z),abs(j-y)))
                            else:
                                if orientation == 0:
                                    r,g,b,a = image.getpixel((width - (abs(k-z)+1),abs(i-x)))
                                elif orientation == 1:
                                    r,g,b,a = image.getpixel((width - (abs(j-y)+1),abs(i-x)))
                                else:
                                    r,g,b,a = image.getpixel((width - (abs(k-z)+1),abs(j-y)))
                            if a < 25:
                                block = BLOCK_AIR
                            else:
                                r = int(round(float(r)/50))*50
                                if r == 0:
                                    r = 50
                                if r == 250:
                                    r = 200
                                g = int(round(float(g)/50))*50
                                if g == 0:
                                    g = 50
                                if g == 250:
                                    g = 200
                                b = int(round(float(b)/50))*50
                                if b == 0:
                                    b = 50
                                if b == 250:
                                    b = 200
                                if r == 50:
                                    if g == 100:
                                        g = 50
                                    if g == 150:
                                        g = 200
                                if r == 100:
                                    if g == 50:
                                        g = 100
                                    if g == 200:
                                        g = 150
                                if r == 150:
                                    if g == 100:
                                        g = 150
                                if r==50 and g==50:
                                    b = 50
                                if r==50 and g==200:
                                    if b == 100:
                                        b = 150
                                if r==100 and g==100:
                                    b = 100
                                if r==100 and g==150:
                                    b = 200
                                if r==150 and g==50:
                                    b = 200
                                if r==150 and g==150:
                                    if b == 50 or b == 100:
                                        b = 150
                                if r==150 and g==200:
                                    b = 50
                                if r==200 and g==50:
                                    if b == 100:
                                        b = 150
                                if r==200 and g==100:
                                    b = 200
                                if r==200 and g==150:
                                    b = 50
                                if r==200 and g==200:
                                    if b == 100:
                                        b = 50
                                    if b == 150:
                                        b = 200
                                if (r,g,b) == (200,50,50):
                                    block = BLOCK_RED
                                if (r,g,b) == (200,150,50):
                                    block = BLOCK_ORANGE
                                if (r,g,b) == (200,200,50):
                                    block = BLOCK_YELLOW
                                if (r,g,b) == (150,200,50):
                                    block = BLOCK_LIME
                                if (r,g,b) == (50,200,50):
                                    block = BLOCK_GREEN
                                if (r,g,b) == (50,200,150):
                                    block = BLOCK_TURQUOISE
                                if (r,g,b) == (50,200,200):
                                    block = BLOCK_CYAN
                                if (r,g,b) == (100,150,200):
                                    block = BLOCK_BLUE
                                if (r,g,b) == (150,150,200):
                                    block = BLOCK_INDIGO
                                if (r,g,b) == (150,50,200):
                                    block = BLOCK_VIOLET
                                if (r,g,b) == (200,100,200):
                                    block = BLOCK_PURPLE
                                if (r,g,b) == (200,50,200):
                                    block = BLOCK_MAGENTA
                                if (r,g,b) == (200,50,150):
                                    block = BLOCK_PINK
                                if (r,g,b) == (100,100,100):
                                    block = BLOCK_BLACK
                                if (r,g,b) == (150,150,150):
                                    block = BLOCK_GRAY
                                if (r,g,b) == (200,200,200):
                                    block = BLOCK_WHITE
                                if (r,g,b) == (50,50,50):
                                    block = BLOCK_OBSIDIAN
                            block = chr(block)
                            try:
                                world[i, j, k] = block
                            except AssertionError:
                                self.client.sendServerMessage("Out of bounds imagedraw error.")
                                return
                            self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                            self.client.sendBlock(i, j, k, block)
                            yield
            # Now, set up a loop delayed by the reactor
            block_iter = iter(generate_changes())
            def do_step():
                # Do 10 blocks
                try:
                    for x in range(10):#10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                        block_iter.next()
                    reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
                except StopIteration:
                    self.client.sendServerMessage("Your imagedraw just completed.")
                    pass
            do_step()
