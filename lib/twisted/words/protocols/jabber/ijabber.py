# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.
from lib.zope.interface import Attribute, Interface
class IInitializer(Interface):

class IInitiatingInitializer(IInitializer):
    xmlstream = Attribute("""The associated XML stream""")
    def initialize():

class IIQResponseTracker(Interface):
    iqDeferreds = Attribute("Dictionary of deferreds waiting for an iq "
                             "response")

class IXMPPHandler(Interface):
    parent = Attribute("""XML stream manager for this handler""")
    xmlstream = Attribute("""The managed XML stream""")

    def setHandlerParent(parent):

    def disownHandlerParent(parent):

    def makeConnection(xs):

    def connectionMade():

    def connectionInitialized():

    def connectionLost(reason):

class IXMPPHandlerCollection(Interface):
    def __iter__():

    def addHandler(handler):

    def removeHandler(handler):

class IService(Interface):
    def componentConnected(xs):

    def componentDisconnected():

    def transportConnected(xs):
