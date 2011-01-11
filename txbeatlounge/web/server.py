"""
#. Runs a websocket server that talks to the beatlounge console.

built on https://github.com/rlotun/txWebSocket
"""

import argparse
import StringIO, sys, time
from datetime import datetime

from twisted.internet.protocol import Protocol, Factory
from twisted.python import log
from twisted.web import resource
from twisted.web.static import File
from twisted.internet import task
from twisted.conch.manhole import ManholeInterpreter

from websocket import WebSocketHandler, WebSocketSite

import pprint
pp = pprint.PrettyPrinter(indent=2)
pp = pp.pprint


class CodeHandler(WebSocketHandler):

    special_messages_to_method = {'restart': 'restart'}

    def __init__(self, transport):
        WebSocketHandler.__init__(self, transport)
        self.startInterpreter()

    def startInterpreter(self):
        self.interpreter = ManholeInterpreter(self)
        self.interpreter.runcode("""
from txbeatlounge.scheduler import clock as reactor
reactor.synthAudioDevice = "coreaudio"
reactor.run()
#from comps.core import *
import pprint
pp = pprint.PrettyPrinter(indent=2)
pp = pp.pprint
""")

    def __del__(self):
        print 'Deleting handler'

    def frameReceived(self, frame):
        """ """
        #print 'Peer: ', self.transport.getPeer()

        if not self.interpreter:
            self.startInterpreter()

        if frame in self.special_messages_to_method.keys():
            getattr(self, self.special_messages_to_method[frame])()
        else:
            self.interpreter.runcode(frame)

    def addOutput(self, data, async=False):
        self.transport.write(data)
        #log.msg(data)

    def connectionMade(self):
        print 'Connected to client.'

    def connectionLost(self, reason):
        print 'Lost connection.', reason
        reason.printTraceback()

    def restart(self):
        """Method that doesn't work @drew TODO :)
        """
        self.interpreter.runcode("reactor.task.stop()")
        self.interpreter.runcode("""
from txbeatlounge.instrument.fsynth import ChordPlayerMixin
l = locals()
for v in l.values():
    if isinstance(v, ChordPlayerMixin):
        v.stopall()

""")
        self.interpreter = None
        #time.sleep(3)
        #self.startInterpreter()



if __name__ == "__main__":

    # Note, the port will need to be changed in the index.html
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=8080)
    args = parser.parse_args()
    port = int(args.p)


    from twisted.internet import reactor
    log.startLogging(sys.stdout)

    root = File('.')
    site = WebSocketSite(root)
    site.addHandler('/code', CodeHandler)
    reactor.listenTCP(port, site, interface='127.0.0.1')
    reactor.run()

