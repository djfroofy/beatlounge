from zope.interface import implements, Interface, Attribute

import itertools

__all__ = ['IRudiment', 'FiveStrokeRoll', 'FSR',
    'SixStrokeRoll', 'SSR', 'strokeGenerator', 'timeGenerator', 'generator',
    'chainRudiments']

class IRudiment(Interface):
    """
    Primarily a rudiment supplies a generator for timeing of strokes
    (time) but can also generate reference "strokes" (notes) and
    velocity.
    """

    length = Attribute('The length of the rudiment = The number of smallest division '
                       'beats that comprise one bar of the rudiment')

    def time(ticks, cycle=False, start=0):
        """
        Generator for the relative timing for a rudiment. The timing begins and start
        and increments by the ticks or greater between strokes; i.e. the ticks argument
        is the shortest stroke in the rudiment.
        """

    def strokes(r, l, cycle=False):
        """
        Generator for the "strokes" for a rudiment. E.g. [l, r, l, r]
        """

    def velocity(cycle=False):
        """
        Generator for the velocity to accompany strokes in the rudiment.
        """


def _maybeCycle(l, cycle=False):
    if cycle:
        return itertools.cycle(l)
    return l

R = 0
L = 1


def strokeGenerator(pattern):
    def gen(self, r, l, cycle=False):
        g = ( (r,l)[idx] for idx in pattern )
        for hand in _maybeCycle(g, cycle=cycle):
            yield hand
    return gen

def timeGenerator(times, length):
    def gen(self, ticks, cycle=False, start=0):
        t = start
        if cycle:
            l = ticks * length
            def offsetg(t):
                while 1:
                    yield t
                    t += l
            g = ( o + s * ticks for o in offsetg(t) for s in times )
        else:
            g = ( t + s * ticks for s in times )
        for tick in g:
            yield tick
    return gen


def generator(values):
    def gen(self, cycle=False):
        for v in _maybeCycle(values, cycle):
            yield v
    return gen


class _SustainMixin:

    def sustain(self):
        while 1:
            yield None

class FiveStrokeRoll(_SustainMixin):
    implements(IRudiment)

    length = 12
    time = timeGenerator((0,1,2,3,4, 6,7,8,9,10), length)
    strokes = strokeGenerator((R,R,L,L,R, L,L,R,R,L))
    velocity = generator((90,70,80,67,120, 90,76,89,70,127))


FSR = FiveStrokeRoll

class SixStrokeRoll(_SustainMixin):
    implements(IRudiment)

    length = 16
    time = timeGenerator((0,2,3,4,5,6, 8,10,11,12,13,14), length)
    strokes = strokeGenerator((L,R,R,L,L,R, L,R,R,L,L,R))
    velocity = generator((120,90,70,80,67,120, 123,90,76,89,70,127))

SSR = SixStrokeRoll


def chainRudiments(rudimentFactory, ticksFactory, start=0):
    t = start
    while 1:
        rudiment, hands = rudimentFactory()
        ticks = ticksFactory()
        strokes = rudiment.strokes(hands[0], hands[1]).next
        velocity = rudiment.velocity().next
        sustain = rudiment.sustain().next
        for tick in rudiment.time(ticks, start=t):
            yield (tick, strokes(), velocity(), sustain())
        t += ticks * rudiment.length 




