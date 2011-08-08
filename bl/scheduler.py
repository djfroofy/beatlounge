import time
import math
import warnings

from collections import namedtuple
from functools import wraps
from zope.interface import implements

from twisted.python import log
from twisted.python.failure import Failure
from twisted.python.components import proxyForInterface
from twisted.internet.interfaces import IReactorTime
from twisted.internet.base import ReactorBase
from twisted.internet.selectreactor import SelectReactor
from twisted.internet.defer import Deferred, succeed
from twisted.internet.task import LoopingCall

from bl.debug import DEBUG

__all__ = [ 'Tempo', 'Beat', 'Meter', 'standardMeter', 'BeatClock',
            'ScheduledEvent', 'clock' ]

_BeatBase = namedtuple('_BeatBase', 'measure quarter eighth sixteenth remainder')



class Tempo(object):
    """
    Tempo gives the tempo in 3 forms for ready access:

    bpm (beats per minute)
    tpb (ticks per beat)
    tpm (ticks per minute)

    Do not set these attributes directly, but call reset() instead.
    Otherwise, expect unexpected behaviors.
    """

    def __init__(self, bpm=120, tpb=24):
        self.bpm = bpm
        self.tpb = tpb
        self.tpm = self.bpm * self.tpb


    def reset(self, bpm=None, tpb=None, tpm=None):
        if bpm:
            self.bpm = bpm
        if tpb:
            self.tpb = tpb
        if tpm:
            self.tpm = tpm
            self.bpm = (tpm / self.tpb)
            return
        self.tpm = self.bpm * self.tpb

    def __str__(self):
        return 'Tempo(bpm=%s, tpb=%s)' % (self.bpm, self.tpb)

TEMPO_120_24 = Tempo()
STANDARD_TICKS_PER_MEASURE = 96

class Beat(_BeatBase):
    """
    A named tuple representing the current beat as:

        (measure no, quarter no, eigth number no, sixteenth no, remaning ticks)

    If we are on the 15th semiquaver of the 2nd measure for example, then the Beat would be:

        (1, 3, 1, 1, 0)

    If we are the third 1/32 of the first measure:

        (0, 0, 0, 1, 3)
    """

    def __repr__(self):
        return ('Beat(measure=%s, quarter=%s, eighth=%s, sixteenth=%s, '
                'remainder=%s)' % (self.measure, self.quarter, self.eighth,
                self.sixteenth, self.remainder))

class Meter(object):
    """
    Representation of a Musical meter with methods for representing the current Beat
    and converting to other related values: the current measure number based on ticks,
    ticks into the current measure, etc.
    """
    strict = True

    def __init__(self, length=4, division=4, number=1, tempo=TEMPO_120_24):
        self.length = length
        self.division = division
        self.number = number
        self._quarters_per_measure = self.length * self.number / (self.division / 4.)
        self._hash = hash((self.length, self.division, self.number))
        self.resetTempo(tempo)

    def resetTempo(self, tempo):
        self.ticksPerMeasure = int(tempo.tpb * self.length * 4. / self.division * self.number)

    def beat(self, ticks):
        """
        Return Beat tuple based on the given ticks.

        ticks: the clock ticks (BeatClock.ticks)
        """
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
        """
        Return the number of ticks that have elapsed since the start of the current
        measure based on the total clock ticks.

        ticks: the clock ticks (BeatClock.ticks)
        """
        return ticks % self.ticksPerMeasure

    def divisionToTicks(self, n, d):
        """
        Convert n/d (examples 1/4, 3/4, 3/32, 8/4..)
        For example, if the ticks-per-beat are 24, then n=1 and d=8 would return 12.
        """
        ticks = float(n)/d * self.ticksPerMeasure
        _, rem = divmod(ticks, 1)
        if rem and self.strict:
            raise ValueError('<divisionToTicks> %s/%s does not evenly divide %s' % (n,d,self.ticksPerMeasure))
        elif rem and not self.strict:
            log.err(Failure(ValueError('<divisionToTicks> %s/%s does not evenly divide %s' % (n,d,self.ticksPerMeasure))))
        return int(math.floor(ticks))

    dtt = divisionToTicks

    def nextDivision(self, ticks, n, d):
        m = self.measure(ticks) * self.ticksPerMeasure
        nm = m + self.ticksPerMeasure
        offset_ticks = self.divisionToTicks(n, d)
        next = m + offset_ticks
        if next < ticks:
            next = next + self.ticksPerMeasure
        return next

    nd = nextDivision

    def nextMeasure(self, ticks, measures=1):
        m = self.measure(ticks) * self.ticksPerMeasure
        r = m + measures * self.ticksPerMeasure
        return r

    nm = nextMeasure

    def untilNextMeasure(self, ticks, measures=1):
        return self.nextMeasure(measures) - ticks

    unm = untilNextMeasure

    def measure(self, ticks):
        """
        Return the current measure number based on ticks.

        ticks. the clock ticks (BeatClock.ticks)
        """
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
    """
    A BeatClock is a meta reactor based on a looping call which is used to keep
    virtual time based on a given tempo and meter. The current implementation assumes
    there are  24 ticks (pulses) per quarter note (or 96 ticks per standard measure).

    In general a runtime should only use one singleton BeatClck, though it's in theory
    possible to have many running at the same time (waves hands).
    """

    defaultClock = None
    syncClock = None

    def __init__(self, tempo=TEMPO_120_24, meter=None, meters=(), reactor=None, syncClockClass=None, default=False):
        """
        tempo: The tempo in beats per minute (default: 130)
        meters: Meters used by the clock - default to [ Meter(4,4) ]
        reactor: The underlying reactor to drive this BeatClock - this defaults to the global
            reactor (i.e "from twisted.internet import reactor")
        syncClockClass: SyncClock class to use for synchronizing the clock's ticks and scheduling
            offset (if None, no SyncClock will be used). See bl.sync.
        default: If True, BeatClock.defaultClock will be set to the instance - this is used
            by other components to get the default global BeatClock.
        """
        global clock
        self.tempo = tempo
        self.ticks = 0
        self.meters = meters
        self._meter_schedule = {}
        if not self.meters:
            self.meters = [Meter(4,4,1,tempo=self.tempo)]
        else:
            warnings.warn('meters argument is deprecated, use meter=oneMeterNotAList instead')
        self.meter = meter or self.meters[0]
        if not reactor:
            from twisted.internet import reactor
        self.reactor = reactor
        if default or (self.defaultClock is None):
            BeatClock.defaultClock = self
            clock = self

        if syncClockClass:
            self.syncClock = syncClockClass(self)
            lasttick, ts = self.syncClock.lastTick()
            self.ticks = lasttick

        SelectReactor.__init__(self)

    def setTempo(self, tempo):
        """
        Change the current tempo. Note that this has the side-effect of restarting
        the underlying task driving the BeatClock and resyncing to the syncClock if
        there is a syncClock. BUG: resyncing to SyncClock on tempo changes causes
        scheduled events not get called for an unreasonable amount of time. Hopefully
        this will resolved soon, but for the time being don't change the tempo at runtime
        and set before starting the clock (e.g. with beatlounge command use the -t arg
        to set the tempo in advance).

        tempo: The tempo (instance of Tempo)
        """
        self.tempo = tempo
        if hasattr(self, 'task'):
            self.task.stop()
            self.task.start(60. / self.tempo.tpm, True)

        if self.syncClock:
            lasttick, ignore = self.syncClock.lastTick()
            self.ticks = lasttick

    def run(self):
        """
        Start the BeatClock. Note that if twisted's reactor has not been started this
        will start it. This is done for you by bl/console.py (beatlounge command)
        so you generally should not call this directly in interpreter sessions.
        """
        self._initBackends()
        self.startTicking()
        self.running = True
        if not self.reactor.running:
            self.reactor.run()


    def _initBackends(self):
        # XXX this should be refactored some - make backends pluggable and indicate
        # which to start from a command line, etc.
        try:
            from bl.instrument import fsynth
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
        """
        Called by run - do not call me directly. Start the LoopingCall which
        will drive the BeatClock.
        """
        self.task = LoopingCall(self.tick)
        self.on_stop = self.task.start(60. / self.tempo.tpm, True)

    def tick(self):
        """
        Advance ticks and run delayed calls.
        """
        if self.syncClock:
            ticks, ts = self.syncClock.lastTick()
            if self.ticks > (ticks + 1):
                if DEBUG:
                    log.msg("We're ahead by %s ticks, waiting" % (self.ticks - (ticks + 1)))
                return
        self.ticks += 1
        self.runUntilCurrent()
        if self.syncClock:
            tick, ts = self.syncClock.lastTick()
            if tick > self.ticks:
                self._syncToTick(tick, ts)
            next = self.task._expectNextCallAt
            if abs(next - ts) > 0.0005:
                if DEBUG:
                    log.msg('Off by: %3.3fms; skewing time' % (1000. * (next - ts)))
                self.task._expectNextCallAt -= (next - ts)

    def _syncToTick(self, tick, ts):
        """
        Synchronize the current ticks based on tick and timestamp (ts) reported
        by the SyncClock.
        """
        # TODO - quiet everything somehow
        delta = tick - self.ticks
        if DEBUG:
            log.msg("We're behind by %s ticks (ticks=%s expected=%s)" % (delta, self.ticks, tick))
        tpm = self.meter.ticksPerMeasure
        if delta > tpm:
            t = tick % tpm
            ct = self.ticks % tpm
            if t < ct:
                t += tpm
            delta = t - ct

        # Do some catchup
        for i in range(delta):
            if DEBUG:
                log.msg('Catch up tick: %d' % i)
            self.ticks += 1
            self.runUntilCurrent()
        # XXX not very smart to do this considering tick based scheduling
        # - i.e. we need to take something already scheduled for tick N and make it instead
        # schedule for N + delta or something (???)

        # First normalize the timed events
        offset = tick - self.ticks
        if DEBUG:
            log.msg('Adjusting delayed calls ticks by offset: %s' % offset)
        for call in self._pendingTimedCalls:
            if DEBUG:
                log.msg('Call time was %s' % call.time)
            call.time += offset
            if DEBUG:
                log.msg('Call time now %s' % call.time)
        if DEBUG:
            log.msg('Reset ticks to %s' % tick)
        self.ticks = tick


    def seconds(self):
        """
        Seconds is the number of ticks since startup or ticks as derived from our
        SyncClock if we have one.
        """
        return self.ticks

    def schedule(self, _f, *args, **kwargs):
        """
        Schedule a callable to run on a periodic basis. This will return a ScheduledEvent
        which can be used to start calls to _f and stop based on the clock's meter.

        _f: the function to schedule calls to
        args: positional args to call _f with
        kwargs: keyword args to call _f
        """
        event = ScheduledEvent(self, _f, *args, **kwargs)
        return event

    def callWhenRunning(self, *a, **kw):
        return self.reactor.callWhenRunning(*a, **kw)

    def callAfterMeasures(self, measures, f, *a, **kw):
        """
        Call a function after measures have elapsed. Measures can be a float or 2-tuple
        (see measuresToTicks for details on how measures are converted to ticks).

        measures: Measures to wait before calling f
        f: A callable
        a: postional args to call f with
        kw: keyword args to call f with
        """
        ticks = self.meter.nextMeasure(self.ticks, measures)
        self.callLater(ticks, f, *a, **kw)

    def nudge(self, pause=0.1):
        """
        Pause the BeatClock for pause seconds. This is only useful if a syncClock
        can't be used and you want to manually sync the BeatClock with some external
        system.

        pause: seconds to nudge
        """
        if not hasattr(self, 'task'):
            raise ValueError("Cannot nudge a clock that hasn't started")
        self.task.stop()
        self.reactor.callLater(pause, self.task.start, 60. / self.tempo.tpm, True)




class ScheduledEvent(object):
    """
    A ScheduledEvent is a wrapper around a callable which
    can be scheduled at a future date with calls repeated for a given
    interval until stopped.
    """

    meter = None

    def __init__(self, clock, _f, *args, **kwargs):
        self.clock = clock
        self.call = (_f, args, kwargs)


    def startAfterTicks(self, ticks, interval):
        """
        Start scheduled event after ticks. Calls to wrapped callable will recur every interval ticks.
        This is for raw tick-based schedulingl use startAfter for a simpler metrical api.
        """
        def _start():
            self.clock.callLater(ticks, self.start, interval, True)
        self.clock.callWhenRunning(_start)
        return self


    def startAfter(self, measures=1, interval=(1,4), n=0, d=4):
        """
        Start event after measures and division (n/d). Interval is a two-tuple expression
        interval (e.g. (1,4) for every quarter note). This will calculate ticks based
        on active meter (the meter assigned to the clock this schedule event was generated
        from) and call startAfterTicks().
        """
        meter = self.clock.meter
        ticks = None
        if measures == 0:
            m = meter.measure(self.clock.ticks) * meter.ticksPerMeasure
            if self.clock.ticks > m:
                measures = 1
            else:
                ticks = 0
        if ticks is None:
            ticks = meter.nm(self.clock.ticks, measures) + meter.dtt(n,d) - self.clock.ticks
        self.startAfterTicks(ticks, meter.dtt(interval[0], interval[1]))

    def start(self, ticks=None, now=True):
        """
        Start calling our target function now. This is called by startLater; generally you
        should not use this method directly.
        """
        def _start():
            self.task = LoopingCall(self.call[0], *self.call[1], **self.call[2])
            self.task.clock = self.clock
            self.deferred = self.task.start(ticks, now)
        self.clock.callWhenRunning(_start)
        return self


    def stopAfterTicks(self, ticks):
        """
        Stop schedule event after ticks. This is for raw tick-based scheduling; use
        stopAfter for a simpler metrical api.
        """
        def _schedule_stop():
            def _stop():
                if hasattr(self, 'task'):
                    self.task.stop()
                else:
                    log.msg('tried to stop an event that has not yet started')
            self.clock.callLater(ticks, _stop)
        self.clock.callWhenRunning(_schedule_stop)
        return self

    def stopAfter(self, measures=1, n=0, d=4):
        """
        Stop event after measures and division (n/d). This will calculate ticks based
        on active meter (the meter assigned to the clock this schedule event was generated
        from) and call stopAfterTicks().
        """
        meter = self.clock.meter
        ticks = meter.nm(measures) + meter.dtt(n,d) - self.clock.ticks
        self.stopAfterTicks(ticks)

    def stop(self):
        """
        Stop calling the target function now. This is called by stopLater; generally
        you should not call this method directly.
        """
        if hasattr(self, 'task') and self.task.running:
            self.task.stop()


clock = BeatClock()

