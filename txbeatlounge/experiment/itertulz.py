import random

from warnings import warn

warn('itertulz is deprecated - for randomCycleCycle use player.randomPhrase')

def cycleCycle(cycles):
   for cycle in cycles:
        for next in cycle:
            yield next 


def randomCycleCycle(cycles):
    while 1:
        cycle = random.choice(cycles)
        for next in cycle:
            yield next


