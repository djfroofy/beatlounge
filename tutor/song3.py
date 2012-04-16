# Yeah, we learn about arpegiators ...

from itertools import cycle
import random

from bl.arp import RandomArp, OrderedArp, Adder
from bl.orchestra.midi import Player
from bl.instrument.fsynth import Layer
from bl.scheduler import clock

from tutor.complib import bass_f, kit_f


dtt = clock.meter.dtt

notes1 = Adder(RandomArp())
notes1.reset([60, 60, 62, 60, 60, 60, 60, 61, 48, 50, 60, 60, 60, 60, 60, 71,
              60, 60,60,60,60,60,60,50])
notes1.amount = -18
velocity1 = Adder(OrderedArp([120,80,89,83,120,120,80,79]))
bass = bass_f()
bass_player = Player(bass, notes1, velocity1,
                     release=(lambda: random.randint(12,60)),
                     interval=dtt(1,16))
bass_player.resumePlaying()


notes2 = Adder(RandomArp())
notes2.reset([60, 60, 62])
notes2.amount = -18
velocity2 = Adder(OrderedArp([120,80,120,83,120,110,90,100]))
kit = kit_f()
kit_player = Player(kit, notes2, velocity2,
                    release=(lambda: random.randint(12,60)),
                    interval=dtt(1,16))
kit_player.resumePlaying()


# Now we see how we can set up a simple "process" to change the key periodically

keys = cycle([-18] * 8 + [-18,-37,-18,-37] * 4 + [-18,-26,-18,-26,-37,-26,-18])
def change_key():
    notes1.amount = keys.next()
change_key_event = clock.schedule(change_key)
change_key_event.startAfter((1,1), (1,1))


# TODO say some things with some enthusiasm ... late
