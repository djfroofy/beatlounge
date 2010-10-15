import random


def cycleCycle(cycles):
   for cycle in cycles:
        for next in cycle:
            yield next 


def randomCycleCycle(cycles):
    while 1:
        cycle = random.choice(cycles)
        for next in cycle:
            yield next


