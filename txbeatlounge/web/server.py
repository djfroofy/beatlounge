"""
#. Runs a websocket server that talks to the beatlounge console.

built on https://github.com/rlotun/txWebSocket
"""

import StringIO, sys, time
from datetime import datetime
import pprint

from twisted.internet.protocol import Protocol, Factory
from twisted.python import log, usage
from twisted.web import resource
from twisted.web.static import File
from twisted.internet import defer, task
from twisted.conch.manhole import ManholeInterpreter

from websocket import WebSocketHandler, WebSocketSite

from txbeatlounge.console import consoleNamespace

class ReallyStupidHostKeyVericationUIMixinRewriteMePlease(object):
    """
    This class is just some skeleton code to make consoleConnect()
    work but needs to be replaced with something that's ummm secure
    so the user can verify hosts, rather than doing it under the hood.
    
    Read docstrings below for information on what needs to be implemented.
    """

    session = None

    def writeHelp(self, message):
        """
        This should push some help text to the user's web browser
        and display somewhere in the UI. Generally we're just going
        to need this for the standard yes/no prompt text to accept
        a host's identity. 
        """
        log.msg('writeHelp: %s' % message)

    warn = writeHelp

    def prompt(self, message):
        """
        This should actually notify the UI and let the user verify
        the identity of the host. A popup or something.
        """
        return defer.succeed(True)


class CodeHandler(WebSocketHandler, ReallyStupidHostKeyVericationUIMixinRewriteMePlease):

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
        self.interpreter.locals['console'] = self

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
            if self.session:
                self._forwardRemote(frame)

    def _forwardRemote(self, frame):
        log.msg('forwarding frame to remote: %r' % frame)
        for line in frame.splitlines():
            line2 = line.strip()
            if not line2: continue
            self.session.write(line2 + '\r\n')
            

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


    

class Options(usage.Options):
    optParameters = [['port', 'p', 8080, 'Port to listen on', int],
                     ['interface', 'i', '127.0.0.1', 'Interface to listen on'],
                     ['audio-dev', 'a', 'coreaudio', 'Audio device']]

if __name__ == "__main__":
    from twisted.internet import reactor
    from txbeatlounge.scheduler import clock
    
    # Note, the port will need to be changed in the index.html
    options = Options()
    options.parseOptions()
    port = options['port']
    interface = options['interface']
    
    clock.synthAudioDevice = options['audio-dev']

    log.startLogging(sys.stdout)

    root = File('.')
    site = WebSocketSite(root)
    site.addHandler('/code', CodeHandler)
    reactor.listenTCP(port, site, interface=interface)
    reactor.callWhenRunning(clock.run)
    reactor.run()

