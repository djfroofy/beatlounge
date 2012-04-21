from itertools import cycle

from bl.ugen import W
from bl.arp import ChordPatternArp, OrderedArp, RandomArp, ArpMap
from bl.scheduler import clock
from bl.orchestra.midi import ChordPlayer

from tutor.complib import piano_f


pattern = [3, 3, [3, 1], 1, 2, 1, 2, 1, [3, 2, 1, 0, 4], 0, 1, 2, 3, 4, 3, 2,
           [3, 2], 0, 0, [0, 1, 2], 2, 1, 2, 0, [0, 1, 2, 3], 3, 2, 1, 0,
           [5, 4, 1], 5, 4, 3, 4, 2, 1, 5, 0, [5, 0]]

notes = cycle([[38, 50, 62, 65, 69, 80],
               [38, 50, 62, 65, 69, 84],
               [38, 50, 62, 65, 67, 84],
               [38, 50, 62, 65, 69, 84],
               [36, 50, 62, 65, 69, 84],
               [36, 55, 62, 65, 69, 84],
               [36, 55, 62, 67, 69, 84],
               [36, 55, 60, 67, 69, 84],
               [36, 53, 55, 67, 69, 84],
               [36, 53, 55, 67, 69, 81],
               [36, 53, 55, 65, 69, 81],
               [36, 53, 55, 65, 67, 81],
               [38, 53, 55, 65, 67, 81],
               [38, 53, 55, 67, 69, 81],
               [38, 53, 55, 67, 69, 74],
               [38, 53, 55, 65, 67, 74],
               [36, 53, 55, 65, 67, 74],
               [36, 55, 57, 65, 67, 74],
               [36, 55, 57, 60, 67, 74],
               [36, 55, 57, 60, 64, 74],
               [36, 55, 57, 60, 64, 80],
               [36, 55, 57, 60, 64, 81],
               [36, 55, 57, 60, 64, 84],
               [36, 55, 57, 60, 63, 84],
               [36, 55, 57, 60, 64, 84],
               [36, 55, 57, 60, 69, 84],
               [36, 55, 57, 60, 69, 81],
               [36, 55, 57, 60, 69, 78],
               [36, 53, 55, 60, 69, 78],
               [36, 53, 55, 62, 69, 78]])

piano = piano_f()
piano.controlChange(reverb=120, sustain=100, chorus=50, vibrato=15)

r = W((0, 5), (12, 2), (-12, 3))
f = lambda chord: [r() + n for n in chord]
arp = ArpMap(f, ChordPatternArp(notes.next(), pattern))

player = ChordPlayer(piano, arp,
                     velocity=OrderedArp([127, 80, 90, 80, 90, 120, 120, 80]),
                     release=RandomArp([11, 10, 9, 8]))
resetter = clock.schedule(lambda: arp.reset(notes.next())
        ).startAfter((2, 1), (2, 1))
player.resumePlaying()
