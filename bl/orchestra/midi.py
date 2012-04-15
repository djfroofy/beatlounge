from itertools import cycle

from bl.utils import getClock
from bl.instrument.interfaces import IMIDIInstrument
from bl.orchestra.base import SchedulePlayer, schedule, childSchedule, metronome


class CallMemo(object):

    def __init__(self, ugen):
        self.ugen = ugen

    def __call__(self):
        self.value = self.ugen()
        return self.value

    def lastValue(self):
        return self.value


class OneSchedulePlayerMixin(object):

    schedulePlayer = None

    def resumePlaying(self):
        self.schedulePlayer.resumePlaying()

    def pausePlaying(self):
        self.schedulePlayer.pausePlaying()


class Player(OneSchedulePlayerMixin):

    onMethodName = 'noteon'
    offMethodName = 'noteoff'

    def __init__(self, instr, notes, velocity=None, release=None,
                 interval=(1,8), time=None, clock=None):
        self.instr = IMIDIInstrument(instr)
        self.clock = getClock(clock)
        if velocity is None:
            velocity = cycle([127]).next
        self.notes = notes
        self.velocity = velocity
        self.release = release
        if time is None:
            if type(interval) in (list, tuple):
                interval = self.clock.meter.dtt(*interval)
            time = metronome(interval).next
        noteMemo = CallMemo(notes)
        noteonSchedule = schedule(time, self.noteon,
                                  {'note': noteMemo, 'velocity': velocity})
        self.schedulePlayer = SchedulePlayer(noteonSchedule, self.clock)
        if self.release:
            releaseChild = childSchedule(self._scheduleNoteoff,
                                     {'note': noteMemo.lastValue,
                                      'when': self.release})
            self.schedulePlayer.addChild(releaseChild)

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
