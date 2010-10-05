import random

from txbeatlounge import constants



def percindex(r, lst):
    '''Given 0<=r=<1, get the item of the list'''

    return lst[int(len(lst)*r)]


def windex(lst):
    '''an attempt to make a random.choose() function that makes weighted choices

    accepts a list of tuples with the item and probability as a pair'''

    wtotal = sum([x[1] for x in lst])
    n = random.uniform(0, wtotal)
    for item, weight in lst:
        if n < weight:
            break
        n = n - weight
    return item

def midi_to_letter(midi):
    for l in constants.NOTES:
        if midi in getattr(constants, l):
            return l



spaces = {
    '8trip': 1/6.,
    '16th': 1/4.,
    '8th': 1/2,
    'qtrup': 1/3.,
    'quarter': 1,
    'half': 2,
    'whole': 4,
}

def clock_converter(bpm, space):
    return (60./bpm) * spaces[space]


def random_onoff(event, likelihood=[1,0], frequency=0.125):
    if not hasattr(event, 'playing'):
        event.playing = True
    if random.choice(likelihood):
        if event.playing:
            event.stop_at_interval(0)
            event.playing = False
        else:
            event.start(frequency)
            event.playing = True


