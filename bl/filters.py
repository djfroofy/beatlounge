import random
from itertools import cycle

import math
from warnings import warn

from zope.interface import implements, Interface, Attribute

from bl.utils import minmax, getClock


warn('bl.filters was a bad idea; this is deprecated, so do not use anymore')

__all__ = ['IFilter', 'BaseFilter', 'PassThru', 'Sustainer', 'Ducker', 'StandardDucker',
           'Chain', 'Standard8Ducker', 'Standard16Ducker', 'Standard32Ducker',
           'Sin', 'Sinusoid', 'Sawtooth', 'Triangle', 'FadeIn', 'FadeOut',
           'M34Ducker', 'M78Ducker', 'Stepper', 'Humanize']

class IFilter(Interface):

    clock = Attribute("""A L{IBeatClock}""")

    def filter(value, original=None):
        """
        Optionally filter value and return tuple (filtered value, original).
        If original is None, a filter should generally instead return (filtered value, value).
        """


class BaseFilter(object):
    implements(IFilter)
    
    def filter(self, velocity, original):
        return velocity, original

    def __call__(self, velocity=None, original=None):
        if velocity is None:
            velocity = 127
        return self.filter(velocity, original)        

PassThru = BaseFilter

class Sustainer(BaseFilter):

    def __init__(self, velocity):
        self.velocity = velocity

    def filter(self, velocity, original=None):
        if original is None:
            original = self.velocity
        return self.velocity, original


class Humanize(BaseFilter):
    """
    Takes an original and alters it randomly within the integral range
    [-amount, amount]
    """

    def __init__(self, amount):
        self.amount = amount

    def filter(self, velocity, original=None):
        h = random.randrange(self.amount)
        if not velocity:
            velocity = h
        if original is None:
            original = velocity
        return minmax(velocity + random.choice([-1, 1]) * h), original


def _scaleVelocity(velocity, original):
    if original is None:
        original = velocity
    scale = float(velocity) / original
    return scale, original


class WeightNote(BaseFilter):

    def __init__(self, callMemo, noteWeights, default=100):
        self.callMemo = callMemo
        self.noteWeights = noteWeights
        self.default = default

    def filter(self, velocity, original=None):
        scale, original = _scaleVelocity(velocity, original)
        velocity = self.noteWeights.get(self.callMemo.currentValue, self.default)
        return int(scale * velocity), original


class Ducker(BaseFilter):
    peaks = None
    duckLevel = 0

    def __init__(self, duckLevel=None, peaks=None, clock=None, meter=None):
        warn('Ducker is deprecated - use Stepper instead which is simpler')
        self.clock = getClock(clock)
        if meter is None:
            meter = self.clock.meter
        self.meter = meter
        self.peaks = peaks or self.peaks
        self.duckLevel = duckLevel is None and self.duckLevel or duckLevel

    def filter(self, velocity, original=None):
        if original is None:
            original = velocity
        duckLevel = self.duckLevel
        if velocity != original:
            duckLevel = (float(velocity) / original) * duckLevel
        beat = self.meter.beat(self.clock.ticks)
        if beat[1:] not in self.peaks:
            velocity = int(velocity - duckLevel)
        return velocity, original


class Stepper(BaseFilter):
    """
    TODO cycles through an iterable of integers between 0 and 127, velocity.
    """

    def __init__(self, steps):
        self._current_step = 0
        self._count = len(steps)
        self.steps = steps

    def _get_steps(self):
        return self._steps

    def _set_steps(self, steps):
        count = len(steps)
        factor = float(count) / self._count
        self._steps = steps
        self._stepcycle = cycle(steps)
        for i in range(int(factor * self._current_step)):
            self._stepcycle.next()
        self._count = count
        
    steps = property(_get_steps, _set_steps)

    def filter(self, velocity, original=None):
        if original is None:
            original = velocity
        v = self._stepcycle.next()
        if callable(v):
            v = v()
        self._current_step += 1
        self._current_step %= self._count
        return v, original


class Chain(BaseFilter):

    def __init__(self, *filters):
        self.filters = filters

    def filter(self, velocity, original=None):
        for filter in self.filters:
            velocity, o = filter.filter(velocity, original)
            if original is None:
                original = o
        return velocity, original

class StandardDucker(Ducker):
    peaks = [(0,0,0,0),(1,0,0,0),(2,0,0,0),(3,0,0,0)]

class Standard8Ducker(Ducker):
    peaks = [(0,0,0,0),
             (0,1,0,0),
             (1,0,0,0),
             (1,1,0,0),
             (2,0,0,0),
             (2,1,0,0),
             (3,0,0,0),
             (3,1,0,0)]

class Standard16Ducker(Ducker):
    peaks = [ (i,j,k,0) for i in range(4)
              for j in range(2) for k in range(2) ]

class Standard32Ducker(Ducker):
    peaks = [ (i,j,k,l) for i in range(4)
               for j in range(2) for k in range(2)
               for l in range(0,24,12) ]

class M34Ducker(Ducker):
    peaks = [(0,0,0,0),(1,0,0,0),(2,0,0,0)]


M78Ducker = M34Ducker

duck34 = lambda peak, duckamount : Chain(Sustainer(peak), M78Ducker(duckamount)).filter
duck78 = duck34


class FadeX(BaseFilter):
    
    def __init__(self, min=0, max=127, step=1, tickrate=12, clock=None):
        self.clock = getClock(clock)
        self.min = min
        self.max = max
        self.step = step
        self.current = self.min
        self.tickrate = tickrate
        self._currenttick = self.clock.ticks
        self._laststep = self.clock.ticks


class FadeIn(FadeX):

    def filter(self, velocity, original=None):
        if self.current == self.max:
            return self.current, self.max
        self._currenttick = self.clock.ticks
        if self._currenttick - self._laststep >= self.tickrate:
            self.current += self.step
            self.current = min(self.max, self.current)
            self._laststep = self._currenttick
        return self.current, self.max


class FadeOut(FadeX):

    def __init__(self, max=127, min=0, **kw):
        super(FadeOut, self).__init__(min, max, **kw)
        self.current = self.max

    def filter(self, velocity, original=None):
        if self.current == self.min:
            return self.current, self.max
        self._currenttick = self.clock.ticks
        if self._currenttick - self._laststep >= self.tickrate:
            self.current -= self.step
            self.current = max(self.min, self.current)
            self._laststep = self._currenttick
        return self.current, self.max



class Sin(BaseFilter):

    min = 0
    max = 127

    def __init__(self, amplitude, period, phase=0, center=63, clock=None):
        self.amplitude = amplitude
        self.frequency = math.pi * 2 / period
        self.phase = phase
        self.center = center
        self.clock = getClock(clock)

    def filter(self, velocity, original=None):
        if original is None:
            original = velocity
        velocity = self.center + self.amplitude * math.sin(self.frequency * self.clock.ticks + self.phase)
        velocity = max(self.min, int(velocity))
        velocity = min(velocity, self.max)
        return velocity, original

# backwards compat
Sinusoid = Sin

def _sawtooth(period, t):
    ft = float(t)
    return 2 * (ft / period - math.floor(ft / period + 0.5))    


class Sawtooth(BaseFilter):

    def __init__(self, amplitude, period, center=63, phase=0, clock=None):
        self.period = period
        self.amplitude = amplitude
        self.center = center
        self.phase = phase
        self.clock = getClock(clock)

    def filter(self, velocity, original=None):
        if original is None:
            original = velocity
        velocity = _sawtooth(self.period, self.clock.ticks + self.phase)
        return int(self.center + self.amplitude * velocity), original

class Triangle(Sawtooth):

    def __init__(self, amplitude, *p, **kw):
        super(Triangle, self).__init__(amplitude, *p, **kw)
        self._bump = self.amplitude / 2.

    def filter(self, velocity, original=None):
        if original is None:
            original = velocity
        velocity = abs(_sawtooth(self.period, self.clock.ticks + self.phase))
        return int(self.center + self.amplitude * velocity - self._bump), original


