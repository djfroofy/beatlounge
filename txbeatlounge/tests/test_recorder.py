from twisted.trial.unittest import TestCase


from txbeatlounge.scheduler import BeatClock, Meter
from txbeatlounge.testlib import ClockRunner, TestReactor
from txbeatlounge.recorder import LoopRecorder


class LoopRecorderTests(TestCase, ClockRunner):

    def setUp(self):
        self.clock = BeatClock(135, meters=[Meter(4,4)], reactor=TestReactor())

    def test_record_and_latch(self):
        self.runTicks(23)
        loopRecorder = LoopRecorder(1, self.clock, Meter(4,4))
        self.runTicks(73)
        for c in 'abcdefghi':
            loopRecorder.record(c)
            self.runTicks(24)
        current = loopRecorder.latch()
        self.assertEquals(current, [('e',0),('f',24),('g',48),('h',72)])
        last = loopRecorder.latch(1)
        self.assertEquals(last, [('a',0),('b',24),('c',48),('d',72)])


    def test_max_loop_depth(self):
        loopRecorder = LoopRecorder(1, self.clock, Meter(4,4))
        for i in range(80):
            loopRecorder.record(i)
            self.runTicks(24)
        self.assertEquals(len(loopRecorder._loops), 10)


