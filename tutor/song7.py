from itertools import cycle

from bl.ugen import LSystem
from bl.orchestra.midi import Player
from bl.arp import OrderedArp, OctaveArp, Adder, LSystemArp
from bl.scheduler import clock

from tutor.complib import piano_f


lsystem = Adder(LSystemArp(
        {60: [64, 67],
         67: [62, 64],
         62: [48, 53],
         64: [57, 67, 50],
         50: [60, 60, 36],
         36: [60, 48, 57],
         57: [64, 67, 69],
         55: [60, 62],
         52: [36, 50, 50],
         53: [36, 48, 62],
         69: [52, 52, 62],
         48: [52, 55, 62]},
        axiom=60))

velocity = Adder(OrderedArp([120,80,89,83,120,120,80,79]))

piano = piano_f()
piano.controlChange(reverb=120, sustain=120, chorus=100)
pianoPlayer = Player(piano, lsystem, velocity)
pianoPlayer.resumePlaying()



