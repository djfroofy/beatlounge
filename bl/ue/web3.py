"""

"""
import json

from twisted.web.static import File
from websocket import WebSocketHandler, WebSocketSite


#class BaseHandler(WebSocketHandler):

class BaseHandler(WebSocketHandler):

    values = []
    transports = []

    def __init__(self, transport):
        print '__init__', transport
        WebSocketHandler.__init__(self, transport)

    def __del__(self):
        print 'Deleting handler'
        self.transports.remove(self.transport)

    def connectionMade(self):
        print 'Connected to client.'
        self.transports.append(self.transport)
        self.transport.write(self.values)

    def connectionLost(self, reason):
        print 'Lost connection.', reason
        self.transports.remove(self.transport)


class ListHandler(BaseHandler):

    def frameReceived(self, frame):
        print 'frame:', frame
        on, row, col = [int(n) for n in frame.split('-')]
        note = row*12+col
        if on:
            self.values.append(note)
        else:
            self.values.remove(note)

        for t in self.transports:
            t.write(json.dumps(self.values))


class ArpHandler(ListHandler):
    arps = []

    def frameReceived(self, frame):
        ListHandler.frameReceived(self, frame)
        for a in self.arps:
            a.reset(self.values)





class SliderHandler(WebSocketHandler):

    values = {}
    transports = []

    def __init__(self, transport):
        print '__init__', transport
        WebSocketHandler.__init__(self, transport)

    def __del__(self):
        print 'Deleting handler'
        self.transports.remove(self.transport)

    def frameReceived(self, frame):
        """value should be as <slider-num>-<value>"""
        index, value = [int(n) for n in frame.split('-')]
        self.values[index] = value
        print 'value:', frame
        print self.values
        for t in self.transports:
            t.write(json.dumps(self.values))

    def connectionMade(self):
        print 'Connected to client.'
        self.transports.append(self.transport)
        self.transport.write(self.values)

    def connectionLost(self, reason):
        print 'Lost connection.', reason
        self.transports.remove(self.transport)

import os.path
HERE = os.path.dirname(__file__)

def start():

    from twisted.internet import reactor
    from bl.utils import getClock
    clock = getClock()
    root = File(HERE)
    site = WebSocketSite(root)
    site.addHandler('/test', ArpHandler)
    site.addHandler('/slider', SliderHandler)
    reactor.listenTCP(8347, site)



if __name__ == "__main__":
    start()
