from functools import partial

from twisted.trial.unittest import TestCase

from txbeatlounge.scheduler2 import BeatClock, Meter

import data

class ClockRunner:

    def _runTicks(self, ticks):
        for i in range(ticks):
            self.clock.runUntilCurrent()
            self.clock.tick()


class TestReactor(object):

    def __init__(self):
        from twisted.internet import reactor
        self.reactor = reactor

    def callWhenRunning(self, f, *a, **k):
        f(*a, **k)

    def __getattr__(self, a):
        return getattr(self.reactor, a)


class TestInstrument:

    def __init__(self, name, clock, callq):
        self.name = name
        self.clock = clock
        self.callq = callq

    def __call__(self):
        self.callq.append((self.clock.ticks, self.name))


class MeterTests(TestCase):

    def setUp(self):
        self.meterStandard = Meter(4,4) 
        self.meter34 = Meter(3,4)
        self.meter54 = Meter(5,4)
        self.meter98 = Meter(9,8) 


    def test_beat(self):
        beats = []
        for i in range(96 * 2):
            beats.append(self.meterStandard.beat(i))
        self.assertEquals(beats, data.measure_standard_beats)
       
        beats = []
        for i in range(96 * 2):
            beats.append(self.meter34.beat(i)) 
        self.assertEquals(beats, data.measure_34_beats)

        beats = []
        for i in range(96 * 2):
            beats.append(self.meter54.beat(i))
        self.assertEquals(beats, data.measure_54_beats)
        
        beats = []
        for i in range(96 * 2):
            beats.append(self.meter98.beat(i))
        self.assertEquals(beats, data.measure_98_beats)

        
        
class ClockTests(TestCase, ClockRunner):


    def setUp(self):
        self.meters = [ Meter(4,4), Meter(3,4) ]
        self.meterStandard = self.meters[0]
        self.meter34 = self.meters[1]
        self.clock = BeatClock(135, meters=self.meters, reactor=TestReactor())


    def test_defaultMeterIsStandard(self):
        clock = BeatClock(120)
        self.assertEquals(len(clock.meters), 1)
        meter = clock.meters[0]
        self.assertEquals(meter.length, 4)
        self.assertEquals(meter.division, 4)
        self.assertEquals(meter.number, 1)


    def test_startLater(self):
        called = []

        instr1 = TestInstrument('f1', self.clock, called)

        self.clock.schedule(instr1).startLater(0, 0.25)
        self._runTicks(96 * 2)

        expected = [(0, 'f1'), (24, 'f1'), (48, 'f1'), (72, 'f1'), (96, 'f1'),
                    (120, 'f1'), (144, 'f1'), (168, 'f1'), (192, 'f1')]
        self.assertEquals(called, expected)
        
        called[:] = []

        instr2 = TestInstrument('f2', self.clock, called)
        
        self.clock.schedule(instr2).startLater(1.0, 1.0 / 3)
        self._runTicks(96 * 2)
        expected = [(216, 'f1'), (240, 'f1'), (264, 'f1'), (288, 'f2'), (288, 'f1'),
                    (312, 'f1'), (320, 'f2'), (336, 'f1'), (352, 'f2'), (360, 'f1'),
                    (384, 'f2'), (384, 'f1')]
        self.assertEquals(called, expected)


    def test_startLaterWithMeter(self):
        called = []

        instr1 = TestInstrument('f1', self.clock, called)
        instr2 = TestInstrument('f2', self.clock, called)
        
        self.clock.schedule(instr1).startLater(1.0, 0.25, meter=self.meterStandard)
        self.clock.schedule(instr2).startLater(1.0, 0.25, meter=self.meter34)

        self._runTicks(96 * 2)

        expected = [(72, 'f2'), (96, 'f2'), (96, 'f1'), (120, 'f2'), (120, 'f1'),
                    (144, 'f2'), (144, 'f1'), (168, 'f2'), (168, 'f1'),
                    (192, 'f2'), (192, 'f1')]
        self.assertEquals(len(called), len(expected))
        self.assertEquals(set(called), set(expected))



