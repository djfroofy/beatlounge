from twisted.trial.unittest import TestCase

from bl.scheduler import Meter, Tempo, BeatClock
from bl.rudiments import FiveStrokeRoll, SixStrokeRoll, scaleRudiment
from bl.rudiments import RudimentSchedulePlayer
from bl.testlib import TestInstrument, TestReactor, ClockRunner


class RudimentsTest(TestCase):

    def test_fiveStrokeRoll(self):

        fsr = FiveStrokeRoll()
        l = list(fsr.time())
        self.assertEquals(l, [0, 6, 12, 18, 24,  48, 54, 60, 66, 72])

        ct = 20
        l = []
        for tick in fsr.time(cycle=True):
            l.append(tick)
            ct -= 1
            if not ct:
                break
        self.assertEquals(l, [0, 6, 12, 18, 24,  48, 54, 60, 66, 72,
                              96, 102, 108, 114, 120,  144, 150, 156,
                              162, 168])

        l = list(fsr.strokes(25, 26))
        self.assertEquals(l, [25, 25, 26, 26, 25, 26, 26, 25, 25, 26])

        v = list(fsr.velocity())
        self.assertEquals(v, [90, 70, 80, 67, 120, 90, 76, 89, 70, 127])

    def test_sixStrokeRoll(self):

        ssr = SixStrokeRoll()
        l = list(ssr.time())
        self.assertEquals(l, [0, 12, 18, 24, 30, 36, 48, 60, 66, 72, 78, 84])

        ct = 36
        l = []
        for tick in ssr.time(cycle=True):
            l.append(tick)
            ct -= 1
            if not ct:
                break

        self.assertEquals(l, [0, 12, 18, 24, 30, 36, 48, 60, 66, 72, 78, 84,
                              96, 108, 114, 120, 126, 132, 144, 156, 162, 168,
                              174, 180, 192, 204, 210, 216, 222, 228, 240, 252,
                              258, 264, 270, 276])

        l = list(ssr.strokes(12, 14))
        self.assertEquals(l, [14, 12, 12, 14, 14, 12, 14, 12, 12, 14, 14, 12])

        v = list(ssr.velocity())
        self.assertEquals(v, [120, 90, 70, 80, 67, 120, 123, 90, 76, 89, 70,
                              127])

    def test_scaleRudiment(self):
        ScaledSixStrokeRoll = scaleRudiment(SixStrokeRoll, 48)
        self.assertEqual(ScaledSixStrokeRoll.defaultDivisionLength, 12)
        self.assertEqual(ScaledSixStrokeRoll.__name__, 'SixStrokeRoll_TPB48')
        ssr = ScaledSixStrokeRoll()
        l = list(ssr.time())
        self.assertEquals(l, [0, 24, 36, 48, 60, 72, 96, 120, 132, 144,
                              156, 168])
        # check the caching
        cached = scaleRudiment(SixStrokeRoll, 48)
        self.assertIdentical(cached, ScaledSixStrokeRoll)
        ScaledFiveStrokRoll = scaleRudiment(FiveStrokeRoll, 48)
        self.failIfIdentical(ScaledFiveStrokRoll, ScaledSixStrokeRoll)


class RudimentsSchedulePlayerTests(TestCase, ClockRunner):

    def setUp(self):
        tempo = Tempo(135)
        self.meter = Meter(4, 4, tempo=tempo)
        self.clock = BeatClock(tempo, meter=self.meter, reactor=TestReactor())
        self.instr = TestInstrument(self.clock)

    def test_rudiment_schedule_player(self):
        rudiment = FiveStrokeRoll()
        player = RudimentSchedulePlayer(self.instr, rudiment, 60, 63,
                                        clock=self.clock)
        player.resumePlaying()
        self.runTicks(96 * 2 - 1)
        expected = [
                ('note', 0, 60, 90),
                ('note', 6, 60, 70),
                ('note', 12, 63, 80),
                ('note', 18, 63, 67),
                ('note', 24, 60, 120),
                ('note', 48, 63, 90),
                ('note', 54, 63, 76),
                ('note', 60, 60, 89),
                ('note', 66, 60, 70),
                ('note', 72, 63, 127),
                ('note', 96, 60, 90),
                ('note', 102, 60, 70),
                ('note', 108, 63, 80),
                ('note', 114, 63, 67),
                ('note', 120, 60, 120),
                ('note', 144, 63, 90),
                ('note', 150, 63, 76),
                ('note', 156, 60, 89),
                ('note', 162, 60, 70),
                ('note', 168, 63, 127)]
        self.assertEquals(self.instr.plays, expected)

    def test_changeStrokes(self):
        rudiment = FiveStrokeRoll()
        player = RudimentSchedulePlayer(self.instr, rudiment, 60, 63,
                                        clock=self.clock)
        player.changeStrokes(45, 49)
        player.resumePlaying()
        self.runTicks(96 * 2 - 1)
        expected = [
                ('note', 0, 45, 90),
                ('note', 6, 45, 70),
                ('note', 12, 49, 80),
                ('note', 18, 49, 67),
                ('note', 24, 45, 120),
                ('note', 48, 49, 90),
                ('note', 54, 49, 76),
                ('note', 60, 45, 89),
                ('note', 66, 45, 70),
                ('note', 72, 49, 127),
                ('note', 96, 45, 90),
                ('note', 102, 45, 70),
                ('note', 108, 49, 80),
                ('note', 114, 49, 67),
                ('note', 120, 45, 120),
                ('note', 144, 49, 90),
                ('note', 150, 49, 76),
                ('note', 156, 45, 89),
                ('note', 162, 45, 70),
                ('note', 168, 49, 127)]
        self.assertEquals(self.instr.plays, expected)
