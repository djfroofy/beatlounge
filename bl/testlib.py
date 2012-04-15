from zope.interface import implements

from bl.instrument.interfaces import IMIDIInstrument


class ClockRunner:

    def runTicks(self, ticks):
        for i in range(ticks):
            self.clock.runUntilCurrent()
            self.clock.tick()
        self.clock.runUntilCurrent()

    _runTicks = runTicks


class TestReactor(object):
    running = True

    def __init__(self):
        from twisted.internet import reactor
        self.reactor = reactor
        self.scheduled = []

    def callWhenRunning(self, f, *a, **k):
        f(*a, **k)

    def __getattr__(self, a):
        return getattr(self.reactor, a)

    def callLater(self, later, f, *a, **k):
        self.scheduled.append((later, f, a, k))


class TestInstrument(object):
    implements(IMIDIInstrument)

    def __init__(self, clock):
        self.clock = clock
        self.plays = []
        self.stops = []
        self.cc = []

    def noteon(self, note, velocity):
        self.plays.append(('note', self.clock.ticks, note, velocity))

    playnote = noteon

    def noteoff(self, note):
        self.stops.append(('note', self.clock.ticks, note))

    stopnote = noteoff

    def chordon(self, chord, velocity):
        self.plays.append(('chord', self.clock.ticks, chord, velocity))

    playchord = chordon

    def chordoff(self, chord):
        self.stops.append(('chord', self.clock.ticks, chord))

    stopchord = chordoff

    def controlChange(self, **kwargs):
        self.cc.append((self.clock.ticks, kwargs))
