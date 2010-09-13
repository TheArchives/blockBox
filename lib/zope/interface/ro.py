##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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


def ro(object):
    return mergeOrderings([_flatten(object)])

def mergeOrderings(orderings, seen=None):
    if seen is None:
        seen = {}
    result = []
    orderings.reverse()
    for ordering in orderings:
        ordering = list(ordering)
        ordering.reverse()
        for o in ordering:
            if o not in seen:
                seen[o] = 1
                result.append(o)

    result.reverse()
    return result

def _flatten(ob):
    result = [ob]
    i = 0
    for ob in iter(result):
        i += 1
        result[i:i] = ob.__bases__
    return result
