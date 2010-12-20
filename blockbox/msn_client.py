# blockBox is Copyright 2009-2010 of the Archives Team, the blockBox Team, and the iCraft team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

import getpass, locale, sys
from urllib import quote, unquote

from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.words.protocols import msn
from twisted.python import log

def _createNotificationFac():
    fac = msn.NotificationFactory()
    fac.userHandle = USER_HANDLE
    fac.password = PASSWORD
    fac.protocol = Notification
    return fac

class Switchboard(msn.SwitchboardClient):
    def __init__(self, notification, userHandle, person, key, sessionID='', message=''):
        msn.SwitchboardClient.__init__(self)
        self.notification = notification
        self.userHandle = USER_HANDLE
        self.to = userHandle
        self.person = person
        self.key = key
        self.sessionID = sessionID

    def lineReceived(self, line):
        print "<<<", line.decode('UTF-8').encode(default_locale[1])
        msn.SwitchboardClient.lineReceived(self, line)

    def sendLine(self, line):
        print ">>>", line.decode('UTF-8').encode(default_locale[1])
        msn.SwitchboardClient.sendLine(self, line)

    def gotMessage(self, msg):
        print msg.message.decode('UTF-8').encode(default_locale[1])
        echo = msn.MSNMessage(message = msg.message)
        echo.setHeader('Content-Type', msg.getHeader('Content-Type'))
        self.sendMessage(echo)

class SwitchboardFactory(ClientFactory):
    protocol = Switchboard
    def __init__(self, notification, userHandle, person, key, sessionID='', message=''):
        self.notification = notification
        self.userHandle = userHandle
        self.person = person
        self.key = key
        self.sessionID = sessionID
        self.message = message

    def buildProtocol(self,addr):
        p = self.protocol(self.notification, self.userHandle, self.person, self.key, self.sessionID, self.message)
        if self.sessionID:
            p.reply = 1
        return p

class Dispatch(msn.DispatchClient):

    def __init__(self):
        msn.DispatchClient.__init__(self)
        self.userHandle = USER_HANDLE

    def gotNotificationReferral(self, host, port):
        self.transport.loseConnection()
        reactor.connectTCP(host, port, _createNotificationFac())

class Notification(msn.NotificationClient):

    def loginFailure(self, message):
        print 'Login failure:', message

    def listSynchronized(self, *args):
        contactList = self.factory.contacts
        print 'Contact list has been synchronized, number of contacts = %s' % len(contactList.getContacts())
        for contact in contactList.getContacts().values():
            if not contact.lists & msn.REVERSE_LIST:
                # Can't just promptRemovedMe here, or else the account will enter a strange state
                print 'WARNING: %s removed me' % contact.userHandle
                continue
            print 'Contact: %s' % (contact.screenName,)
            print '    email: %s' % (contact.userHandle,)
            print '   groups:'
            for group in contact.groups:
                print '      - %s' % contactList.groups[group]
            print
        # Did anyone enter my FORWARD_LIST when I am offline?
        for contact in contactList.getReverseContacts().values():
            if not contact.lists & msn.FORWARD_LIST:
                self.promptAddedMe(contact.userHandle, contact.screenName)

    def promptRemovedMe(self, userHandle):
        print userHandle, "REMOVE ME!"
        self.remContact(msn.ALLOW_LIST, userHandle)
        self.remContact(msn.FORWARD_LIST, userHandle)

    def promptAddedMe(self, userHandle, screenName):
        print userHandle, screenName, "ADD ME!"
        self.addContact(msn.ALLOW_LIST, userHandle)
        self.addContact(msn.FORWARD_LIST, userHandle)

    def userRemovedMe(self, userHandle, listVersion):
        '''Reloads userRemovedMe '''
        msn.NotificationClient.userRemovedMe(self, userHandle, listVersion)
        self.promptRemovedMe(userHandle)

    def userAddedMe(self, userHandle, screenName, listVersion):
        '''Reloads userAddedMe '''
        msn.NotificationClient.userAddedMe(self, userHandle, screenName, listVersion)
        self.promptAddedMe(userHandle, screenName)

    def gotSwitchboardInvitation(self, sessionID, host, port,
                                 key, userHandle, screenName):
        print '%s(%s) send a invitaion ...' % (userHandle, screenName)
        factory = SwitchboardFactory(self, userHandle, screenName, key, sessionID)
        print 'connect to %s:%d' % (host, port)
        print 'key => %s; sessionID => %d' % (key, sessionID)
        reactor.connectTCP(host, port, factory)

    def gotMessage(self, message):
        cTypes = [s.lstrip() for s in message.getHeader('Content-Type').split(';')]
        if 'text/x-msmsgsinitialemailnotification' in cTypes:
            print 'Hotmail Info ->', message.message.split('\r\n')[0]
        print

    def lineReceived(self, line):
        print line.decode('UTF-8').encode(default_locale[1])
        msn.MSNEventBase.lineReceived(self, line)

    def handle_LST(self, params):
        print params
        msn.NotificationClient.handle_LST(self, params)

if __name__ == '__main__':
    USER_HANDLE = raw_input("Email (passport): ")
    PASSWORD = getpass.getpass()
    log.startLogging(sys.stdout)
    default_locale = locale.getdefaultlocale()
    _dummy_fac = ClientFactory()
    _dummy_fac.protocol = Dispatch
    reactor.connectTCP('messenger.hotmail.com', 1863, _dummy_fac)
    reactor.run()

"""
THIS IS A NEWLY PLANNED IDEA. NOTHING HAS BEEN DONE YET!

A brand new idea. MSN client.

Users get an new account for the bot on Windows Live, when server starts up the MSN bot will connect.
Specify the owner's MSN account, and the bot will try to add him. If owner sent a request to add the bot, the bot will accept (at this point it ignores others)
The owner can send a Shake (idk what's the name) which is equal to a /cmdlist.
The owner can send commands. He can also make the MSN client return chatlogs or even console logs.
The owner can save maps to the server and boot it, thanks to the file transfer feature in MSN.

So... these are the currently planned features. 
-tyteen
"""
