from bl.arp import ScheduleArp, TimingArp, OrderedArp
from bl.ugen import LinearOsc
from bl.orchestra.midi import Player

from tutor.complib import drums_f


time = ScheduleArp(TimingArp([(0, 8), (1, 8), (1, 8), (1, 16), (1, 16),
                              (1, 16), (1, 16)] + [(1, 32)] * 8))
drums = drums_f()
velocity = LinearOsc([((0, 1), 120), ((1, 4), 70), ((1, 4), 127),
                      ((1, 4), 80)])
note = OrderedArp([46])
player = Player(drums, note, velocity=velocity, time=time)
player.resumePlaying()

# >>> t = time.values
# >>> time.reset([(0,8),(1,8)] + [(1,32)] * 4 + [(1,8), (1,8)] +
#                [(1,16)] * 4 + [(1,32)] * 4)
# >>> time.reset([(0,8),(1,8)] + [(1,16)] * 4 + [(1,8), (1,8)] + [(1,16)] * 4)
# >>> time.reset([(0,8),(1,8)] + [(1,32)] * 4 + [(1,8), (1,8)] + [(1,16)] * 4 +
#                [(1,32)] * 4)
# >>> time.reset(t)
