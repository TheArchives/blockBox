##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

class Invalid(Exception):


class DoesNotImplement(Invalid):
    def __init__(self, interface):
        self.interface = interface

    def __str__(self):
        return """An object does not implement interface %(interface)s

        """ % self.__dict__

class BrokenImplementation(Invalid):

    def __init__(self, interface, name):
        self.interface=interface
        self.name=name

    def __str__(self):
        return """An object has failed to implement interface %(interface)s

        The %(name)s attribute was not provided.
        """ % self.__dict__

class BrokenMethodImplementation(Invalid):

    def __init__(self, method, mess):
        self.method=method
        self.mess=mess

    def __str__(self):
        return """The implementation of %(method)s violates its contract
        because %(mess)s.
        """ % self.__dict__

class InvalidInterface(Exception):


class BadImplements(TypeError):

