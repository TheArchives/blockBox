# -*- test-case-name: twisted.words.test.test_xmpproutertap -*-
#
# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.

from lib.twisted.application import strports
from lib.twisted.python import usage
from lib.twisted.words.protocols.jabber import component

class Options(usage.Options):
    optParameters = [
            ('port', None, 'tcp:5347:interface=127.0.0.1',
                           'Port components connect to'),
            ('secret', None, 'secret', 'Router secret'),
    ]

    optFlags = [
            ('verbose', 'v', 'Log traffic'),
    ]



def makeService(config):
    router = component.Router()
    factory = component.XMPPComponentServerFactory(router, config['secret'])

    if config['verbose']:
        factory.logTraffic = True

    return strports.service(config['port'], factory)
