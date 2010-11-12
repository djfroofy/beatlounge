import random


DEBUG = False

class Conductor(object):


    def __init__(self, scoreGraph, clock=None):
        self.clock = _getclock(clock)
        self.scoreGraph = scoreGraph
        self.currentNode = {'musicians':()}

    def start(self):
        node = self.scoreGraph[None]
        self._resume(node)

    def _resume(self, node):
        schedule = self.clock.schedule
        if node is None:
            node = random.choice(self.currentNode['transitions'])
        next = self.scoreGraph[node]
        if DEBUG:
            print 'transitioning', next
        duration = next["duration"]
        for musician in self.currentNode.get('musicians', ()):
            musician.stop(node)
        for musician in next["musicians"]:
            musician.start(node)
        self.currentNode = next
        self.clock.callAfterMeasures(duration, self._resume, None) 
        


def weight(edges):
    l = []
    for k in edges:
        l.extend([k[0] for i in range(k[1])]) 
    random.shuffle(l)
    return l


class PlayerMusician(object):

    def __init__(self, players):
        self.players = players
        self.player = None

    def start(self, node):
        self.player = self.players[node]
        self.player.startPlaying()

    def stop(self, node):
        self.player.stopPlaying()

Musician = PlayerMusician


def _getclock(clock):
    if clock is None:
        from txbeatlounge.scheduler2 import clock
    return clock 
