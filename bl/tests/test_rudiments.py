from pprint import pprint
from itertools import cycle

from twisted.trial.unittest import TestCase


from bl.rudiments import *


class RudimentsTest(TestCase):

    def test_fiveStrokeRoll(self):

        fsr = FiveStrokeRoll()
        l = list(fsr.time(8))
        self.assertEquals(l, [0, 8, 16, 24, 32, 48, 56, 64, 72, 80])

        ct = 20
        l = []
        for tick in fsr.time(8, cycle=True):
            l.append(tick)
            ct -= 1
            if not ct:
                break
        self.assertEquals(l, [0, 8, 16, 24, 32, 48, 56, 64, 72, 80,
                              96, 104, 112, 120, 128, 144, 152, 160, 168, 176])


        l = list(fsr.strokes(25, 26))
        self.assertEquals(l, [25, 25, 26, 26, 25, 26, 26, 25, 25, 26])


        v = list(fsr.velocity())
        self.assertEquals(v, [90,70,80,67,120, 90,76,89,70,127])

    def test_sixStrokeRoll(self):

        ssr = SixStrokeRoll()
        l = list(ssr.time(6))
        self.assertEquals(l, [0, 12, 18, 24, 30, 36, 48, 60, 66, 72, 78, 84])

        ct = 36
        l = []
        for tick in ssr.time(6, cycle=True):
            l.append(tick)
            ct -= 1
            if not ct:
                break

        self.assertEquals(l, [0, 12, 18, 24, 30, 36, 48, 60, 66, 72, 78, 84,
                              96, 108, 114, 120, 126, 132, 144, 156, 162, 168, 174, 180,
                              192, 204, 210, 216, 222, 228, 240, 252, 258, 264, 270, 276])

        l = list(ssr.strokes(12,14))
        self.assertEquals(l, [14, 12, 12, 14, 14, 12, 14, 12, 12, 14, 14, 12])

        v = list(ssr.velocity())
        self.assertEquals(v, [120,90,70,80,67,120, 123,90,76,89,70,127])

    def test_chainRudiments(self):

        fsr = FiveStrokeRoll()
        ssr = SixStrokeRoll()


        def rudimentFactory():
            for rud, hands in zip((fsr,fsr,ssr,ssr,fsr),
                                  ([0,1],[2,3],[0,1],[2,3],[4,5])):
                yield rud, hands
        ticksFactory = cycle([8,8,4,8,4]).next

        played = []
        for tup in chainRudiments(rudimentFactory().next, ticksFactory):
            played.append(tup)

        pprint(played)








