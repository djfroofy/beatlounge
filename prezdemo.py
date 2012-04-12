# Yeah, we learn about arpegiators ...

from itertools import cycle
import random

from bl.arp import RandomArp, OrderedArp, Adder
from bl.player import SchedulePlayer, Player, N, R
from bl.rudiments import FiveStrokeRoll
from bl.instrument.fsynth import Layer, Instrument
from bl.scheduler import clock

from tutor.complib import bass_f, kit_f


def loadInstrument(path):
    return Instrument(path, connection='mono')


dtt = clock.meter.dtt

notes1 = Adder(RandomArp())
notes1.reset([60, 60, 62, 60, 60, 60, 60, 61, 48, 50, 60, 60, 60, 60, 60, 71,
              60, 60,60,60,60,60,60,50])
notes1.amount = -18
velocity1 = Adder(OrderedArp([120,80,89,83,120,120,80,79]))
bass = Instrument('sf2/bass/PV_SynBass1.sf2', connection='mono')
bass.controlChange(expression=86, reverb=50)
bass_player = Player(bass, notes1, velocity1,
                stop=lambda: random.randint(12,60),
                interval=dtt(1,16))
bass_player.startPlaying()


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
fsr = FiveStrokeRoll()
timing = fsr.time(6, cycle=True)
strokes = fsr.strokes(24, 25, cycle=False)
notes3 = OrderedArp(list(strokes))
velocity3 = OrderedArp([127,90,110,97,120,60,125,98])
sustain = cycle([None])
schedule = ((timing.next(), notes3(), velocity3(), sustain.next())
            for i in cycle([0]))
clubkit_player = SchedulePlayer(clubkit, lambda : schedule)

# Now we see how we can set up a simple "process" to change the key periodically

#keys = cycle([-18] * 8 + [-18,-37,-18,-37] * 4 + [-18,-26,-18,-26,-37,-26,-18])
#def change_key():
#    notes1.amount = keys.next()
#change_key_event = clock.schedule(change_key)
#change_key_event.startAfter((1,1), (1,1))


# TODO say some things with some enthusiasm ... late
