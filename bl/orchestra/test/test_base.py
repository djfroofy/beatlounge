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
        def schedule():
            while 1:
                yield (time, func,
                       {'a': a, 'b': b})
        player = SchedulePlayer(schedule(), clock=self.clock)
        self.runTicks(25)
        self.assertEquals(func.calls, [])
        player.startPlaying()
        self.runTicks((96 - 25) + 96)
        self.assertEquals(func.calls,
                          [(96, {'a': 0, 'b': 0}), (120, {'a': 1, 'b': 2}),
                           (144, {'a':2, 'b': 4}), (168, {'a': 3, 'b': 6}),
                           (192, {'a': 4, 'b':8})])
