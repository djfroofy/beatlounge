import time

from collections import namedtuple
from functools import wraps
from zope.interface import implements

from twisted.python import log
from twisted.python.components import proxyForInterface
from twisted.internet.interfaces import IReactorTime
from twisted.internet.base import ReactorBase
from twisted.internet.selectreactor import SelectReactor
from twisted.internet.defer import Deferred, succeed
from twisted.internet.task import LoopingCall

#from fluidsynth import Synth

__all__ = ['Beat', 'Meter', 'standardMeter', 'BeatClock', 'measuresToTicks', 'mtt',
            'ScheduledEvent', 'clock' ]

_BeatBase = namedtuple('_BeatBase', 'measure quarter eighth sixteenth remainder')

secs = lambda : time.time() % 86400

class Beat(_BeatBase):

    def __repr__(self):
        return ('Beat(measure=%s, quarter=%s, eighth=%s, sixteenth=%s, '
                'remainder=%s)' % (self.measure, self.quarter, self.eighth,
                self.sixteenth, self.remainder))

class Meter(object):

    def __init__(self, length=4, division=4, number=1):
        self.length = length
        self.division = division
        self.number = number
        self._quarters_per_measure = self.length * self.number / (self.division / 4.)
        self._hash = hash((self.length, self.division, self.number))
        self.ticksPerMeasure = int(24 * self.length * 4. / self.division * self.number)
        

    def beat(self, ticks):
        measure, ticks = divmod(ticks, self.ticksPerMeasure)
        if not ticks:
            return Beat(measure, 0, 0, 0, 0)
        quarter, ticks = divmod(ticks, self.ticksPerMeasure / self._quarters_per_measure) 
        if not ticks:
            return Beat(measure, int(quarter), 0, 0, 0)
        eighth, ticks = divmod(ticks, self.ticksPerMeasure / (self._quarters_per_measure * 2)) 
        if not ticks:
            return Beat(measure, int(quarter), int(eighth), 0, 0)
        sixteenth, ticks = divmod(ticks, self.ticksPerMeasure / (self._quarters_per_measure * 4))
        return Beat(measure, int(quarter), int(eighth), int(sixteenth), int(ticks))

    def ticks(self, ticks):
        return ticks % self.ticksPerMeasure

    def measure(self, ticks):
        return divmod(ticks, self.ticksPerMeasure)[0]

    def __repr__(self):
        return 'Meter(length=%s, division=%s, number=%s)' % (self.length, self.division, self.number)

    def __hash__(self):
        return self._hash


standardMeter = Meter(4,4)

class SynthControllerMixin(object):
    synthAudioDevice = 'coreaudio'
    synthChannels = 'stereo'

class BeatClock(SelectReactor, SynthControllerMixin):

    defaultClock = None

    def __init__(self, tempo=130, meters=(), reactor=None, default=False):
        self.tempo = tempo
        self.ticks = 0
        #self.setTempo(tempo)
        self._tick_interval = (60. / tempo) * (1./24)
        self.meters = meters
        self._meter_schedule = {}
        if not self.meters:
            self.meters = [Meter(4,4,1)]
        if not reactor:
            from twisted.internet import reactor
        self.reactor = reactor
        if default or (self.defaultClock is None):
            BeatClock.defaultClock = self
        SelectReactor.__init__(self)

    def setTempo(self, tempo):
        self._tick_interval = (60. / tempo) * (1./24)
        if hasattr(self, 'task'):
            self.task.stop()
            self.task.start(self._tick_interval, True)
        self.tempo = tempo

    def run(self):
        self._initBackends()
        self.startTicking()
        self.running = True
        if not self.reactor.running:
            self.reactor.run()


    def _initBackends(self):
        try:
            from txbeatlounge.instrument import fsynth
            if self.synthChannels == 'stereo':
                return
            if self.synthChannels == 'mono':
                pool = fsynth.MonoPool()
            elif self.synthChannels == 'quad':
                pool = fsynth.QuadPool()
            else:
                try:
                    self.synthChannels = int(self.synthChannels) 
                except ValueError:
                    raise ValueError('synthChannels should be one of mono, stereo, quad or an integer')
                synths = dict( (n, fsynth.Synth) for n in range(self.synthChannels) )
                pool = fsynth.NConnectionPool(synths)
            fsynth.suggestDefaultPool(pool)
        except ImportError:
            log.msg('fluidsynth will not be available at runtime')
            pass

    def startTicking(self):
        self.task = LoopingCall(self.tick)
        self.on_stop = self.task.start(self._tick_interval, True)

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

    def callAfterMeasures(self, measures, f, *a, **kw):
        meter = self.meters[0]
        ticks = _ticks(measures, meter, self)
        self.callLater(ticks, f, *a, **kw)    

    def nudge(self, pause=0.1):
        if not hasattr(self, 'task'):
            raise ValueError("Cannot nudge a clock that hasn't started")
        self.task.stop()
        self.reactor.callLater(pause, self.task.start, self._tick_interval, True)


    def receiveTime(self, receiver=None, port=17779, interface='192.168.2.3', listen_now=True):
        """
        Receives time from a master and starts the clock with the next "one"
        """

        if self.running: raise ValueError('clock is already running')

        if not receiver:
            from txosc.dispatch import Receiver
            receiver = Receiver()

        def _sync(message, address):
            args = message.arguments

            tempo = int(args[3].value)
            beats, duration = [int(a) for a in str(args[2].value).split('/')]
            meter = Meter(beats, duration, 1)

            if self.running:
                if tempo == self.tempo:
                    return
                else:
                    log.msg('received clock tempo change')
                    self.task.stop()

            log.msg(message)
            ticks = int(args[0].value)
            time_of_last_one = float(args[1].value)

            ticks_per = 96/duration
            ticks_per_measure = ticks_per * beats
            ticks_per_second = tempo * 0.4
            seconds_per_measure = ticks_per_measure/ticks_per_second

            self.tempo = tempo
            self._tick_interval = (60. / tempo) * (1./24)
            self.meters = [Meter(beats, duration, 1)]
            self.ticks = ticks + ticks_per_measure
            delta = (time_of_last_one + seconds_per_measure) - secs()

            if self.running:
                self.reactor.callLater(delta, self.startTicking)
            else:
                self.reactor.callLater(delta, self.run)

        receiver.addCallback('/clock', _sync)

        if listen_now:
            from txosc.async import DatagramServerProtocol
            self.reactor.listenUDP(port, DatagramServerProtocol(receiver), interface=interface)


def measuresToTicks(measures, meter=standardMeter):
    return int(measures * meter.ticksPerMeasure)

mtt = measuresToTicks

def _ticks(measures, meter, clock):
    current_measure = meter.measure(clock.ticks)
    tick = int(current_measure * meter.ticksPerMeasure + measures * meter.ticksPerMeasure)
    ticks = tick - clock.seconds()
    if ticks < 0:
        ticks += meter.ticksPerMeasure
    return ticks

class ScheduledEvent(object):
   
    meter = None
 
    def __init__(self, clock, _f, *args, **kwargs):
        self.clock = clock
        self.call = (_f, args, kwargs)

    def startLater(self, measures=1, frequency=0.25, ticks=None, meter=None):
        if measures < 0:
            raise ValueError("measures must be greater than zero")
        meter = meter or self.meter or self.clock.meters[0]
        if ticks is None:
            # XXX
            # I'm a little torn between whether this should be absolute to a 
            # a standard meter (as current), or relative to any given meter.
            # The advantage of the former is that 0.25 always means quarter note
            # etc.
            ticks = frequency * standardMeter.ticksPerMeasure
        def _start_later():
            ticksLater = self._ticks(measures, meter)
            self.clock.callLater(ticksLater, self.start, ticks, True)
        self.clock.callWhenRunning(_start_later)
        return self

    def start(self, ticks=None, now=True):
        def _start():
            self.task = LoopingCall(self.call[0], *self.call[1], **self.call[2])
            self.task.clock = self.clock
            self.deferred = self.task.start(ticks, now)
        self.clock.callWhenRunning(_start)
        return self

    def stopLater(self, measures=1, meter=None, ticksLater=None):
        meter = meter or self.meter or self.clock.meters[0]
        def _scheduleStop():
            ticks = ticksLater
            if ticks is None:
                ticks = self._ticks(measures, meter)
            def _stop():
                if hasattr(self, 'task'):
                    self.task.stop()
                else:
                    log.msg('Tried to stop an event that has not yet started')
            self.clock.callLater(ticks, _stop)
        self.clock.callWhenRunning(_scheduleStop)
        return self

    def stop(self):
        if hasattr(self, 'task') and self.task.running:
            self.task.stop()

    def bindMeter(self, meter):
        self.meter = meter
        return self

    def _ticks(self, measures, meter):
        current_measure = meter.measure(self.clock.ticks)
        tick = int(current_measure * meter.ticksPerMeasure + measures * meter.ticksPerMeasure)
        ticks = tick - self.clock.seconds()
        if ticks < 0:
            ticks += meter.ticksPerMeasure
        return ticks


BPM = 130
clock = BeatClock(BPM)

