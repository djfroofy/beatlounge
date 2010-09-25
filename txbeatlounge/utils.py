import random

from txbeatlounge import constants


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
    '8trip': 1/12.,
    '16th': 1/8.,
    '8th': 1/4.,
    'qtrup': 1/3.,
    'quarter': 1,
    'half': 2,
    'whole': 4,
}

def clock_converter(bpm, space):
    return (60./bpm) * spaces[space]

