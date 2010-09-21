#!/usr/bin/env python

import fluidsynth

from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from common import Enunciator, PatternGenerator, BeatGenerator

import constants


#e1 = Enunciator(sf2path='sf2/Ob-3.sf2')
#e2 = Enunciator(sf2path='sf2/english_organ.sf2', channel=1)
#e3 = Enunciator(sf2path='sf2/hs_magic_techno_drums.sf2', channel=2)
e4 = Enunciator(sf2path='sf2/arab.sf2')


#p1 = PatternGenerator(e1)
#p2 = PatternGenerator(e2, noteweights=[('B', 8), ('F', 4), ('A', 8), ('D', 12), ('C', 10), ('E', 10), ('G', 10)])
#p3 = PatternGenerator(e3, noteweights=constants.all_equal())
b1 = BeatGenerator(e4)


#pattern1 = p1.get_generator()
#pattern2 = p2.get_generator()
#pattern3 = p3.get_generator()

beat1 = b1.get_generator()

def conduct_16th():
    beat1.next()

def conduct_8th():
    #pattern3.next()

    pass

def conduct_4th():
    pass
def conduct_half():
    #pattern2.next()

    pass

def conduct_whole():
    #pattern1.next()

    pass

def conduct_measure():
    #pattern2.next()

    pass


if __name__ == '__main__':
    lc16th = LoopingCall(conduct_16th)
    lc8th = LoopingCall(conduct_8th)
    lc4th = LoopingCall(conduct_4th)
    lchalf = LoopingCall(conduct_half)
    lcwhole = LoopingCall(conduct_whole)
    lcmeasure = LoopingCall(conduct_measure)

    reactor.callWhenRunning(lc16th.start, 0.125, True)
    reactor.callWhenRunning(lc8th.start, 0.25, True)
    reactor.callWhenRunning(lc4th.start, 0.5, True)
    reactor.callWhenRunning(lchalf.start, 1.0, True)
    reactor.callWhenRunning(lcwhole.start, 2.0, True)
    reactor.callWhenRunning(lcmeasure.start, 8.0, True)

    reactor.run()


