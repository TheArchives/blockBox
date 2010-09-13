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
from zope import interface

class IMinimalSequence(interface.Interface):

    def __getitem__(index):

class IFiniteSequence(IMinimalSequence):

    def __len__():

class IReadSequence(IFiniteSequence):

    def __contains__(item):

    def __lt__(other):

    def __le__(other):

    def __eq__(other):

    def __ne__(other):

    def __gt__(other):

    def __ge__(other):

    def __add__(other):

    def __mul__(n):

    def __rmul__(n):

    def __getslice__(i, j):

class IExtendedReadSequence(IReadSequence):

    def count(item):

    def index(item, *args):

class IUniqueMemberWriteSequence(interface.Interface):

    def __setitem__(index, item):

    def __delitem__(index):

    def __setslice__(i, j, other):

    def __delslice__(i, j):

    def __iadd__(y):

    def append(item):

    def insert(index, item):

    def pop(index=-1):

    def remove(item):

    def reverse():

    def sort(cmpfunc=None):

    def extend(iterable):

class IWriteSequence(IUniqueMemberWriteSequence):

    def __imul__(n):

class ISequence(IReadSequence, IWriteSequence):
