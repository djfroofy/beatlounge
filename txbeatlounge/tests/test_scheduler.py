
from zope.interface import implements

from twisted.internet.defer import Deferred
from twisted.internet.interfaces import IReactorTime

from twisted.trial.unittest import TestCase


from txbeatlounge.scheduler import Scheduler
from txbeatlounge.scheduler import BeatClock, Timely

class FakeDelayedCall(object):

    def __init__(self, clock, call_id):
        self._clock = clock
        self._id = call_id

    def cancel(self):
        self._clock.cancelCallLater(self._id)
        return Deferred()

class FakeClock(object):
    """
    Knowlingly half-ass implementation - no DelayedCalls returned
    """
    implements(IReactorTime)

    ticks = 0
    _seq = -1

    def __init__(self):
        self._schedule = {}
        self._ids = {}

    def seconds(self):
        return self.ticks

    def callLater(self, delay, f, *a, **kw):
        when = self.ticks + delay
        if when == self.ticks:
            f(*a, **kw)
            return
        q = self._schedule.setdefault(when, [])
        callid = self._next_id()
        q.append((f, a, kw, callid))
        self._ids[callid] = when
        return FakeDelayedCall(self, callid)

    def cancelCallLater(self, callid):
        if callid not in self._ids:
            raise ValueError('Unkown call id: %s' % callid)
        when = self._ids.pop(callid)
        q = self._schedule[when]
        q = [ arr for arr in q if arr[-1] != callid ]
        self._schedule[when] = q

    def getDelayedCalls(self):
        return ()

    def _next_id(self):
        self._seq = self._seq + 1
        return self._seq

    def tick(self):
        self._schedule.pop(self.ticks, None)
        self.ticks = self.ticks + 1
        for (f, a, k, id) in self._schedule.get(self.ticks, []):
            if id not in self._ids:
                continue
            f(*a, **k)
            del self._ids[id]

    def tickUntil(self, ticks):
        for i in range(ticks):
            self.tick()


class TestReactor(object):

    def __init__(self):
        from twisted.internet import reactor
        self.reactor = reactor

    def callWhenRunning(self, f, *a, **k):
        f(*a, **k)

    def __getattr__(self, a):
        return getattr(self.reactor, a)

class SchedulerTests(TestCase):

    def setUp(self):
        from twisted.internet import reactor
        super(SchedulerTests, self).setUp()
        self.clock = FakeClock()
        self.schedule = Scheduler(self.clock,
                                  reactor=TestReactor()).schedule

    def test_start(self):
        seconds = [ ]

        def func(a, b=None):
            self.assertEquals(a, 1)
            self.assertEquals(b, 2)
            seconds.append(self.clock.seconds())
            
        self.schedule(func, 1, b=2).start(3, False)
        self.clock.tickUntil(10)
        self.assertEquals(seconds, [3, 6, 9])
        
    def test_start_now(self):
        seconds = [ ]

        def func(a, b=None):
            self.assertEquals(a, 1)
            self.assertEquals(b, 2)
            seconds.append(self.clock.seconds())
            
        self.schedule(func, 1, b=2).start(3, True)
        self.clock.tickUntil(10)
        self.assertEquals(seconds, [0, 3, 6, 9])


    def test_start_later(self):
        seconds = []

        def func(a, b=None):
            self.assertEquals(a, 1)
            self.assertEquals(b, 2)
            seconds.append(self.clock.seconds())
    
        self.schedule(func, 1, b=2).start_later(10, 3)
        self.clock.tickUntil(17)
        self.assertEquals(seconds, [10, 13, 16])
        

    def test_stop_at_interval(self):
        seconds = []
        
        def func():
            seconds.append(self.clock.seconds())

        self.schedule(func).start(3, True).stop_at_interval(15)
        self.clock.tickUntil(20)
        self.assertEquals(seconds, [0, 3, 6, 9, 12])
        


    def test_stop_after_iterations(self):
        seconds = []

        def func():
            seconds.append(self.clock.seconds())

        self.schedule(func).start(3, True).stop_after_iterations(3)
        self.clock.tickUntil(20)
        self.assertEquals(seconds, [0, 3, 6])
   

    def test_set_threshold_reached(self):
        something = [ None ]
        seconds = []

        def threshold_reached(se, count):
            se.task.stop()
            something[0] = self.clock.seconds()


        def func():
            seconds.append(self.clock.seconds())

        
        self.schedule(func).start(3, True).stop_after_iterations(3
            ).set_threshold_reached(threshold_reached)
        self.clock.tickUntil(20)
        self.assertEquals(seconds, [0, 3, 6])
        self.assertEquals(something, [6])

    def test_on_count(self):
        seconds = []
        counts = []

        def on_count(se, ct):
            counts.append(ct)

        def func():
            seconds.append(self.clock.seconds())

        self.schedule(func).set_on_count(on_count).start(2, True)

        self.clock.tickUntil(20)
        self.assertEquals(seconds, [0,2,4,6,8,10,12,14,16,18,20])
        self.assertEquals(counts, [1,2,3,4,5,6,7,8,9,10,11])


class BeatClockTests(TestCase):


    def setUp(self):
        super(BeatClockTests, self).setUp()
        self.clock = FakeClock()

    def test_bpm(self):
        beatclock = BeatClock(bpm=30, clock=self.clock)
        
        beats = []
        seconds = []

        def hitbeat():
            seconds.append(beatclock.seconds())
            beats.append(beatclock.beats())
            beatclock.callLater(1, hitbeat)
        
        beatclock.callLater(1, hitbeat)

        self.clock.tickUntil(11)

        self.assertEquals(seconds, [2,4,6,8,10])
        self.assertEquals(beats, [1.0, 2.0, 3.0, 4.0, 5.0])


class TimelyTests(TestCase):


    def setUp(self):
        super(TimelyTests, self).setUp()
        self.clock = FakeClock()


    def test_timely(self):
        timely = Timely(self.clock)

        seconds = []
        called = [ False ]
    
        @timely
        def make_beats(a, b=1):
            self.assertEquals(a, 1)
            self.assertEquals(b, 2)
            seconds.append(self.clock.seconds())
            yield 1
            seconds.append(self.clock.seconds())
            yield 2
            seconds.append(self.clock.seconds())
            yield 4
            seconds.append(self.clock.seconds())

        def cb(ignore):
            called[0] = True

        make_beats(1, b=2).addCallback(cb)

        self.clock.tickUntil(10)

        self.assertEquals(seconds, [0,1,3,7])
        self.assert_(called[0])



