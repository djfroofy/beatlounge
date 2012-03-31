###############################################################################
# SONG 2
# ======
#
# Von Sprechenreit walks into the room and sees you sitting at the piano
# desperately trying to smash out a tune. That's all lost visitors initially
# can do after stumbling upon his little room at its convoluted arragement of
# instruments and whimsical inventions. He looks at you somewhat half annoyment
# and half in elated appreciation of your new-found endeavour to understand
# some aspects of his little quicky world.
#
# VS: "Ah, I see zie hast found die piano, but hasn't zie looked more in meine
# code? Du must instantiate eine Player instance! Es vil save you so much time,
# Ja!"
#
# You look on old Sprechenreit with a bit of confusion as he speaks ... But
# this Player thing sounds rather intriguing ...
#
# ~~---<<<>>>---~~~<><><>~~~---<<<>>>---~~~<><><>~~~---<<<>>>---~~~<><><>~~~---

import random
from itertools import cycle

from bl.player import Player, R, N
from tutor.complib import piano_f


# VS: "Ja let's use meine convenience function ... instead"
#
#instrument = Instrument(sf2('piano.sf2'))

piano = piano_f()


# Sprechenreit explains to you that Players can take a generator of
# numbers for both notes and velocities and then you don't have to
# work with the lower-level BeatClock interface. "Es ist zher super abstraction
# layer!!"
#
# First let's start by making a generator for our notes. Sprechereit also
# points out the R or Random function which creates a callable that returns
# some random value for the arguments we provide; yes, just a partial of
# random.choice(), if you care. Also N is special function to represent and
# return None (this translates to a pause in playing).

notes = cycle([R(60, 64, 67, 69), R(36, 48, 60, N), R(48, 52, 55),
               R(36, 40, 43, 45)])


# Next we'll create a callable for our velocity.

velocity = cycle([120, 80, 89, 83]).next


# Finally let's create a Player whick takes as its arguments (amongst, some
# other things), the notes generator and veocity functions from above. The
# argument stop is function which returns a "release" time (for stop notes
# played). The interval is the interval between note plays.

player = Player(piano, notes, velocity, stop=lambda: random.randint(12, 48),
                interval=0.25)


player.startPlaying()

# Now try this exercise from the shell.
#
# player.stopPlaying() # Stop on the next measure
# player.interval = 0.125
# player.startPlaying()
# player.instr = bass_f()
