# -*- test-case-name: lib.twisted.words.test -*-
# Copyright (c) 2001-2005 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.zope.interface import Interface, Attribute, implements

class IProtocolPlugin(Interface):
    name = Attribute("A single word describing what kind of interface this is (eg, irc or web)")

    def getFactory(realm, portal):

class IGroup(Interface):
    name = Attribute("A short string, unique among groups.")

    def add(user):

    def remove(user, reason=None):

    def size():

    def receive(sender, recipient, message):

    def setMetadata(meta):

    def iterusers():

class IChatClient(Interface):
    name = Attribute("A short string, unique among users.  This will be set by the L{IChatService} at login time.")

    def receive(sender, recipient, message):

    def groupMetaUpdate(group, meta):

    def userJoined(group, user):

    def userLeft(group, user, reason=None):

class IUser(Interface):
    realm = Attribute("A reference to the Realm to which this user belongs.  Set if and only if the user is logged in.")
    mind = Attribute("A reference to the mind which logged in to this user.  Set if and only if the user is logged in.")
    name = Attribute("A short string, unique among users.")
    lastMessage = Attribute("A POSIX timestamp indicating the time of the last message received from this user.")
    signOn = Attribute("A POSIX timestamp indicating this user's most recent sign on time.")

    def loggedIn(realm, mind):

    def send(recipient, message):

    def join(group):

    def leave(group):

    def itergroups():

class IChatService(Interface):
    name = Attribute("A short string identifying this chat service (eg, a hostname)")
    createGroupOnRequest = Attribute(
        "A boolean indicating whether L{getGroup} should implicitly "
        "create groups which are requested but which do not yet exist.")
    createUserOnRequest = Attribute(
        "A boolean indicating whether L{getUser} should implicitly "
        "create users which are requested but which do not yet exist.")
    def itergroups():

    def getGroup(name):

    def createGroup(name):

    def lookupGroup(name):

    def getUser(name):

    def createUser(name):

__all__ = [
    'IChatInterface', 'IGroup', 'IChatClient', 'IUser', 'IChatService',
    ]
