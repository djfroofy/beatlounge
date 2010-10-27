
from twisted.trial.unittest import TestCase

from txbeatlounge import filters
from txbeatlounge.scheduler2 import Meter, BeatClock
from txbeatlounge.testlib import TestReactor

Sustainer = filters.Sustainer
PassThru = filters.PassThru
FadeIn = filters.FadeIn
Chain = filters.Chain
StandardDucker = filters.StandardDucker


class FiltersTests(TestCase):

    def setUp(self):
        self.clock = BeatClock(135, reactor=TestReactor())
        self.sustainer = Sustainer(120)
        self.passthru = PassThru()
        self.ducker = StandardDucker(10, clock=self.clock)
        self.chain = Chain(Sustainer(100), StandardDucker(20, clock=self.clock))

    def test_sustainer(self):
        velocity, original = self.sustainer.filter(127, 127)
        self.assertEquals(velocity, 120)
        self.assertEquals(original, 127)

    def test_ducker(self):
        
        for tick in (0,24,48,72):
            self.clock.ticks = tick
            velocity, original = self.ducker.filter(127, 127)
            self.assertEquals(velocity, 127)
            self.assertEquals(original, 127)

        adjust = 100. / 110

        for tick in range(1,24) + range(25, 48) + range(49, 72):
            self.clock.ticks = tick
            velocity, original = self.ducker.filter(127, 127)
            self.assertEquals(velocity, 117)
            self.assertEquals(original, 127)
            velocity, original = self.ducker.filter(100, 110)
            self.assertEquals(velocity, int(100 - (adjust * 10)))
            self.assertEquals(original, 110)


    def test_chain(self):
        
        for tick in (0,24,48,72):
            self.clock.ticks = tick
            velocity, original = self.chain.filter(127)
            self.assertEquals(velocity, 100)
            self.assertEquals(original, 100)


        for tick in range(1,24) + range(25, 48) + range(49, 72):
            self.clock.ticks = tick
            velocity, original = self.chain.filter(127)
            self.assertEquals(velocity, 80)
            self.assertEquals(original, 100)

    def test_passthru(self):

        velocity, original = self.passthru.filter(60, 70)
        self.assertEquals(velocity, 60)
        self.assertEquals(original, 70)
    

