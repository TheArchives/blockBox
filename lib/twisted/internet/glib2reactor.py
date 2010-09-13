from lib.twisted.internet import gtk2reactor

class Glib2Reactor(gtk2reactor.Gtk2Reactor):
    def __init__(self):
        gtk2reactor.Gtk2Reactor.__init__(self, useGtk=False)

def install():
    reactor = Glib2Reactor()
    from lib.twisted.internet.main import installReactor
    installReactor(reactor)
    
__all__ = ['install']

