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


class SchedulePlayerTestCase(TestCase, ClockRunner):

    def setUp(self):
        self.tempo = Tempo(135)
        self.meter = Meter(4,4, tempo=self.tempo)
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
        player.startPlaying()
        self.runTicks((96 - 25) + 96)
        self.assertEquals(func.calls,
                          [(96, {'a': 0, 'b': 0}), (120, {'a': 1, 'b': 2}),
                           (144, {'a':2, 'b': 4}), (168, {'a': 3, 'b': 6}),
                           (192, {'a': 4, 'b':8})])

    def test_pause(self):
        func = TestFunc(self.clock)
        time = (v for v in xrange(0, 1024, 24)).next
        a = (v for v in xrange(1024)).next
        b = (v for v in xrange(0, 1024, 2)).next
        player = SchedulePlayer(schedule(time, func, a, b), clock=self.clock)
        self.runTicks(25)
        self.assertEquals(func.calls, [])
        player.startPlaying()
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
                         (432, {'a': 11,'b': 22}), (456, {'a': 12, 'b': 24}),
                         (480, {'a': 13, 'b': 26})])
        self.assertEquals(func.calls, expected)

