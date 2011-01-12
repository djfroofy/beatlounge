"""
#. Runs a websocket server that talks to the beatlounge console.

built on https://github.com/rlotun/txWebSocket
"""

import argparse
import StringIO, sys, time
from datetime import datetime
import pprint

from twisted.internet.protocol import Protocol, Factory
from twisted.python import log
from twisted.web import resource
from twisted.web.static import File
from twisted.internet import task
from twisted.conch.manhole import ManholeInterpreter

from websocket import WebSocketHandler, WebSocketSite

from txbeatlounge.console import consoleNamespace

class CodeHandler(WebSocketHandler):

    special_messages_to_method = {'restart': 'restart'}

    def __init__(self, transport):
        WebSocketHandler.__init__(self, transport)
        self.startInterpreter()

    def startInterpreter(self):
        log.msg('starting interpreter')
        self.interpreter = ManholeInterpreter(self)
        self.interpreter.locals = dict(consoleNamespace)
        pp = pprint.PrettyPrinter(indent=2)
        pp = pp.pprint
        self.interpreter.locals['pp'] = pp

    def __del__(self):
        log.msg('Deleting handler')

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
        log.msg('Connected to client.')

    def connectionLost(self, reason):
        log.msg('Lost connection.')
        log.err(reason)

    def restart(self):
        """
        Method that doesn't work @drew TODO :)

        I'm working on it ... sort of (in my head now) - but i think the right thing to
        do is have some global registry of players and scheduled events and then stop
        everything in the registry - players, then scheduled events for plain tasks. (drew)
        """

        # NOTE
        # please don't alias clock as "reactor" anymore - i'm sorry i did
        # that before - eventually BeatClock probably shouldn't even inherit
        # from SelectReactor etc. and this get's confusing because it's hard to
        # tell one from the other in code - they're not the same (e.g. Twisted's
        # global singleton reactor and our custom reactor - BeatClock)

        #self.interpreter.runcode("reactor.task.stop()")
        #self.interpreter.runcode("""
#from txbeatlounge.instrument.fsynth import ChordPlayerMixin
#l = locals()
#for v in l.values():
#    if isinstance(v, ChordPlayerMixin):
#        v.stopall()
#
#""")
#        self.interpreter = None
        #time.sleep(3)
        #self.startInterpreter()



if __name__ == "__main__":
    from twisted.internet import reactor
    from txbeatlounge.scheduler import clock
    
    # Note, the port will need to be changed in the index.html
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=8080)
    args = parser.parse_args()
    port = int(args.p)

    log.startLogging(sys.stdout)

    root = File('.')
    site = WebSocketSite(root)
    site.addHandler('/code', CodeHandler)
    reactor.listenTCP(port, site, interface='127.0.0.1')
    reactor.callWhenRunning(clock.run)
    reactor.run()

