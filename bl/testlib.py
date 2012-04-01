

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


class TestInstrument:

    def __init__(self, clock):
        self.clock = clock
        self.plays = []
        self.stops = []

    def playnote(self, note, velocity):
        self.plays.append(('note', self.clock.ticks, note, velocity))

    def stopnote(self, note):
        self.stops.append(('note', self.clock.ticks, note))

    def playchord(self, chord, velocity):
        self.plays.append(('chord', self.clock.ticks, chord, velocity))

    def stopchord(self, chord):
        self.stops.append(('chord', self.clock.ticks, chord))
