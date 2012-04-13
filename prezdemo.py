# Yeah, we learn about arpegiators ...

from itertools import cycle, combinations
import random

from bl.arp import RandomArp, OrderedArp, Adder
from bl.player import SchedulePlayer, Player, N, R
from bl.rudiments import FiveStrokeRoll, RudimentSchedulePlayer
from bl.instrument.fsynth import Layer, Instrument
from bl.scheduler import clock

from tutor.complib import bass_f, kit_f


C, Cs, D, Eb, E, F, Fs, G, Gs, A, As, B = range(12)
major_scale = [C, D, E, F, G, A, B]
triads = combinations(major_scale, 3)


dtt = clock.meter.dtt

notes1 = Adder(RandomArp())
#for i in range(128):

notes1.reset([60, 60, 62, 60, 60, 60, 60, 61, 48, 50, 60, 60, 60, 60, 60, 71,
              60, 60,60,60,60,60,60,50])
notes1.amount = -18
velocity1 = Adder(OrderedArp([120,80,89,83,120,120,80,79]))
bass = Instrument('sf2/bass/PV_SynBass1.sf2', connection='mono')
bass.controlChange(expression=86, reverb=50)
bass_player = Player(bass, notes1, velocity1,
                          stop=lambda: random.randint(12,60),
                          interval=dtt(1,16))
#bass_player.startPlaying()


notes2 = Adder(RandomArp())
notes2.reset([45, 47])
notes2.amount = 0
velocity2 = Adder(OrderedArp([120,80,120,83,120,110,90,100]))
kit = kit_f()
kit.controlChange(expression=90, reverb=120, chorus=90)
kit_player = Player(kit, notes2, velocity2, stop=lambda: random.randint(1,4),
                interval=dtt(1,16))
#kit_player.startPlaying()

clubkit = Instrument('sf2/drum/hs_magic_techno_drums.sf2')
clubkit.controlChange(reverb=127, sustain=100, chorus=120, expression=127)
fsr = FiveStrokeRoll()
clubkit_player = RudimentSchedulePlayer(clubkit, fsr, 35, 25)

# Now we see how we can set up a simple "process" to change the key periodically

#keys = cycle([-18] * 8 + [-18,-37,-18,-37] * 4 + [-18,-26,-18,-26,-37,-26,-18])
#def change_key():
#    notes1.amount = keys.next()
#change_key_event = clock.schedule(change_key)
#change_key_event.startAfter((1,1), (1,1))

octaves = [36,48] * 4 + [60]
rc = lambda : random.choice(major_scale) + random.choice(octaves)
phrases = [[rc(), rc(), rc(), rc(), rc(), rc(), rc(), rc()] for i in range(128)]
arp = Adder(OrderedArp(phrases[0]))


def change_phrase(arp, phrases):
    for i in range(128):
        phrase = random.choice(phrases[i:])
        for j in range(8):
            phrase2 = []
            for (i1, i2) in zip([phrase[j]] * 4  + [phrase[-j]] * 4, phrase):
                phrase2.extend([i1,i2])
            arp.reset(phrase2[:8] + phrase + phrase2[8:] + phrase)
            print arp.values
            yield


actor = clock.schedule(change_phrase(arp, phrases).next)
actor.startAfter((1,1), (4,1))

moog = Instrument('sf2/synth/moogbazz.sf2', connection='mono')
moog_player = Player(moog, arp,
                     OrderedArp([127,R(80,50,50,120),120,R(70,120),R(90,110,120),R(76,100),120,90]),
                     stop=(lambda: random.randint(12,24)), interval=dtt(1,8))

# TODO say some things with some enthusiasm ... late
