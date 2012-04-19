# Yeah, we learn about arpegiators ...
# And then rudiments

from itertools import cycle
import random

from bl.arp import OrderedArp, OctaveArp, Adder
from bl.orchestra.midi import Player
from bl.instrument.fsynth import Layer
from bl.scheduler import clock
from bl.rudiments import FiveStrokeRoll, RudimentSchedulePlayer

from tutor.complib import piano_f, kit_f


dtt = clock.meter.dtt

notes = Adder(OctaveArp(OrderedArp([60, 48, 62, 64, 69, 71, 46])))
notes.arp.octaves = 2
notes.arp.oscillate = True
notes.amount = 12

velocity = Adder(OrderedArp([120,80,89,83,120,120,80,79]))

piano = piano_f()
pianoPlayer = Player(piano, notes, velocity,
                     release=lambda: random.randint(12,60),
                     interval=dtt(1,16))
pianoPlayer.resumePlaying()


kit = kit_f()
drumRudiment = FiveStrokeRoll()
drumPlayer = RudimentSchedulePlayer(kit, drumRudiment, 51, 48)
drumPlayer.resumePlaying()

# Now we see how we can set up a simple "process" to change the key periodically

keys = cycle([-18] * 8 + [-18,-37,-18,-37] * 4 + [-18,-26,-18,-26,-37,-26,-18])
def change_key():
    notes.amount = keys.next()
change_key_event = clock.schedule(change_key)
change_key_event.startAfter((1,1), (1,1))


# TODO say some things with some enthusiasm ... late
