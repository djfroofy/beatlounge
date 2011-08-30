from zope.interface import implements, Interface, Attribute

import itertools

__all__ = ['IRudiment', 'IDoubleStrokeOpenRoll', 'IFlam', 'FiveStrokeRoll', 'FSR',
    'SixStrokeRoll', 'SSR', 'Flam', 'Flam32', 'Flam64', 'FlamAccent', 'FlamAccent32', 'FlamAccent64',
    'FlamTap', 'FlamTap32', 'FlamTap64', 'Flamacue', 'Flamacue32', 'Flamacue64',
    'strokeGenerator', 'timeGenerator', 'generator', 'chainRudiments']

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


class IDoubleStrokeOpenRoll(IRudiment):
    pass

class IFlam(IRudiment):
    pass


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


# Double Stroke Open Roll Rudiments

class FiveStrokeRoll(_SustainMixin):
    implements(IDoubleStrokeOpenRoll)

    length = 12
    time = timeGenerator((0,1,2,3,4, 6,7,8,9,10), length)
    strokes = strokeGenerator((R,R,L,L,R, L,L,R,R,L))
    velocity = generator((90,70,80,67,120, 90,76,89,70,127))


FSR = FiveStrokeRoll

class SixStrokeRoll(_SustainMixin):
    implements(IDoubleStrokeOpenRoll)

    length = 16
    time = timeGenerator((0,2,3,4,5,6, 8,10,11,12,13,14), length)
    strokes = strokeGenerator((L,R,R,L,L,R, L,R,R,L,L,R))
    velocity = generator((120,90,70,80,67,120, 123,90,76,89,70,127))

SSR = SixStrokeRoll


# Flam Rudiments

class Flam32(_SustainMixin):
    implements(IFlam)

    length = 32
    time = timeGenerator((0, 7,8, 15,16, 23,24, 31), length)
    strokes = strokeGenerator((R, R,L, L,R, R,L, L))
    velocity = generator((127, 50,120, 55,120, 45,115, 40,), )


Flam = Flam32

class Flam64(Flam):

    length = 64
    time = timeGenerator((0, 15,16, 31,32, 47,48, 63), length)

class FlamAccent32(_SustainMixin):
    implements(IFlam)

    length = 48
    time = timeGenerator((0,8,16, 21,24,32,40, 45,), length)
    strokes = strokeGenerator((R,L,R,  R,L,R,L, L))
    velocity = generator((127,80,70, 60,120,90,80, 65))

FlamAccent = FlamAccent32

class FlamAccent64(FlamAccent):
    length = 96
    time = timeGenerator((0,16,32, 45,48,64,80, 93), length)


class FlamTap32(_SustainMixin):
    implements(IFlam)

    length = 48
    time = timeGenerator((0,6,9,12,18, 21,24,30,33,36,42, 45), length)
    strokes = strokeGenerator((R,R,R,L,L, L,R,R,R,L,L, L))
    velocity = generator((127,90,60,120,95, 60,120,90,50,120,90, 60))


FlamTap = FlamTap32

class FlamTap64(FlamTap):
    length = 96
    time = timeGenerator((0,12,21,24,36, 45,48,60,69,72,84, 93), length)


class Flamacue32(_SustainMixin):
    implements(IFlam)
    length = 48
    time = timeGenerator((0,6,12,18, 21,24, 45), length)
    strokes = strokeGenerator((R,L,R,L,L,R,L, L,R,L,R,R,L,R))
    velocity = generator((90,127,85,90, 70,115, 60))

Flamacue = Flamacue32

class Flamacue64(Flamacue):
    length = 96
    time = timeGenerator((0,12,24,36, 45,48, 93), length)


# Utilities for combining and chaining different Rudiments

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




