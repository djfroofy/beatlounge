
class ClockRunner:

    def _runTicks(self, ticks):
        for i in range(ticks):
            self.clock.runUntilCurrent()
            self.clock.tick()


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
