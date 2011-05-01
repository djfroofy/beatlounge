"""
Herein we derive offsets from equal temperament to pythagorean, just ratios.

Some authors define the Indian shruti system as a combination of pythagorean and just tuning.
We are among these authors.
"""

from bl.music.constants import twelve_tone_equal_440


__all__ = ['just', 'pythagorean', 'shrutis', 'offsets', 'centsMultiplier']


pythagorean = {
    0: 1/1.,
    1: 256/243.,
    2: 9/8.,
    3: 32/27.,
    4: 81/64.,
    5: 4/3.,
    6: 729/512.,
    7: 3/2.,
    8: 128/81.,
    9: 27/16.,
    10: 16/9.,
    11: 243/128.,
}

just = {
    0: 1/1.,
    1: 16/15.,
    2: 10/9.,
    3: 6/5.,
    4: 5/4.,
    5: 4/3.,
    6: 45/32.,
    7: 3/2.,
    8: 8/5.,
    9: 5/3.,
    10: 9/5.,
    11: 15/8.,
}

more = {}
for k,v in pythagorean.iteritems():
    more[k+12] = v*2
pythagorean.update(more)

more = {}
for k,v in just.iteritems():
    more[k+12] = v*2
just.update(more)


shrutis = {}

for k,v in just.iteritems():
    shrutis[k] = []
    shrutis[k].append(v)

for k,v in pythagorean.iteritems():
    shrutis[k].append(v)


offsets = {}
for k, v in shrutis.iteritems():
    offsets[k] = []
    for val in v:
        offsets[k].append(440.*val/twelve_tone_equal_440[57+k])


def centsMultiplier(cents):
    return 2**(cents/1200.)


