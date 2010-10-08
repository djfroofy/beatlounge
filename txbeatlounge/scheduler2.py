from functools import wraps

from zope.interface import implements

from twisted.python.components import proxyForInterface
from twisted.internet.interfaces import IReactorTime
from twisted.internet.base import ReactorBase
from twisted.internet.selectreactor import SelectReactor
from twisted.internet.defer import Deferred, succeed
from twisted.internet.task import LoopingCall

from fluidsynth import Synth

class Beat(tuple):

    def __init__(self, measure, quarter=0, eighth=0, sixteenth=0, remainder=0):
        self.measure = measure
        self.quarter = quarter
        self.eighth = eighth
        self.sixteenth = sixteenth
        self.remainder = remainder
        a = (measure, quarter, eighth, sixteenth, remainder)
        tuple.__init__(self, *a)
 
    def n_eighth(self):
        return self.quarter * 2 + self.eighth

    def n_sixteenth(self):
        return self.quarter * 4 + self.eighth * 2 + self.sixteenth


class Meter(object):

    def __init__(self, length=4, division=4, number=1):
        self.length = length
        self.division = division
        self.number = number
        self._hash = hash((self.length, self.division, self.number))
        self.ticks_per_measure = int(24 * (self.length / 4.) * 4 * (4. / self.division) *  self.number)

    def beat(self, ticks):
        measure, ticks = divmod(ticks, self.ticks_per_measure)
        if not ticks:
            return Beat(measure)
        quarter, ticks = divmod(ticks, self.ticks_per_measure / 4) 
        if not ticks:
            return Beat(measure, quarter)
        eighth, ticks = divmod(ticks, self.ticks_per_measure / 8)     
        if not ticks:
            return Beat(measure, quarter, eighth)
        sixteenth, ticks = divmod(ticks, self.ticks_per_measure / 16)
        return Beat(measure, quarter, eighth, sixteenth, ticks)

    def ticks(self, ticks):
        return ticks % self.ticks_per_measure

    def measure(self, ticks):
        return divmod(ticks, self.ticks_per_measure)[0]

    def __hash__(self):
        return self._hash

class SynthControllerMixin(object):
    synthAudioDevice = 'coreaudio'
    synth = Synth(0.2)


class BeatClock(SelectReactor, SynthControllerMixin):

    def __init__(self, tempo=130, meters=(), reactor=None):
        self.tempo = tempo
        self.ticks = 0
        self._tick_interval = (60. / tempo) * (1./24)
        self.meters = meters
        self._meter_schedule = {}
        if not self.meters:
            self.meters = [Meter(4,4,1)]
        if not reactor:
            from twisted.internet import reactor
        self.reactor = reactor
        SelectReactor.__init__(self)

    def run(self):
        self.synth.start(self.synthAudioDevice)
        import time
        time.sleep(10)
        self.task = LoopingCall(self.tick)
        self.on_stop = self.task.start(self._tick_interval, True)
        if not self.reactor.running:
            self.reactor.run()

    def tick(self):
        self.ticks += 1
        self.runUntilCurrent()

    def seconds(self):
        return self.ticks

    def schedule(self, _f, *args, **kwargs):
        event = ScheduledEvent(self, _f, *args, **kwargs)
        return event

    def callWhenRunning(self, *a, **kw):
        return self.reactor.callWhenRunning(*a, **kw)


class ScheduledEvent(object):
    
    def __init__(self, clock, _f, *args, **kwargs):
        self.clock = clock
        self.call = (_f, args, kwargs)

    def startLater(self, measures=1, frequency=0.25, ticks=None, meter=None):
        if measures < 1:
            raise ValueError("measures should be a non-zero positive integer")
        if meter is None:
            meter = self.clock.meters[0]
        if ticks is None:
            ticks = frequency * meter.ticks_per_measure
        def _start_later():
            current_measure = meter.measure(self.clock.ticks)
            tick = int(current_measure + meter.ticks_per_measure * measures)
            seconds = tick - self.clock.seconds()
            self.clock.callLater(seconds, self.start, ticks, True)
        self.clock.callWhenRunning(_start_later)
        return self

    def start(self, ticks, now=True):
        def _start():
            self.task = LoopingCall(self.call[0], *self.call[1], **self.call[2])
            self.task.clock = self.clock
            self.deferred = self.task.start(ticks, now)
        self.clock.callWhenRunning(_start)
        return self

    def stopLater(self, measures=1):
        def _stop():
            current_measure = meter.measure(self.ticks)
            tick = int(current_measure + meter.ticks_per_measure * measures)
            seconds = tick - self.clock.seconds()
            self.clock.callLater(seconds, self.task.stop)
        self.clock.callWhenRunning(_stop)
        return self


BPM = 130
clock = BeatClock(BPM)

