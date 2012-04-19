from zope.interface import implements, Interface, Attribute

import itertools

from bl.orchestra.midi import Player
from bl.arp import OrderedArp


__all__ = ['IRudiment', 'IDoubleStrokeOpenRoll', 'IFlam', 'FiveStrokeRoll',
    'SixStrokeRoll', 'Flam', 'Flam32', 'Flam64', 'FlamAccent', 'FlamAccent32',
    'FlamAccent64', 'FlamTap', 'FlamTap32', 'FlamTap64', 'Flamacue',
    'Flamacue32', 'Flamacue64', 'InvertedFlamTap', 'InvertedFlamTap32',
    'InvertedFlamTap64', 'strokeGenerator', 'timeGenerator', 'generator',
    'chainRudiments', 'scaleRudiment']


class IRudiment(Interface):
    """
    A rudiment gives a generator for timing of strokes (time) and two surrogate
    generators: strokes (notes) and veloicty.
    """

    length = Attribute('The length of the rudiment, which is more precisely '
                       'the count of smallest time division that can fit in '
                       'on play of the rudiment. For example if the shortest '
                       'time within the rudiment is 1/16 and one play of the '
                       'rudiment lasts 1 measure (in 4/4), then the length of '
                       'the rudiment is 16.')
    defaultDivisionLength = Attribute(
                       'The default number of ticks that make up the smallest '
                       'division of the rudiment. E.g. for the example given '
                       'for length above (1/16 in 4/4 time), this would be 6.')

    def time(ticks=None, cycle=False, start=0):
        """
        Generator for the relative timing for a rudiment. The timing begins and
        start and increments by the ticks or greater between strokes; i.e. the
        ticks argument is the shortest stroke in the rudiment.

        @param ticks: the number of ticks comprising the shortest stroke. If
        not given the rudiment should choose a default that assumes 24 ticks
        per beat and 4/4 time.

        @param cycle: If True, cycle the generator using (N * length) as start
        for each N iteration; this means values generated for N cycle are in
        range [N*length, N*length+length].
        """

    def strokes(r, l, cycle=False):
        """
        Generator for the "strokes" for a rudiment. E.g. [l, r, l, r]

        @param r: note for the "right" hand
        @param l: note for the "left" hand
        @param cycle: if True, generate pattern infinitely. Otherwise, enough
        for one run of the rudiment (generally, a measure)
        """

    def velocity(cycle=False):
        """
        Generator for the velocity to zip with strokes in the rudiment.

        @param cycle: if True, generate pattern infinitely. Otherwise, enough
        for one run of the rudiment (generally, a measure)
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
        g = ((r, l)[idx] for idx in pattern)
        for hand in _maybeCycle(g, cycle=cycle):
            yield hand
    return gen


def timeGenerator(times, length):
    def gen(self, ticks=None, cycle=False, start=0):
        if ticks is None:
            ticks = self.defaultDivisionLength
        t = start
        if cycle:
            l = ticks * length

            def offsetg(t):
                while 1:
                    yield t
                    t += l

            g = (o + s * ticks for o in offsetg(t) for s in times)
        else:
            g = (t + s * ticks for s in times)
        for tick in g:
            yield tick
    return gen


def generator(values):
    def gen(self, cycle=False):
        for v in _maybeCycle(values, cycle):
            yield v
    return gen


class _SustainMixin(object):

    def sustain(self):
        while 1:
            yield None


# Double Stroke Open Roll Rudiments

class FiveStrokeRoll(_SustainMixin):
    implements(IDoubleStrokeOpenRoll)

    length = 16
    defaultDivisionLength = 6
    time = timeGenerator((0, 1, 2, 3, 4, 8, 9, 10, 11, 12), length)
    strokes = strokeGenerator((R, R, L, L, R, L, L, R, R, L))
    velocity = generator((90, 70, 80, 67, 120, 90, 76, 89, 70, 127))


class SixStrokeRoll(_SustainMixin):
    implements(IDoubleStrokeOpenRoll)

    length = 16
    defaultDivisionLength = 6
    # TODO - adjust timing relative to 96 ticks/measure
    # However, don't think this is the right timing anyhow
    time = timeGenerator((0, 2, 3, 4, 5, 6, 8, 10, 11, 12, 13, 14), length)
    strokes = strokeGenerator((L, R, R, L, L, R, L, R, R, L, L, R))
    velocity = generator((120, 90, 70, 80, 67, 120, 123, 90, 76, 89, 70, 127))


# Flam Rudiments


class Flam32(_SustainMixin):
    implements(IFlam)

    length = 32
    defaultDivisionLength = 3
    time = timeGenerator((0, 7, 8, 15, 16, 23, 24, 31), length)
    strokes = strokeGenerator((R, R, L, L, R, R, L, L))
    velocity = generator((127, 50, 120, 55, 120, 45, 115, 40,), )


Flam = Flam32


class Flam64(Flam):

    length = 64
    defaultDivisionLength = 1
    time = timeGenerator((0, 15, 16, 31, 32, 47, 48, 63), length)


class FlamAccent32(_SustainMixin):
    implements(IFlam)

    length = 48
    defaultDivisionLength = 2
    time = timeGenerator((0, 8, 16, 21, 24, 32, 40, 45,), length)
    strokes = strokeGenerator((R, L, R,  R, L, R, L, L))
    velocity = generator((127, 80, 70, 60, 120, 90, 80, 65))


FlamAccent = FlamAccent32


class FlamAccent64(FlamAccent):
    length = 96
    defaultDivisionLength = 1
    time = timeGenerator((0, 16, 32, 45, 48, 64, 80, 93), length)


class FlamTap32(_SustainMixin):
    implements(IFlam)

    length = 48
    defaultDivisionLength = 2
    time = timeGenerator((0, 6, 9, 12, 18, 21, 24, 30, 33, 36, 42, 45), length)
    strokes = strokeGenerator((R, R, R, L, L, L, R, R, R, L, L, L))
    velocity = generator((127, 90, 60, 120, 95, 60, 120, 90, 50, 120, 90, 60))


FlamTap = FlamTap32


class FlamTap64(FlamTap):
    length = 96
    defaultDivisionLength = 1
    time = timeGenerator((0, 12, 21, 24, 36, 45, 48, 60, 69, 72, 84, 93),
                         length)


class _InvertedFlamTapMixin(object):
    strokes = strokeGenerator((R, L, R, L, R, L, R, L, R, L, R, L))


class InvertedFlamTap32(_InvertedFlamTapMixin, FlamTap32):
    pass


InvertedFlamTap = InvertedFlamTap32


class InvertedFlamTap64(_InvertedFlamTapMixin, FlamTap64):
    pass


class Flamacue32(_SustainMixin):
    implements(IFlam)
    length = 48
    defaultDivisionLength = 2
    time = timeGenerator((0, 6, 12, 18, 21, 24, 45), length)
    strokes = strokeGenerator((R, L, R, L, L, R, L, L, R, L, R, R, L, R))
    velocity = generator((90, 127, 85, 90, 70, 115, 60))


Flamacue = Flamacue32


class Flamacue64(Flamacue):
    length = 96
    defaultDivisionLength = 1
    time = timeGenerator((0, 12, 24, 36, 45, 48, 93), length)


# Utilities for combining and chaining different Rudiments

def chainRudiments(rudimentFactory, ticksFactory, start=0):
    # TODO test me
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


_rudiment_classes = {}


def scaleRudiment(rudimentClass, ticksPerBeat):
    """
    Scale rudiment to ticksPerBeat. This returns a new Rudiment class based on
    the given rudimentClass with defaultDivisionLength scaled appropriately.
    """
    q = ticksPerBeat / 24.
    name = '%s_TPB%s' % (rudimentClass.__name__, ticksPerBeat)
    if name not in _rudiment_classes:
        _rudiment_classes[name] = klass = type(name, (rudimentClass,), {})
        klass.defaultDivisionLength = int(q * klass.defaultDivisionLength)
    return _rudiment_classes[name]


class RudimentSchedulePlayer(Player):
    """
    A schedule player for a rudiment. This also gives us arps to manipulate
    or change during the runtime.

    noteArp: The note arp (OrderedArp)
    velocityArp: The velocity arp (OrderedArp)
    sustainArp: the sustain arp (OrderedArp)
    """

    def __init__(self, instrument, rudiment, r, l, release=None, **kw):
        """
        @param instrument: The backend instrument (Fsynth instrument etc)
        @param rudiment: A IRudiment provider
        @param r: The "right" note
        @param l: the "left" note
        @param sustainArp: An optional "sustain" value arp.
        """
        self.rudiment = rudiment
        time = rudiment.time(cycle=True).next
        note = OrderedArp(list(rudiment.strokes(r, l, cycle=False)))
        velocity = OrderedArp(list(rudiment.velocity(cycle=False)))
        kw['time'] = time
        kw['velocity'] = velocity
        Player.__init__(self, instrument, note, **kw)

    def changeStrokes(self, r, l):
        self.note.reset(list(self.rudiment.strokes(r, l, cycle=False)))
