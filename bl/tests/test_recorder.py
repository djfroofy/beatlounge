from twisted.trial.unittest import TestCase

from bl.scheduler import BeatClock, Meter
from bl.testlib import ClockRunner, TestReactor
from bl.recorder import LoopRecorder


class LoopRecorderTests(TestCase, ClockRunner):

    def setUp(self):
        self.clock = BeatClock(reactor=TestReactor())

    def test_record_and_latch(self):
        self.runTicks(23)
        loopRecorder = LoopRecorder(1, self.clock, Meter(4, 4))
        self.runTicks(73)
        for c in 'abcdefghi':
            loopRecorder.record(c)
            self.runTicks(24)
        current = loopRecorder.latch()
        self.assertEquals(current, [('e', 0), ('f', 24), ('g', 48), ('h', 72)])
        last = loopRecorder.latch(1)
        self.assertEquals(last, [('a', 0), ('b', 24), ('c', 48), ('d', 72)])

    def test_record_with_non_standard_meter(self):
        loopRecorder = LoopRecorder(1, self.clock, Meter(3, 4))
        for c in 'abcde':
            loopRecorder.record(c)
            self.runTicks(24)
        current = loopRecorder.latch()
        self.assertEquals(current, [('a', 0), ('b', 24), ('c', 48)])

    def test_max_loop_depth(self):
        loopRecorder = LoopRecorder(1, self.clock, Meter(4, 4))
        for i in range(80):
            loopRecorder.record(i)
            self.runTicks(24)
        self.assertEquals(len(loopRecorder._loops), 10)

    def test_ticks_are_relative_to_loop_start(self):
        loopRecorder = LoopRecorder(3, self.clock, Meter(4, 4))
        self.runTicks(12)
        loopRecorder.record('a')
        self.runTicks(84)
        loopRecorder.record('b')
        self.runTicks(12)
        loopRecorder.record('c')
        self.runTicks(84)
        loopRecorder.record('d')
        self.runTicks(12)
        loopRecorder.record('e')
        self.runTicks(84)
        loopRecorder.record('f')
        current = loopRecorder.latch()
        self.assertEquals(current, [('a', 12), ('b', 96), ('c', 108),
                                    ('d', 192), ('e', 204)])
