"""

"""
import json

from twisted.web.static import File
from websocket import WebSocketHandler, WebSocketSite


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
        self.transport.write(json.dumps(self.values))

    def connectionLost(self, reason):
        print 'Lost connection.', reason
        self.transports.remove(self.transport)




class StepHandler(BaseHandler):
    """
    values will be like:

    {
        <tick>: [note,note,note],

    }
    """

    values = {}
    transports = []

    def frameReceived(self, frame):
        """<1-384>-<1-127>::<1-127>"""

        print "frame:", frame
        tick, values = frame.split('-')
        tick = tick
        print tick, values

        values = [int(v) for v in values.split(',') if v]
        if values:
            self.values[tick] = values
        else:
            del self.values[tick]

        print self.values

        for t in self.transports:
            t.write(json.dumps(self.values))

    @classmethod
    def factory(self):
        #l = sorted(self.values.values(), key=lambda i: i[0])

        l = []
        for k,v in self.values.iteritems():
            # TODO, put vol, sus in UI instead of hardcoding to 100,24
            item = [int(k), v, 100,24]
            l.append(item)

        l = sorted(l, key=lambda i: i[0])
        print l
        return l




class VolumeHandler(BaseHandler):

    values = {}
    transports = []

    def frameReceived(self, frame):
        print "VolumeHandler frame:", type(frame)

        # TODO better algo
        values = json.loads(frame)
        #print type(values)
        for k,v in values.iteritems():
            self.values[int(k)] = int(v)

        for t in self.transports:
            t.write(json.dumps(self.values))

        #print self.values


class SusHandler(VolumeHandler):
    values = {}
    transports = []


class StepVolumeFactory(object):

    def __init__(self, stephandler, volumehandler):
        self.stephandler = stephandler
        self.volumehandler = volumehandler

    def factory(self):
        svalues = self.stephandler.values
        vvalues = self.volumehandler.values
        print svalues
        print vvalues

        l = []
        for k,v in svalues.iteritems():
            vol = vvalues.get(int(k), 100)
            item = [int(k), v, vol, 24] # StepVolumeSustainFactory .. 
            #yield item <-- how do I get this type of thing going on?
            l.append(item)
        l = sorted(l, key=lambda i: i[0])
        print l
        return l



class ListHandler(BaseHandler):
    values = []
    transports = []

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
    values = []
    transports = []
    arps = []

    def frameReceived(self, frame):
        ListHandler.frameReceived(self, frame)
        for a in self.arps:
            a.reset(self.values)


class ValuesHandler(BaseHandler):
    """keeps a dict in stead of a list as ListHandler"""

    values = {}
    transports = []

    def connectionMade(self):
        BaseHandler.connectionMade(self)

        if self.values:
            self.transport.write(json.dumps(self.values))


    def frameReceived(self, frame):
        """value should be as <slider-num>-<value>"""

        print 'ValuesHandler.frameReceived: ', frame
        index, value = frame.split('-')
        self.values[index] = value
        for t in self.transports:
            t.write(json.dumps(self.values))


class ControlChangeHandler(ValuesHandler):
    """
    values dict values are ints 0-127,
    keys are: vibrato, volume, pan, expression, sustain, reverb, chorus.
    """

    values = {}
    instrs = []

    def frameReceived(self, frame):
        ValuesHandler.frameReceived(self, frame)

        print frame
        kwargs = {}
        k, v = frame.split('-')
        kwargs[k] = int(v)

        for i in self.instrs:
            i.controlChange(**kwargs)




import os.path
HERE = os.path.dirname(__file__)

def start():

    from twisted.internet import reactor
    from bl.utils import getClock
    clock = getClock()
    root = File(HERE)
    site = WebSocketSite(root)
    site.addHandler('/list', ArpHandler)
    site.addHandler('/cc', ControlChangeHandler)
    site.addHandler('/step', StepHandler)
    site.addHandler('/vol', VolumeHandler)
    site.addHandler('/vol', SusHandler)
    reactor.listenTCP(8347, site)



if __name__ == "__main__":
    start()
