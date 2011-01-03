"""
#. Runs a websocket server that talks to the beatlounge console.

built on https://github.com/rlotun/txWebSocket
"""

import StringIO, sys
from datetime import datetime

from twisted.internet.protocol import Protocol, Factory
from twisted.python import log
from twisted.web import resource
from twisted.web.static import File
from twisted.internet import task
from twisted.conch.manhole import ManholeInterpreter

from websocket import WebSocketHandler, WebSocketSite


class CodeHandler(WebSocketHandler):

    def __init__(self, transport):
        WebSocketHandler.__init__(self, transport)
        self.interpreter = ManholeInterpreter(self)
        self.interpreter.runcode("""
from txbeatlounge.scheduler import clock as reactor
reactor.synthAudioDevice = "coreaudio"
reactor.run()
#from comps.core import *
""")

    def __del__(self):
        print 'Deleting handler'

    def frameReceived(self, frame):
        """ """
        print 'Peer: ', self.transport.getPeer()
        self.interpreter.runcode(frame)

    def addOutput(self, data, async=False):
        self.transport.write(data)
        #log.msg(data)

    def connectionMade(self):
        print 'Connected to client.'

    def connectionLost(self, reason):
        print 'Lost connection.', reason
        reason.printTraceback()


if __name__ == "__main__":
    from twisted.internet import reactor
    log.startLogging(sys.stdout)

    root = File('.')
    site = WebSocketSite(root)
    site.addHandler('/code', CodeHandler)
    reactor.listenTCP(8080, site, interface='127.0.0.1')
    reactor.run()

