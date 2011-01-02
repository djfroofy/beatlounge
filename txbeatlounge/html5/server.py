"""
#. Runs a websocket server that talks to the beatlounge console.

built on https://github.com/rlotun/txWebSocket
"""
from datetime import datetime

from twisted.internet.protocol import Protocol, Factory
from twisted.web import resource
from twisted.web.static import File
from twisted.internet import task

from websocket import WebSocketHandler, WebSocketSite

class Handler(WebSocketHandler):
    def __init__(self, transport):
        WebSocketHandler.__init__(self, transport)

    def __del__(self):
        print 'Deleting handler'

    def send_foo(self, foo="foo"):
        self.transport.write(foo)

    def frameReceived(self, frame):
        """ """
        print 'Peer: ', self.transport.getPeer()
        print frame
        self.transport.write(frame)

    def connectionMade(self):
        print 'Connected to client.'

    def connectionLost(self, reason):
        print 'Lost connection.'


if __name__ == "__main__":
    from twisted.internet import reactor

    # run our websocket server
    # serve index.html from the local directory
    root = File('.')
    site = WebSocketSite(root)
    site.addHandler('/tcp', Handler)
    reactor.listenTCP(8080, site)
    # run policy file server
    #factory = Factory()
    #factory.protocol = FlashSocketPolicy
    #reactor.listenTCP(843, factory)
    reactor.run()

