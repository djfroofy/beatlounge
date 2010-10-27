from zope.interface import implements, Interface, Attribute


class IFilter(Interface):

    clock = Attribute("""A L{IBeatClock}""")

    def filter(value, original=None):
        """
        Optionally filter value and return tuple (filtered value, original).
        If original is None, a filter should generally instead return (filtered value, value).
        """


class PassThru(object):
    implements(IFilter)

    def filter(self, velocity, original):
        return velocity, original


class Sustainer(object):
    implements(IFilter)

    def __init__(self, velocity):
        self.velocity = velocity

    def filter(self, velocity, original=None):
        if original is None:
            original = self.velocity
        return self.velocity, original


class Ducker(object):
    implements(IFilter)

    peaks = None
    duckLevel = 0

    def __init__(self, duckLevel=None, peaks=None, clock=None):
        self.clock = _getclock(clock)
        self.meter = self.clock.meters[0]
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


class Chain(object):
    implements(IFilter)

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


class FadeX(object):
    
    def __init__(self, min=0, max=127, step=1, tickrate=12, clock=None):
        self.clock = _getclock(clock)
        self.min = min
        self.max = max
        self.step = step
        self.current = self.min
        self.tickrate = tickrate
        self._currenttick = self.clock.ticks
        self._laststep = self.clock.ticks


class FadeIn(FadeX):
    implements(IFilter)

    def filter(self, velocity, original=None):
        if original is None:
            original = velocity
        if self.current == self.max:
            return self.current, self.max
        self._currenttick = self.clock.ticks
        if self._currenttick - self._laststep >= self.tickrate:
            self.current += self.step
            self.current = min(max, self.current)
            self._laststep = self._currenttick
        return self.current, self.max



def _getclock(clock):
    if clock is None:
        from txbeatlounge.scheduler2 import clock
    return clock

