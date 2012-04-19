from itertools import cycle

from twisted.trial.unittest import TestCase

from bl.scheduler import Tempo, Meter, BeatClock
from bl.testlib import ClockRunner, TestReactor
from bl.orchestra.base import SchedulePlayer


class TestFunc(object):

    def __init__(self, clock):
        self.clock = clock
        self.calls = []

    def __call__(self, **kw):
        self.calls.append((self.clock.ticks, kw))


def schedule(time, func, a, b):
    while 1:
        yield (time, func,
               {'a': a, 'b': b})


def schedule2(time, func, a, b):
    while 1:
        t = time()
        yield (t, func,
               {'a': a, 'b': b})


class SchedulePlayerTestCase(TestCase, ClockRunner):

    def setUp(self):
        self.tempo = Tempo(135)
        self.meter = Meter(4, 4, tempo=self.tempo)
        self.clock = BeatClock(tempo=self.tempo, meter=self.meter,
                               reactor=TestReactor())

    def test_basic(self):
        func = TestFunc(self.clock)
        time = (v for v in xrange(0, 1024, 24)).next
        a = (v for v in xrange(1024)).next
        b = (v for v in xrange(0, 1024, 2)).next
        player = SchedulePlayer(schedule(time, func, a, b), clock=self.clock)
        self.runTicks(25)
        self.assertEquals(func.calls, [])
        player.resumePlaying()
        self.runTicks((96 - 25) + 96)
        self.assertEquals(func.calls,
                          [(96, {'a': 0, 'b': 0}), (120, {'a': 1, 'b': 2}),
                           (144, {'a':2, 'b': 4}), (168, {'a': 3, 'b': 6}),
                           (192, {'a': 4, 'b':8})])

    def test_children(self):
        func = TestFunc(self.clock)
        time = (v for v in xrange(0, 1024, 24)).next
        a = (v for v in xrange(1024)).next
        b = (v for v in xrange(0, 1024, 2)).next
        func2 = TestFunc(self.clock)
        c = (v for v in xrange(0, 1024, 7)).next
        player = SchedulePlayer(schedule(time, func, a, b), clock=self.clock)
        player.addChild(((func2, {'z': c}) for i in cycle([1])))
        self.runTicks(25)
        self.assertEquals(func.calls, [])
        player.resumePlaying()
        self.runTicks((96 - 25) + 96)
        self.assertEquals(func.calls,
                          [(96, {'a': 0, 'b': 0}), (120, {'a': 1, 'b': 2}),
                           (144, {'a':2, 'b': 4}), (168, {'a': 3, 'b': 6}),
                           (192, {'a': 4, 'b':8})])
        self.assertEquals(func2.calls,
                          [(96, {'z': 0}), (120, {'z': 7}), (144, {'z': 14}),
                           (168, {'z': 21}), (192, {'z': 28})])

    def test_children_that_stop(self):
        func = TestFunc(self.clock)
        time = (v for v in xrange(0, 1024, 24)).next
        a = (v for v in xrange(1024)).next
        b = (v for v in xrange(0, 1024, 2)).next
        func2 = TestFunc(self.clock)
        c = (v for v in xrange(0, 1024, 7)).next
        func3 = TestFunc(self.clock)
        d = (v for v in xrange(0, 1024, 3)).next
        player = SchedulePlayer(schedule(time, func, a, b), clock=self.clock)
        g1 = ((func2, {'z': c}) for i in cycle([1]))
        player.addChild(g1)
        g2 = ((func3, {'z': d}) for i in range(3))
        player.addChild(g2)
        self.runTicks(25)
        self.assertEquals(func.calls, [])
        player.resumePlaying()
        self.runTicks((96 - 25) + 96)
        self.assertEquals(func.calls,
                          [(96, {'a': 0, 'b': 0}), (120, {'a': 1, 'b': 2}),
                           (144, {'a':2, 'b': 4}), (168, {'a': 3, 'b': 6}),
                           (192, {'a': 4, 'b':8})])
        self.assertEquals(func2.calls,
                          [(96, {'z': 0}), (120, {'z': 7}), (144, {'z': 14}),
                           (168, {'z': 21}), (192, {'z': 28})])
        self.assertEquals(func3.calls, [(96, {'z': 0}), (120, {'z': 3}),
                                       (144, {'z': 6})])
        self.failIf(g2 in player._scheduleChildren)
        self.assert_(g1 in player._scheduleChildren)

    def test_pause(self):
        func = TestFunc(self.clock)
        time = (v for v in xrange(0, 1024, 24)).next
        a = (v for v in xrange(1024)).next
        b = (v for v in xrange(0, 1024, 2)).next
        player = SchedulePlayer(schedule(time, func, a, b), clock=self.clock)
        self.runTicks(25)
        self.assertEquals(func.calls, [])
        player.resumePlaying()
        self.runTicks((96 - 25) + 96)
        player.pause()
        self.runTicks(96)
        expected = [(96, {'a': 0, 'b': 0}), (120, {'a': 1, 'b': 2}),
                    (144, {'a':2, 'b': 4}), (168, {'a': 3, 'b': 6}),
                    (192, {'a': 4, 'b':8})]
        self.assertEquals(func.calls, expected)
        player.play()
        self.runTicks(96 * 2)
        expected.extend([(288, {'a': 5, 'b': 10}), (312, {'a': 6, 'b': 12}),
                         (336, {'a': 7, 'b': 14}), (360, {'a': 8, 'b': 16}),
                         (384, {'a': 9, 'b': 18}), (408, {'a': 10, 'b': 20}),
                         (432, {'a': 11, 'b': 22}), (456, {'a': 12, 'b': 24}),
                         (480, {'a': 13, 'b': 26})])
        self.assertEquals(func.calls, expected)

    def test_exhausting_schedule(self):
        func = TestFunc(self.clock)
        time = (v for v in xrange(0, 97, 24)).next
        a = (v for v in xrange(1024)).next
        b = (v for v in xrange(0, 1024, 2)).next
        player = SchedulePlayer(schedule2(time, func, a, b),
                                clock=self.clock)
        self.runTicks(96)
        player.resumePlaying()
        self.runTicks(192)
        expected = [(96, {'a': 0, 'b': 0}), (120, {'a': 1, 'b': 2}),
                    (144, {'a':2, 'b': 4}), (168, {'a': 3, 'b': 6}),
                    (192, {'a': 4, 'b':8})]
        self.assertEquals(func.calls, expected)

    def test_time_in_past_busts_the_scheduler(self):
        func = TestFunc(self.clock)
        time = (v for v in [0, 24, 12, 48, 96]).next
        a = (v for v in xrange(1024)).next
        b = (v for v in xrange(0, 1024, 2)).next
        player = SchedulePlayer(schedule(time, func, a, b),
                                clock=self.clock)
        player.resumePlaying()
        self.runTicks(96)
        self.assert_(self.flushLoggedErrors())
        expected = [(0, {'a': 0, 'b': 0}), (24, {'a': 1, 'b': 2})]
        self.assertEquals(func.calls, expected)

    def test_pausePlaying(self):
        func = TestFunc(self.clock)
        time = (v for v in [24, 48, 108, 120, 144, 168, 192, 288]).next
        a = (v for v in xrange(1024)).next
        b = (v for v in xrange(0, 1024, 2)).next
        player = SchedulePlayer(schedule(time, func, a, b), clock=self.clock)
        player.resumePlaying()
        self.runTicks(1)
        player.pausePlaying()
        self.runTicks(191)
        player.resumePlaying()
        self.runTicks(96)
        expected = [(24, {'a': 0, 'b': 0}), (48, {'a': 1, 'b': 2}),
                    (204, {'a': 2, 'b': 4}), (216, {'a': 3, 'b': 6}),
                    (240, {'a': 4, 'b': 8}), (264, {'a': 5, 'b': 10}),
                    (288, {'a': 6, 'b': 12})]
        self.assertEquals(func.calls, expected)
