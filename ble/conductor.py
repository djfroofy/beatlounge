from zope.interface import Interface, implements

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
            musician.stopPlaying(node)
        for musician in next["musicians"]:
            musician.startPlaying(node)
        self.currentNode = next
        self.clock.callAfterMeasures(duration, self._resume, None) 
        


def weight(edges):
    l = []
    for k in edges:
        l.extend([k[0] for i in range(k[1])]) 
    random.shuffle(l)
    return l



class IMusician(Interface):
    
    def startPlaying(node):
        """
        Schedule play events based on current node in score.
        """

    def stopPlaying(node):
        """
        Stop play events based on current node in score.
        """

class PlayerMusician(object):
    implements(IMusician)

    def __init__(self, players):
        self.players = players
        self.player = None

    def startPlaying(self, node):
        self.player = self.players[node]
        self.player.startPlaying(node)

    def stopPlaying(self, node):
        self.player.stopPlaying(node)

Musician = PlayerMusician


def _getclock(clock):
    if clock is None:
        from txbeatlounge.scheduler import clock
    return clock 
