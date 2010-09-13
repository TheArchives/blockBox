##############################################################################
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################

from lib.zope.interface import Interface, Attribute
from lib.zope.interface import classImplements

from datetime import timedelta, date, datetime, time, tzinfo


class ITimeDeltaClass(Interface):

    min = Attribute("The most negative timedelta object")

    max = Attribute("The most positive timedelta object")

    resolution = Attribute(
        "The smallest difference between non-equal timedelta objects")


class ITimeDelta(ITimeDeltaClass):
    days = Attribute("Days between -999999999 and 999999999 inclusive")

    seconds = Attribute("Seconds between 0 and 86399 inclusive")

    microseconds = Attribute("Microseconds between 0 and 999999 inclusive")


class IDateClass(Interface):
    min = Attribute("The earliest representable date")

    max = Attribute("The latest representable date")

    resolution = Attribute(
        "The smallest difference between non-equal date objects")

    def today():

    def fromtimestamp(timestamp):

    def fromordinal(ordinal):

class IDate(IDateClass):

    year = Attribute("Between MINYEAR and MAXYEAR inclusive.")

    month = Attribute("Between 1 and 12 inclusive")

    day = Attribute(
        "Between 1 and the number of days in the given month of the given year.")

    def replace(year, month, day):

    def timetuple():

    def toordinal():

    def weekday():

    def isoweekday():

    def isocalendar():

    def isoformat():

    def __str__():

    def ctime():

    def strftime(format):

class IDateTimeClass(Interface):

    min = Attribute("The earliest representable datetime")

    max = Attribute("The latest representable datetime")

    resolution = Attribute(
        "The smallest possible difference between non-equal datetime objects")

    def today():

    def now(tz=None):

    def utcnow():

    def fromtimestamp(timestamp, tz=None):

    def utcfromtimestamp(timestamp):

    def fromordinal(ordinal):

    def combine(date, time):

class IDateTime(IDate, IDateTimeClass):

    year = Attribute("Year between MINYEAR and MAXYEAR inclusive")

    month = Attribute("Month between 1 and 12 inclusive")

    day = Attribute(
        "Day between 1 and the number of days in the given month of the year")

    hour = Attribute("Hour in range(24)")

    minute = Attribute("Minute in range(60)")

    second = Attribute("Second in range(60)")

    microsecond = Attribute("Microsecond in range(1000000)")

    tzinfo = Attribute(
        """The object passed as the tzinfo argument to the datetime constructor
        or None if none was passed""")

    def date():

    def time():

    def timetz():

    def replace(year, month, day, hour, minute, second, microsecond, tzinfo):

    def astimezone(tz):

    def utcoffset():

    def dst():

    def tzname():

    def timetuple():

    def utctimetuple():

    def toordinal():

    def weekday():

    def isoweekday():

    def isocalendar():

    def isoformat(sep='T'):

    def __str__():

    def ctime():

    def strftime(format):

class ITimeClass(Interface):

    min = Attribute("The earliest representable time")

    max = Attribute("The latest representable time")

    resolution = Attribute(
        "The smallest possible difference between non-equal time objects")


class ITime(ITimeClass):

    hour = Attribute("Hour in range(24)")

    minute = Attribute("Minute in range(60)")

    second = Attribute("Second in range(60)")

    microsecond = Attribute("Microsecond in range(1000000)")

    tzinfo = Attribute(
        """The object passed as the tzinfo argument to the time constructor
        or None if none was passed.""")

    def replace(hour, minute, second, microsecond, tzinfo):

    def isoformat():

    def __str__():

    def strftime(format):

    def utcoffset():

    def dst():

    def tzname():

class ITZInfo(Interface):

    def utcoffset(dt):

    def dst(dt):

    def tzname(dt):

    def fromutc(dt):

classImplements(timedelta, ITimeDelta)
classImplements(date, IDate)
classImplements(datetime, IDateTime)
classImplements(time, ITime)
classImplements(tzinfo, ITZInfo)

## directlyProvides(timedelta, ITimeDeltaClass)
## directlyProvides(date, IDateClass)
## directlyProvides(datetime, IDateTimeClass)
## directlyProvides(time, ITimeClass)
