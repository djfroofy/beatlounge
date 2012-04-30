from itertools import cycle

from bl.utils import getClock
from bl.instrument.interfaces import IMIDIInstrument
from bl.orchestra.base import (SchedulePlayer, schedule, childSchedule,
                               timing, OneSchedulePlayerMixin)


__all__ = ['Player', 'ChordPlayer']


class CallMemo(object):

    def __init__(self, ugen):
        self.ugen = ugen

    def __call__(self):
        self.value = self.ugen()
        return self.value

    def lastValue(self):
        return self.value


class Player(OneSchedulePlayerMixin):

    onMethodName = 'noteon'
    offMethodName = 'noteoff'

    def __init__(self, instr, note, velocity=None, release=None,
                 interval=(1, 8), time=None, clock=None, cc=None):
        """
        @param note: A ugen for notes
        @param velocity: A ugen for the velocity
        @param release: A ugen for the release (amount of time before calling
        noteoff)
        @param time: A ugen for relative time (values returned must be greater
        than or equal to previously returned value - monotonically increasing)
        @param interval: An interval division (e.g. C{(1, 4)}) that may be
        specified as an alternative to time--this creates a metronome with the
        given interval.
        @param cc: C{dict} of control-change ugens.
        @param clock: A L{BeatClock} (defaults to global default clock)
        """
        self.instr = IMIDIInstrument(instr)
        self.clock = getClock(clock)
        if velocity is None:
            velocity = cycle([127]).next
        self.note = note
        self.velocity = velocity
        self.release = release
        self.cc = cc
        self.time = timing(self.clock, time, interval)
        noteMemo = CallMemo(lambda: self.note())
        noteonSchedule = schedule(self.time, self.noteon,
                                  {'note': noteMemo,
                                   'velocity': (lambda: self.velocity())})
        self.schedulePlayer = SchedulePlayer(noteonSchedule, self.clock)
        if self.release:
            releaseChild = childSchedule(self._scheduleNoteoff,
                                     {'note': noteMemo.lastValue,
                                      'when': (lambda: self.release())})
            self.schedulePlayer.addChild(releaseChild)
        if cc:
            ccChild = childSchedule(self.instr.controlChange, self.cc)
            self.schedulePlayer.addChild(ccChild)

    def noteon(self, note, velocity):
        m = getattr(self.instr, self.onMethodName)
        return m(note, velocity)

    def noteoff(self, note):
        m = getattr(self.instr, self.offMethodName)
        return m(note)

    def _scheduleNoteoff(self, note, when):
        if when is None:
            return
        self.clock.callLater(when, self.noteoff, note)


class ChordPlayer(Player):

    onMethodName = 'chordon'
    offMethodName = 'chordoff'
