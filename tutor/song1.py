###############################################################################
# SONG 1
# ======
#
# Our first song is a simple one. We find a room with some instruments, take a
# seat at the piano and start striking random notes with haphazard force on
# each quaver.
#
# ~~---<<<>>>---~~~<><><>~~~---<<<>>>---~~~<><><>~~~---<<<>>>---~~~<><><>~~~---

import os.path
import random

from bl.scheduler import clock
from bl.instrument.fsynth import Instrument


SF2DIR = os.path.join(os.path.dirname(__file__), 'sf2')


# First let's find an instrument to play with!
#
# What's in our sf2 directory ... hrm ... bass.sf2 ... piano.sf2 ... kit.sf2
# ...
#
# Note that in future songs we'll import some convenience functions defined in
# tutor.complib (piano_f, drums_f, bass_f) to create the instrument instances
# for us.

instrument = Instrument(os.path.join(SF2DIR, 'piano.sf2'))


# Let's define some musical intervals in terms for virtual clock ticks
# Meter.divisionToTicks() API. Note that dtt() is a shorthand alias for
# divisionToTicks()

meter = clock.meter
quaver = meter.dtt(1,8)
quarter = meter.dtt(1,4)
half = meter.dtt(1,2)
one_and_half = meter.dtt(3,2)
scale = range(36, 84)

def hitsomenote():


    # We have no clue what to do with this piano. Let's just
    # hit a note with some random amount of force.

    note = random.choice(scale)
    velocity = random.randint(40, 127)
    instrument.playnote(note, velocity)


    # And we'll take our finger off ... some time later
    release = random.choice((quaver, quarter, half, one_and_half))
    clock.callLater(release, instrument.stopnote, note)


event = clock.schedule(hitsomenote)
event.startAfter((1,1), (1,8))


# Now try this exercise from the shell.
#
# >>> event.stopLater(1) # Stop on the next measure
# >>> event.startLater(1, 0.0625) # restart, but this time every semiquaver

# Also try redfining scale to something less ... random.
# Here's another example to play with

def harmonize(steps):
    current = 0
    for step in steps:
        current += step
    return steps + [ divmod(current, 12)[1] ]

random_steps = [
        random.choice([2,2,3,4,4,4,4]), random.choice([2,2,4,3,3,3,3]),
        random.choice([3,4,2,2,2,2,2]), random.choice([4,3,1,2,2,2,2])]
random_steps = harmonize(random_steps)

random_start = random.randint(36,48)

def use_scale(steps, start, repeat=2):
    global scale
    print 'using steps', steps
    print 'using start', start
    new_scale = [start]
    for _ in range(repeat):
        for step in steps:
            new_scale.append(new_scale[-1] + step)
    print 'new scale', new_scale
    scale = new_scale

# Now call use_scale(random_steps, random_start)
#
# Then try playing some with your own values instead of random_steps
# and random_start.

clock.callAfterMeasures(4, use_scale, random_steps, random_start)

