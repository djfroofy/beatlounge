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

from bl.debug import DEBUG

__all__ = ['Beat', 'Meter', 'standardMeter', 'BeatClock', 'measuresToTicks', 'mtt',
            'ScheduledEvent', 'clock' ]

_BeatBase = namedtuple('_BeatBase', 'measure quarter eighth sixteenth remainder')

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

    def __init__(self, length=4, division=4, number=1):
        self.length = length
        self.division = division
        self.number = number
        self._quarters_per_measure = self.length * self.number / (self.division / 4.)
        self._hash = hash((self.length, self.division, self.number))
        self.ticksPerMeasure = int(24 * self.length * 4. / self.division * self.number)


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

    def __init__(self, tempo=130, meters=(), reactor=None, syncClockClass=None, default=False):
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

        tempo: The tempo (BPM)
        """
        self._tick_interval = (60. / tempo) * (1./24)
        if hasattr(self, 'task'):
            self.task.stop()
            self.task.start(self._tick_interval, True)
        self.tempo = tempo

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
        self.on_stop = self.task.start(self._tick_interval, True)

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
        tpm = self.meters[0].ticksPerMeasure
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
        meter = self.meters[0]
        ticks = _ticks(measures, meter, self)
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
        self.reactor.callLater(pause, self.task.start, self._tick_interval, True)



def measuresToTicks(measures, meter=standardMeter):
    """
    short alias: mtt

    Convert measures to ticks. Measures can either be a float or a tuple consisting of
    the number of whole measures followed by the number of quarter notes. The meter
    can be specified to aid conversion of measures to ticks since the number of ticks
    per measure are dependent on the meter (4/4 contains 96, whereas 3/4 contains 72,
    for example). Note if measures are given as a float, the fractional part of the number
    is a factor of the standard meter (4/4), so 0.25 is a quarter and mtt(1.25, Meter(3/4)) will
    give us 96 ticks (72 for the measure plus 24 for one quarter note (0.25)). This also
    means that floats are not fully expressive for measures containing more than exactly 4
    quarters (examples including 9/8, 11/8, etc); in such cases the tuple representation
    should be used instead.

    Some examples of measures given a as float:

        >>> mtt(1.5, Meter(4,4)) # 1 whole + 1 half
        144
        >>> mtt(1.5, Meter(3,4)) #  1 whole + 1 quarter
        120

    Some examples of measures given as tuple:

        >>> mtt((1,2), Meter(3,4)) # 1 whole + 1 quarter note
        120
        >>> mtt((1,5), Meter(11,8)) # 2 wholes + 1 half + 1 eighth
        252
    """
    if type(measures) in (tuple, list):
        whole_measures, quarters = measures
        mantissa = quarters / 4.
    else:
        whole_measures = int(measures)
        mantissa = measures - whole_measures
    return int(whole_measures * meter.ticksPerMeasure + 96 * mantissa)

mtt = measuresToTicks

def _ticks(measures, meter, clock):
    current_measure = meter.measure(clock.ticks)
    #tick = int(current_measure * meter.ticksPerMeasure + measures * meter.ticksPerMeasure)
    tickslater = mtt(measures, meter)
    tick = current_measure * meter.ticksPerMeasure + tickslater
    ticks = tick - clock.seconds()
    if ticks < 0:
        ticks += meter.ticksPerMeasure
    return ticks


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

    def startLater(self, measures=1, frequency=0.25, ticks=None, meter=None):
        """
        Begin calling our callable after measures (or raw ticks if specified).
        Frequency is the interval in measures to repeat calls to our callable.
        If a meter is given, this will be used as the basis for converting measures and frequency
        to ticks; otherwise the events bound meter of the clock's default meter are used
        for conversion.

        (See measuresToTicks for details on how measures and frequency are converted to clock ticks).
        """
        if measures < 0:
            raise ValueError("measures must be greater than zero")
        meter = meter or self.meter or self.clock.meters[0]
        if ticks is None:
            #ticks = frequency * standardMeter.ticksPerMeasure
            # Use meters to ticks for meter-relative frequency
            ticks = mtt(frequency, meter)
        def _start_later():
            ticksLater = _ticks(measures, meter, self.clock)
            #ticksLater = mtt(measures, meter)
            self.clock.callLater(ticksLater, self.start, ticks, True)
        self.clock.callWhenRunning(_start_later)
        return self

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

    def stopLater(self, measures=1, meter=None, ticks=None):
        """
        Stop calling the callable after measures.

        If a meter is given, this will be used as the basis for converting measures and frequency
        to ticks; otherwise the events bound meter of the clock's default meter are used
        for conversion.

        (See measuresToTicks for details on how measures are converted to clock ticks).
        """

        meter = meter or self.meter or self.clock.meters[0]
        ticks_ = ticks
        def _scheduleStop():
            ticks = ticks_
            if ticks is None:
                ticks = _ticks(measures, meter, self.clock)
                #ticks = mtt(measures, meter)
            def _stop():
                if hasattr(self, 'task'):
                    self.task.stop()
                else:
                    log.msg('Tried to stop an event that has not yet started')
            self.clock.callLater(ticks, _stop)
        self.clock.callWhenRunning(_scheduleStop)
        return self

    def stop(self):
        """
        Stop calling the target function now. This is called by stopLater; generally
        you should not call this method directly.
        """
        if hasattr(self, 'task') and self.task.running:
            self.task.stop()

    def bindMeter(self, meter):
        """
        Bind a meter to this event. When bound, the meter will be used in calls
        to startLater() and stopLater() to derive ticks based on measures. If no
        meter is bound, then in the said calls the clock's default meter will be
        used.
        """
        self.meter = meter
        return self

BPM = 130
clock = BeatClock(BPM)

