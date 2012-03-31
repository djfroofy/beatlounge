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


def hitsomenote():


    # We have no clue what to do with this piano. Let's just
    # hit a note with some random amount of force.

    note = random.randint(36, 84)
    velocity = random.randint(40, 127)
    instrument.playnote(note, velocity)


    # And we'll take our finger off ... some time later

    release = random.choice((0.125, 0.25, 0.5, 1, 1.5))
    clock.callAfterMeasures(release, instrument.stopnote, note)


event = clock.schedule(hitsomenote)
event.startLater(1, 0.125)


# Now try this exercise from the shell.
#
# >>> event.stopLater(1) # Stop on the next measure
# >>> event.startLater(1, 0.0625) # restart, but this time every semiquaver
