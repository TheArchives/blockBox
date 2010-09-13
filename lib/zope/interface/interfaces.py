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
__docformat__ = 'restructuredtext'


from lib.zope.interface import Interface
from lib.zope.interface.interface import Attribute

class IElement(Interface):

    __name__ = Attribute('__name__', 'The object name')
    __doc__  = Attribute('__doc__', 'The object doc string')

    def getTaggedValue(tag):

    def queryTaggedValue(tag, default=None):

    def getTaggedValueTags():

    def setTaggedValue(tag, value):

class IAttribute(IElement):

    interface = Attribute('interface',
                          'Stores the interface instance in which the '
                          'attribute is located.')


class IMethod(IAttribute):


    def getSignatureInfo():

    def getSignatureString():

class ISpecification(Interface):

    def extends(other, strict=True):

    def isOrExtends(other):

    def weakref(callback=None):

    __bases__ = Attribute("""Base specifications

    A tuple if specifications from which this specification is
    directly derived.

    """)

    __sro__ = Attribute("""Specification-resolution order

    A tuple of the specification and all of it's ancestor
    specifications from most specific to least specific.

    (This is similar to the method-resolution order for new-style classes.)
    """)

    __iro__ = Attribute("""Interface-resolution order

    A tuple of the of the specification's ancestor interfaces from
    most specific to least specific.  The specification itself is
    included if it is an interface.

    (This is similar to the method-resolution order for new-style classes.)
    """)

    def get(name, default=None):


class IInterface(ISpecification, IElement):

    def providedBy(object):

    def implementedBy(class_):

    def names(all=False):

    def namesAndDescriptions(all=False):


    def __getitem__(name):

    def direct(name):

    def validateInvariants(obj, errors=None):

    def __contains__(name):

    def __iter__():

    __module__ = Attribute("""The name of the module defining the interface""")

class IDeclaration(ISpecification):

    def __contains__(interface):

    def __iter__():

    def flattened():

    def __sub__(interfaces):

    def __add__(interfaces):

    def __nonzero__():

class IInterfaceDeclaration(Interface):

    def providedBy(ob):

    def implementedBy(class_):

    def classImplements(class_, *interfaces):

    def implementer(*interfaces):

    def classImplementsOnly(class_, *interfaces):
        
    def implementer_only(*interfaces):

    def directlyProvidedBy(object):

    def directlyProvides(object, *interfaces):

    def alsoProvides(object, *interfaces):

    def noLongerProvides(object, interface):

    def implements(*interfaces):

    def implementsOnly(*interfaces):

    def classProvides(*interfaces):

    def provider(*interfaces):

    def moduleProvides(*interfaces):

    def Declaration(*interfaces):

class IAdapterRegistry(Interface):

    def register(required, provided, name, value):

    def registered(required, provided, name=u''):

    def lookup(required, provided, name='', default=None):

    def queryMultiAdapter(objects, provided, name=u'', default=None):

    def lookup1(required, provided, name=u'', default=None):

    def queryAdapter(object, provided, name=u'', default=None):

    def adapter_hook(provided, object, name=u'', default=None):

    def lookupAll(required, provided):

    def names(required, provided):

    def subscribe(required, provided, subscriber, name=u''):

    def subscriptions(required, provided, name=u''):

    def subscribers(objects, provided, name=u''):
