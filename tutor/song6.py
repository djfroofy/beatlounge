from bl.scheduler import clock, Meter
from bl.arp import ScheduleArp, OrderedArp
from bl.ugen import LinearOsc
from bl.orchestra.midi import Player

from tutor.complib import drums_f


time = ScheduleArp([(1, 8),
                    (1, 8),
                    (1, 16),
                    (1, 16),
                    (1, 16),
                    (1, 16)] +
                    [(1, 32)] * 8,
                    meter=Meter(3, 4, tempo=clock.meter.tempo))
drums = drums_f()
#velocity = LinearOsc([((0, 1), 127), ((1, 4), 70), ((1, 8), 115), ((1, 8), 120)],
#                     duration=(3, 4))
velocity = OrderedArp([127])
#,80,120,80,120,80, 120,70,90,70,127,70,110,80])
note = OrderedArp([46])
player = Player(drums, note, velocity=velocity, time=time)
player.resumePlaying()
