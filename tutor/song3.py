# Yeah, we learn about arpegiators ...

from itertools import cycle
import random

from bl.arp import RandomArp, OrderedArp, Adder
from bl.player import Player
from bl.instrument.fsynth import Layer
from bl.scheduler import clock

from tutor.complib import bass_f, kit_f

notes = Adder(RandomArp())
notes.reset([60, 60, 62, 60, 60, 60, 60, 61, 48, 50, 60, 60, 60, 60, 60, 71, 60,
             60,60,60,60,60,60,50])
notes.amount = -18

velocity = Adder(OrderedArp([120,80,89,83,120,120,80,79]))

bass = bass_f()
kit = kit_f()
layer = Layer([bass, kit])

player = Player(layer, notes, velocity, stop=lambda: random.randint(12,60),
                interval=0.0625)
player.startPlaying()


# Now we see how we can set up a simple "process" to change the key periodically

keys = cycle([-18] * 8 + [-18,-37,-18,-37] * 4 + [-18,-26,-18,-26,-37,-26,-18])
def change_key():
    notes.amount = keys.next()
change_key_event = clock.schedule(change_key)
change_key_event.startLater(1, 1)


# TODO say some things with some enthusiasm ... late
