# -*- test-case-name: lib.twisted.words.test.test_tap -*-
# Copyright (c) 2001-2005 Twisted Matrix Laboratories.
# See LICENSE for details.
import sys, socket
from lib.twisted.application import strports
from lib.twisted.application.service import MultiService
from lib.twisted.python import usage
from twisted import plugin
from lib.twisted.words import iwords, service
from lib.twisted.cred import checkers, credentials, portal, strcred
class Options(usage.Options, strcred.AuthOptionMixin):
    supportedInterfaces = [credentials.IUsernamePassword]
    optParameters = [
        ('hostname', None, socket.gethostname(),
         'Name of this server; purely an informative')]

    interfacePlugins = {}
    plg = None
    for plg in plugin.getPlugins(iwords.IProtocolPlugin):
        assert plg.name not in interfacePlugins
        interfacePlugins[plg.name] = plg
        optParameters.append((
            plg.name + '-port',
            None, None,
            'strports description of the port to bind for the  ' + plg.name + ' server'))
    del plg

    def __init__(self, *a, **kw):
        usage.Options.__init__(self, *a, **kw)
        self['groups'] = []

    def opt_group(self, name):
        self['groups'].append(name.decode(sys.stdin.encoding))

    def opt_passwd(self, filename):
        self.addChecker(checkers.FilePasswordDB(filename))

def makeService(config):
    credCheckers = config.get('credCheckers', [])
    wordsRealm = service.InMemoryWordsRealm(config['hostname'])
    wordsPortal = portal.Portal(wordsRealm, credCheckers)
    msvc = MultiService()
    for plgName in config.interfacePlugins:
        port = config.get(plgName + '-port')
        if port is not None:
            factory = config.interfacePlugins[plgName].getFactory(wordsRealm, wordsPortal)
            svc = strports.service(port, factory)
            svc.setServiceParent(msvc)
    for g in config['groups']:
        wordsRealm.createGroup(g)

    return msvc
