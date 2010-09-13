##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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

from lib.zope.interface.interface import Interface, _wire

# Need to actually get the interface elements to implement the right interfaces
_wire()
del _wire

from lib.zope.interface.interface import Attribute, invariant, taggedValue

from lib.zope.interface.declarations import providedBy, implementedBy
from lib.zope.interface.declarations import classImplements, classImplementsOnly
from lib.zope.interface.declarations import directlyProvidedBy, directlyProvides
from lib.zope.interface.declarations import alsoProvides, provider
from lib.zope.interface.declarations import implementer, implementer_only
from lib.zope.interface.declarations import implements, implementsOnly
from lib.zope.interface.declarations import classProvides, moduleProvides
from lib.zope.interface.declarations import noLongerProvides, Declaration
from lib.zope.interface.exceptions import Invalid

# The following are to make spec pickles cleaner
from lib.zope.interface.declarations import Provides


from lib.zope.interface.interfaces import IInterfaceDeclaration

moduleProvides(IInterfaceDeclaration)

__all__ = ('Interface', 'Attribute') + tuple(IInterfaceDeclaration)
