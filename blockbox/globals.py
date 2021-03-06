# blockBox is copyright 2009-2011 the Arc Team, the blockBox Team and other contributors.
# blockBox is licensed under the BSD 3-Clause Modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from collections import defaultdict

def Rank(self, parts, fromloc, overriderank, server=None):
    username = parts[1].lower()
    if server:
        factory = server
    else:
        factory = self.client.factory
    if parts[2] == "builder":
        if len(parts) > 3:
            try:
                world = factory.worlds[parts[3]]
            except KeyError:
                return ("Unknown world %s" % parts[3])
        else:
            if not server:
                world = self.client.world
            else:
                return "You must provide a world."
        # Make builder
        if not server:
            if not (self.client.username.lower() in world.ops or self.client.isWorldOwner() or self.client.isMod()) and not overriderank:
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                if not ((parts[-1]) in world.ops) or factory.isMod(parts[-1]):
                    return ("You are not high enough rank!")
        world.builders.add(username)
        if username in factory.usernames:
            user = factory.usernames[username]
            if user.world == world:
                user.sendBuilderUpdate()
        return ("%s is now a builder in world %s." % (username, world))
    elif parts[2] == "op":
        if len(parts) > 3:
            try:
                world = factory.worlds[parts[3]]
            except KeyError:
                return ("Unknown world %s" % parts[3])
        else:
            if not server:
                world = self.client.world
            else:
                return "You must provide a world."
        if not server:
            if not self.client.isWorldOwner() and not overriderank:
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                return ("You are not high enough rank!")
        world.ops.add(username)
        return ("Opped %s" % username)
        # make op
    elif parts[2] == "worldowner":
        if len(parts) > 3:
            try:
                world = factory.worlds[parts[3]]
            except KeyError:
                return ("Unknown world %s" % parts[3])
        else:
            if not server:
                world = self.client.world
            else:
                return "You must provide a world."
        if not server:
            if not self.client.isMod() and not overriderank:
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                return ("You are not high enough rank!")
        world.owner = username
        return ("%s is now the world owner of world %s." % (username, world))
    elif parts[2] == "advbuilder":
        # make them an advbuilder
        if not server:
            if not self.client.isMod():
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                if not factory.isMod(parts[-1]):
                    return ("You are not high enough rank!")
        factory.advbuilders.add(username)
        if username in factory.usernames:
            factory.usernames[username].sendAdvBuilderUpdate()
        return ("%s is now an Advanced Builder." % username)
    elif parts[2] == "mod":
        #make them a mod
        if not server:
            if not self.client.isDirector():
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                if not factory.isDirector(parts[-1]):
                    return ("You are not high enough rank!")
        factory.mods.add(username)
        if username in factory.usernames:
            factory.usernames[username].sendModUpdate()
        return ("%s is now a Mod." % username)
    elif parts[2] == "admin":
        #make them admin
        if not server:
            if not self.client.isDirector():
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                if not factory.isDirector(parts[-1]):
                    return ("You are not high enough rank!")
        factory.admins.add(username)
        if username in factory.usernames:
            factory.usernames[username].sendAdminUpdate()
        return ("%s is now an admin." % username)
    elif parts[2] == "director":
        #make them director
        if not server:
            if not self.client.isOwner():
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                if not factory.isOwner(parts[-1]):
                    return ("You are not high enough rank!")
        factory.directors.add(username)
        if username in factory.usernames:
            factory.usernames[username].sendDirectorUpdate()
        return ("%s is now a director." % username)
    else:
        return ("Unknown rank \"%s\""%parts[1])

def DeRank(self, parts, fromloc, overriderank, server=None):
    username = parts[2].lower()
    if server:
        factory = server
    else:
        factory = self.client.factory
    if parts[2] == "builder":
        if len(parts) > 3:
            try:
                world = factory.worlds[parts[3]]
            except KeyError:
                return ("Unknown world %s" %parts[3])
        else:
            if not server:
                world = self.client.world
            else:
                return "You must provide a world."
        #Make builder
        if not server:
            if not ((self.client.username in world.ops) or self.client.isWorldOwner() or self.client.isMod()) and overriderank:
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                if not ((parts[-1]) in world.ops) or factory.isMod(parts[-1]):
                    return ("You are not high enough rank!")
        try:
            world.builders.remove(username)
        except KeyError:
                return ("%s is not a builder in world %s." % (username, world))
        if username in factory.usernames:
            user = factory.usernames[username]
            if user.world == world:
                user.sendBuilderUpdate()
        return ("Removed builder %s in world %s" % (username, world))
    elif parts[2] == "op":
        if len(parts) > 3:
            try:
                world = factory.worlds[parts[3]]
            except KeyError:
                return ("Unknown world %s" % parts[3])
        else:
            if not server:
                world = self.client.world
            else:
                return "You must provide a world."
        if not server:
            if not self.client.isWorldOwner() and world != self.client.world:
                return ("You are not a World Owner!")
        else:
            if fromloc != "console":
                if not factory.isWorldOwner(parts[-1]):
                    return ("You are not high enough rank!")
        try:
            world.ops.remove(username)
        except KeyError:
            return ("%s is not an op in world %s." % (username, world))
        if username in factory.usernames:
            user = factory.usernames[username]
            if user.world == world:
                user.sendOpUpdate()
        return ("%s is no longer an op in world %s." % (username, world))
        #make worldowner
    elif parts[2] == "worldowner":
        if len(parts) > 3:
            try:
                world = factory.worlds[parts[3]]
            except KeyError:
                return ("Unknown world %s" % parts[3])
        else:
            if not server:
                world = self.client.world
            else:
                return "You must provide a world."
        if not server:
            if not self.client.isWorldOwner() and world != self.client.world:
                return ("You are not a World Owner!")
        else:
            if fromloc != "console":
                if not factory.isWorldOwner(parts[-1]):
                    return ("You are not high enough rank!")
        try:
            self.client.world.owner = ("")
        except KeyError:
            return ("%s is not a world owner." % username)
        if username in factory.usernames:
            user = factory.usernames[username]
            if user.world == world:
                user.sendWorldOwnerUpdate()
        return ("%s is no longer the world owner of world %s." % (username, world))
    elif parts[2] == "advbuilder":
        #make them an advbuilder
        if not server:
            if not self.client.isMod():
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                if not factory.isMod(parts[-1]):
                    return ("You are not high enough rank!")
        if username in factory.advbuilders:
            factory.advbuilders.remove(username)
        else:
            return ("No such advanced builder %s" % username.lower())
        if username in factory.usernames:
            factory.usernames[username].sendAdvBuilderUpdate()
        return ("%s is no longer an Advanced Builder." % username.lower())
    elif parts[2] == "mod":
        #make them a mod
        if not server:
            if not self.client.isDirector():
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                if not factory.isDirector(parts[-1]):
                    return ("You are not high enough rank!")
        if username in factory.mods:
            factory.mods.remove(username)
        else:
            return ("No such mod %s" % username.lower())
        if username in factory.usernames:
            factory.usernames[username].sendModUpdate()
        return ("%s is no longer a mod." % username.lower())
    elif parts[2] == "admin":
        #make them admin
        if not server:
            if not self.client.isDirector():
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                if not factory.isDirector(parts[-1]):
                    return ("You are not high enough rank!")
        if username in factory.admins:
            factory.admins.remove(username)
            if username in factory.usernames:
                factory.usernames[username].sendAdminUpdate()
            return ("%s is no longer an admin." % username.lower())
        else:
            return ("No such admin %s." % username.lower())
    elif parts[2] == "director":
        #make them director
        if not server:
            if not self.client.isOwner():
                return ("You are not high enough rank!")
        else:
            if fromloc != "console":
                if not factory.isOwner(parts[-1]):
                    return ("You are not high enough rank!")
        if username in factory.directors:
            factory.directors.remove(username)
            if username in factory.usernames:
                factory.usernames[username].sendDirectorUpdate()
            return ("%s is no longer a director." % username.lower())
        else:
            return ("No such director %s" % username.lower())
    else:
        return ("Unknown rank %s" % parts[1])

def Spec(self, username, fromloc, overriderank, server=None):
    if server:
        factory = server
    else:
        factory = self.client.factory
    if username in factory.mods:
        return ("You cannot make staff a spec!")
    factory.spectators.add(username)
    if username in factory.usernames:
        factory.usernames[username].sendSpectatorUpdate()
    return ("%s is now a spec." % username)

def DeSpec(self, username, fromloc, overriderank, server=None):
    if server:
        factory = server
    else:
        factory = self.client.factory
    try:
        factory.spectators.remove(username)
    except:
        return ("%s was not specced." % username)
    if username in factory.usernames:
        factory.usernames[username].sendSpectatorUpdate()
    return ("%s is no longer a spec." % username)

def Staff(self, server=None):
    Temp = []
    if server:
        factory = server
    else:
        factory = self.client.factory
    if len(factory.directors):
        Temp.append(["Directors:"] + list(factory.directors))
    if len(factory.admins):
        Temp.append(["Admins:"] + list(factory.admins))
    if len(factory.mods):
        Temp.append(["Mods:"] + list(factory.mods))
    return Temp

def Credits():
    Temp = []
    Temp.append ("Thanks to the following people for making blockBox possible...")
    Temp.append ("Mojang Specifications (Minecraft): Notch, dock, ez, ...")
    Temp.append ("Creators and Maintainers: aera (Myne), PixelEater (MyneCraft), gdude2002 (Arc), tyteen4a03 (blockBox)")
    Temp.append ("Devs: Adam01, revenant, gdude2002, gothfox, AndrewPH, Varriount, erronjason, destroyerx1, ntfwc, Dwarfy, goober, willempiee")
    Temp.append ("Devs: tyteen4a03, ntfwc, UberFoX, fizyplankton, opticalza")
    Temp.append ("Others: Bidoof_King, Rils, fragmer, PyroPyro, TkTech, the Users, the Testers, the Modders, the Community, ...")
    return Temp

def recursive_default():
    return defaultdict(recursive_default)

def create_if_not(filename):
    import os
    dir = os.path.dirname(filename)
    try:
        os.stat(dir)
    except:
        try:
            os.mkdir(dir)
        except OSError:
            pass
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("")
    del os

def invertDict(OldDict):
    NewDict = dict()
    for key in OldDict.iterkeys():
        if OldDict[key] not in NewDict:
            NewDict[OldDict[key]] = key
    return NewDict

def doExit(exitTime=10):
    print ("blockBox will now exit in %s seconds." % exitTime)
    #if sys.platform == "win32":
    #    print ("blockBox may not exit if run on Windows. Please close the window yourself.")
    sys.exit(exitTime)