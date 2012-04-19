from twisted.trial.unittest import TestCase

from bl.scheduler import BeatClock, Tempo, Meter

import data


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


class TestInstrument:

    def __init__(self, name, clock, callq):
        self.name = name
        self.clock = clock
        self.callq = callq

    def __call__(self):
        self.callq.append((self.clock.ticks, self.name))


class MeterTests(TestCase):

    def setUp(self):
        self.meterStandard = Meter(4, 4)
        self.meter34 = Meter(3, 4)
        self.meter54 = Meter(5, 4)
        self.meter98 = Meter(9, 8)

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
        self.meters = [Meter(4, 4), Meter(3, 4)]
        self.meterStandard = self.meters[0]
        self.meter34 = self.meters[1]
        self.clock = BeatClock(Tempo(135), meters=self.meters,
                               reactor=TestReactor())

    def test_defaultMeterIsStandard(self):
        clock = BeatClock(Tempo(120))
        self.assertEquals(len(clock.meters), 1)
        meter = clock.meter
        self.assertEquals(meter.length, 4)
        self.assertEquals(meter.division, 4)
        self.assertEquals(meter.number, 1)

    def test_startAfterTicks(self):
        called = []

        instr1 = TestInstrument('f1', self.clock, called)

        n = self.clock.meter.dtt
        nm = self.clock.meter.nm

        self.clock.schedule(instr1).startAfterTicks(0, n(1, 4))
        self._runTicks(96 * 2)

        expected = [(0, 'f1'), (24, 'f1'), (48, 'f1'), (72, 'f1'), (96, 'f1'),
                    (120, 'f1'), (144, 'f1'), (168, 'f1'), (192, 'f1')]
        self.assertEquals(called, expected)

        called[:] = []

        instr2 = TestInstrument('f2', self.clock, called)

        t = self.clock.ticks
        self.clock.schedule(instr2).startAfterTicks(nm(t, 1) - t, n(1, 3))
        self._runTicks(96 * 2)
        expected = [(216, 'f1'), (240, 'f1'), (264, 'f1'), (288, 'f2'),
                    (288, 'f1'), (312, 'f1'), (320, 'f2'), (336, 'f1'),
                    (352, 'f2'), (360, 'f1'), (384, 'f2'), (384, 'f1')]
        self.assertEquals(called, expected)

    def test_startAfter(self):
        called = []

        instr1 = TestInstrument('f1', self.clock, called)

        self.clock.schedule(instr1).startAfter((0, 1), (1, 4))
        self._runTicks(96 * 2)

        expected = [(0, 'f1'), (24, 'f1'), (48, 'f1'), (72, 'f1'), (96, 'f1'),
                    (120, 'f1'), (144, 'f1'), (168, 'f1'), (192, 'f1')]
        self.assertEquals(called, expected)

        called[:] = []

        instr2 = TestInstrument('f2', self.clock, called)

        self.clock.schedule(instr2).startAfter((1, 1), (1, 3))
        self._runTicks(96 * 2)
        expected = [(216, 'f1'), (240, 'f1'), (264, 'f1'), (288, 'f2'),
                    (288, 'f1'), (312, 'f1'), (320, 'f2'), (336, 'f1'),
                    (352, 'f2'), (360, 'f1'), (384, 'f2'), (384, 'f1')]
        self.assertEquals(called, expected)

    def test_stopAfterTicks(self):
        called = []

        instr1 = TestInstrument('f1', self.clock, called)

        nm = self.clock.meter.nextMeasure
        n = self.clock.meter.dtt
        t = self.clock.ticks

        self.clock.schedule(instr1).startAfterTicks(nm(t, 1), n(1, 4)
                ).stopAfterTicks(nm(t, 3) + n(1, 2))
        self._runTicks(96 * 5)
        expected = [
            (96,  'f1'),
            (120, 'f1'),
            (144, 'f1'),
            (168, 'f1'),
            (192, 'f1'),
            (216, 'f1'),
            (240, 'f1'),
            (264, 'f1'),
            (288, 'f1'),
            (312, 'f1')]

        self.assertEquals(len(called), len(expected))
        self.assertEquals(called, expected)

    def test_stopAfter(self):
        called = []

        instr1 = TestInstrument('f1', self.clock, called)

        self.clock.schedule(instr1).startAfter((0, 1), (1, 4)
                ).stopAfter((2, 1))
        self._runTicks(96 * 3)

        expected = [(0, 'f1'), (24, 'f1'), (48, 'f1'), (72, 'f1'), (96, 'f1'),
                    (120, 'f1'), (144, 'f1'), (168, 'f1')]
        self.assertEquals(called, expected)

    def test_setTempo(self):
        self.clock.setTempo(Tempo(60))
        interval_before = 60. / self.clock.tempo.tpm
        called = []
        self.clock.startTicking()
        self.clock.on_stop.addCallback(called.append)
        self.clock.setTempo(Tempo(120))
        self.assertEquals(len(called), 1)
        self.assertEquals(60. / self.clock.tempo.tpm, interval_before / 2.)
        self.clock.task.stop()

    def test_nudge(self):
        self.clock.startTicking()
        self.clock.nudge()
        self.assertEquals(self.clock.reactor.scheduled,
            [(0.1, self.clock.task.start, (60. / self.clock.tempo.tpm, True),
             {})])
        self.clock.task.start(1, True)
        self.clock.nudge(pause=0.5)
        self.assertEquals(self.clock.reactor.scheduled,
            [(0.1, self.clock.task.start, (60. / self.clock.tempo.tpm, True),
             {}),
             (0.5, self.clock.task.start, (60. / self.clock.tempo.tpm, True),
             {})])


class TempoTests(TestCase):

    def test_basic_tempo(self):

        tempo = Tempo()
        self.assertEquals(tempo.bpm, 120)
        self.assertEquals(tempo.tpb, 24)
        self.assertEquals(tempo.tpm, 2880)

        tempo.reset(bpm=150)
        self.assertEquals(tempo.bpm, 150)
        self.assertEquals(tempo.tpb, 24)
        self.assertEquals(tempo.tpm, 3600)

        tempo.reset(tpb=48)
        self.assertEquals(tempo.bpm, 150)
        self.assertEquals(tempo.tpb, 48)
        self.assertEquals(tempo.tpm, 7200)

        tempo.reset(tpb=24, bpm=60)
        self.assertEquals(tempo.bpm, 60)
        self.assertEquals(tempo.tpb, 24)
        self.assertEquals(tempo.tpm, 1440)

        tempo.reset(tpm=14400)
        self.assertEquals(tempo.bpm, 600)
        self.assertEquals(tempo.tpb, 24)
        self.assertEquals(tempo.tpm, 14400)


class NewStyleMeterTests(TestCase):

    def test_divisionToTicks(self):

        tempo = Tempo()
        meter = Meter(4, 4, tempo=tempo)
        self.assertEquals(meter.divisionToTicks(1, 4), 24)
        self.assertEquals(meter.divisionToTicks(3, 4), 72)
        self.assertEquals(meter.divisionToTicks(1, 1), 96)
        self.assertEquals(meter.divisionToTicks(8, 4), 192)
        self.assertEquals(meter.divisionToTicks(1, 12), 8)

        tempo = Tempo(bpm=120, tpb=96)
        meter = Meter(4, 4, tempo=tempo)
        self.assertEquals(meter.divisionToTicks(1, 4), 96)
        self.assertEquals(meter.divisionToTicks(3, 4), 96 * 3)
        self.assertEquals(meter.divisionToTicks(1, 1), 96 * 4)
        self.assertEquals(meter.divisionToTicks(8, 4), 96 * 8)
        self.assertEquals(meter.divisionToTicks(1, 12), 32)
        self.assertEquals(meter.divisionToTicks(1, 48), 8)
        self.assertEquals(meter.divisionToTicks(1, 128), 3)
        self.assertEquals(meter.divisionToTicks(1, 192), 2)

    def test_divitionToTicksNonStandardMeasure(self):
        tempo = Tempo()
        meter = Meter(3, 4, tempo=tempo)
        self.assertEquals(meter.divisionToTicks(1, 4), 24)
        meter = Meter(7, 8, tempo=tempo)
        self.assertEquals(meter.divisionToTicks(1, 4), 24)

    def test_invalidDivisionToTicks(self):
        tempo = Tempo()
        meter = Meter(4, 4, tempo=tempo)
        self.assertRaises(ValueError, meter.dtt, 1, 192)
        self.assertRaises(ValueError, meter.dtt, 1, 25)
        self.assertRaises(ValueError, meter.dtt, 1, 7)
        tempo.reset(tpb=192)
        meter.resetTempo(tempo)
        meter.dtt(1, 192)
        tempo.reset(tpb=25)
        meter.resetTempo(tempo)
        meter.dtt(1, 25)
        tempo.reset(tpb=24 * 7)
        meter.resetTempo(tempo)
        meter.dtt(1, 7)
        meter.strict = False
        tempo.reset(tpb=24)
        meter.resetTempo(tempo)
        meter.dtt(1, 192)
        meter.dtt(1, 25)
        meter.dtt(1, 7)
        errors = self.flushLoggedErrors()
        self.assertEquals(len(errors), 3)

    def test_nextDivision(self):
        ticks = 0
        tempo = Tempo()
        meter = Meter(4, 4, tempo=tempo)
        self.assertEquals(meter.nextDivision(ticks, 1, 4), 24)
        self.assertEquals(meter.nextDivision(ticks, 2, 4), 48)
        self.assertEquals(meter.nextDivision(ticks, 1, 1), 96)
        self.assertEquals(meter.nextDivision(ticks, 5, 4), 96 + 24)
        ticks = 48
        self.assertEquals(meter.nextDivision(ticks, 1, 4), 96 + 24)
        self.assertEquals(meter.nextDivision(ticks, 2, 4), 48)
        self.assertEquals(meter.nextDivision(ticks, 1, 1), 96)
        self.assertEquals(meter.nextDivision(ticks, 5, 4), 96 + 24)
        ticks = 96 + 48
        self.assertEquals(meter.nextDivision(ticks, 1, 4), (96 * 2) + 24)
        self.assertEquals(meter.nextDivision(ticks, 2, 4), 96 + 48)
        self.assertEquals(meter.nextDivision(ticks, 1, 1), 96 * 2)
        self.assertEquals(meter.nextDivision(ticks, 5, 4), (96 * 2) + 24)

        ticks = 0
        tempo = Tempo(tpb=48)
        meter = Meter(4, 4, tempo=tempo)
        self.assertEquals(meter.nextDivision(ticks, 1, 4), 48)
        self.assertEquals(meter.nextDivision(ticks, 2, 4), 96)
        self.assertEquals(meter.nextDivision(ticks, 1, 1), 192)
        self.assertEquals(meter.nextDivision(ticks, 5, 4), 240)
        ticks = 96
        self.assertEquals(meter.nextDivision(ticks, 1, 4), 240)
        self.assertEquals(meter.nextDivision(ticks, 2, 4), 96)
        self.assertEquals(meter.nextDivision(ticks, 1, 1), 192)
        self.assertEquals(meter.nextDivision(ticks, 5, 4), 240)
        ticks = 192 + 96
        self.assertEquals(meter.nextDivision(ticks, 1, 4), (192 * 2) + 48)
        self.assertEquals(meter.nextDivision(ticks, 2, 4), 192 + 96)
        self.assertEquals(meter.nextDivision(ticks, 1, 1), 192 * 2)
        self.assertEquals(meter.nextDivision(ticks, 5, 4), (192 * 2) + 48)
