# -*- test-case-name: lib.twisted.words.test.test_jabberjid -*-
#
# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.twisted.words.protocols.jabber.xmpp_stringprep import nodeprep, resourceprep, nameprep

class InvalidFormat(Exception):

def parse(jidstring):
    user = None
    host = None
    resource = None
    user_sep = jidstring.find("@")
    res_sep  = jidstring.find("/")

    if user_sep == -1:
        if res_sep == -1:
            host = jidstring
        else:
            host = jidstring[0:res_sep]
            resource = jidstring[res_sep + 1:] or None
    else:
        if res_sep == -1:
            user = jidstring[0:user_sep] or None
            host = jidstring[user_sep + 1:]
        else:
            if user_sep < res_sep:
                user = jidstring[0:user_sep] or None
                host = jidstring[user_sep + 1:user_sep + (res_sep - user_sep)]
                resource = jidstring[res_sep + 1:] or None
            else:
                host = jidstring[0:res_sep]
                resource = jidstring[res_sep + 1:] or None

    return prep(user, host, resource)

def prep(user, host, resource):
    if user:
        try:
            user = nodeprep.prepare(unicode(user))
        except UnicodeError:
            raise InvalidFormat, "Invalid character in username"
    else:
        user = None

    if not host:
        raise InvalidFormat, "Server address required."
    else:
        try:
            host = nameprep.prepare(unicode(host))
        except UnicodeError:
            raise InvalidFormat, "Invalid character in hostname"

    if resource:
        try:
            resource = resourceprep.prepare(unicode(resource))
        except UnicodeError:
            raise InvalidFormat, "Invalid character in resource"
    else:
        resource = None

    return (user, host, resource)

__internJIDs = {}

def internJID(jidstring):
    if jidstring in __internJIDs:
        return __internJIDs[jidstring]
    else:
        j = JID(jidstring)
        __internJIDs[jidstring] = j
        return j

class JID(object):
    def __init__(self, str=None, tuple=None):
        if not (str or tuple):
            raise RuntimeError("You must provide a value for either 'str' or "
                               "'tuple' arguments.")

        if str:
            user, host, res = parse(str)
        else:
            user, host, res = prep(*tuple)

        self.user = user
        self.host = host
        self.resource = res

    def userhost(self):
        if self.user:
            return u"%s@%s" % (self.user, self.host)
        else:
            return self.host

    def userhostJID(self):
        if self.resource:
            return internJID(self.userhost())
        else:
            return self

    def full(self):
        if self.user:
            if self.resource:
                return u"%s@%s/%s" % (self.user, self.host, self.resource)
            else:
                return u"%s@%s" % (self.user, self.host)
        else:
            if self.resource:
                return u"%s/%s" % (self.host, self.resource)
            else:
                return self.host

    def __eq__(self, other):
        if isinstance(other, JID):
            return (self.user == other.user and
                    self.host == other.host and
                    self.resource == other.resource)
        else:
            return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        else:
            return not result

    def __hash__(self):
        return hash((self.user, self.host, self.resource))

    def __unicode__(self):
        return self.full()

    def __repr__(self):
        return 'JID(%r)' % self.full()
