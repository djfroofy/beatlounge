from itertools import cycle

from twisted.trial.unittest import TestCase

from bl import filters
from bl.scheduler import Meter, BeatClock, Tempo
from bl.player import callMemo
from bl.testlib import TestReactor
from bl.tests import data

Sustainer = filters.Sustainer
PassThru = filters.PassThru
FadeIn = filters.FadeIn
FadeOut = filters.FadeOut
Chain = filters.Chain
StandardDucker = filters.StandardDucker
Sinusoid = filters.Sinusoid
Sawtooth = filters.Sawtooth
Triangle = filters.Triangle
WeightNote = filters.WeightNote

class FiltersTests(TestCase):

    def setUp(self):
        self.clock = BeatClock(Tempo(135), reactor=TestReactor())
        self.sustainer = Sustainer(120)
        self.passthru = PassThru()
        self.ducker = StandardDucker(10, clock=self.clock)
        self.fadein = FadeIn(20, 30, step=5, tickrate=10, clock=self.clock)
        self.fadeout = FadeOut(30, 20, step=5, tickrate=10, clock=self.clock)
        self.chain = Chain(Sustainer(100), StandardDucker(20, clock=self.clock))
        self.sinusoid = Sinusoid(20, 50, 0, 50, clock=self.clock)
        self.sawtooth = Sawtooth(20, 20, 50, clock=self.clock)
        self.triangle = Triangle(30, 20, 70, clock=self.clock)

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


    def test_fadein(self):
        self.clock.ticks = 0

        for i in range(10):
            velocity, original = self.fadein.filter(127)
            self.assertEquals(velocity, 20)
            self.assertEquals(original, 30)
            self.clock.ticks += 1

        for tick in range(10):
            velocity, original = self.fadein.filter(127)
            self.assertEquals(velocity, 25)
            self.assertEquals(original, 30)
            self.clock.ticks += 1

        for tick in range(11):
            velocity, original = self.fadein.filter(127)
            self.assertEquals(velocity, 30)
            self.assertEquals(original, 30)
            self.clock.ticks += 1

    def test_fadeout(self):
        self.clock.ticks = 0

        for i in range(10):
            velocity, original = self.fadeout.filter(127)
            self.assertEquals(velocity, 30)
            self.assertEquals(original, 30)
            self.clock.ticks += 1

        for tick in range(10):
            velocity, original = self.fadeout.filter(127)
            self.assertEquals(velocity, 25)
            self.assertEquals(original, 30)
            self.clock.ticks += 1

        for tick in range(11):
            velocity, original = self.fadeout.filter(127)
            self.assertEquals(velocity, 20)
            self.assertEquals(original, 30)
            self.clock.ticks += 1

    def test_sinusoid(self):

        velocities = []

        for i in range(100):
            velocity, original = self.sinusoid.filter(127)
            velocities.append(velocity)
            self.assertEquals(original, 127)
            self.clock.ticks += 1

        self.assertEquals(velocities, data.sinusoid_velocities)

    def test_sawtooth(self):

        velocities = []

        for i in range(40):
            velocity, original = self.sawtooth.filter(127)
            velocities.append(velocity)
            self.assertEquals(original, 127)
            self.clock.ticks += 1

        self.assertEquals(velocities, data.sawtooth_velocities)

    def test_triangle(self):

        velocities = []

        for i in range(40):
            velocity, original = self.triangle.filter(127)
            velocities.append(velocity)
            self.assertEquals(original, 127)
            self.clock.ticks += 1

        self.assertEquals(velocities, data.triangle_velocities)

    def test_weightNote(self):
        c = cycle([60,63,67,71])
        notes = callMemo(c.next)
        noteWeights = { 60: 127, 63: 95, 67: 80 }
        wn = WeightNote(notes, noteWeights)
        notes()
        v = wn(100)
        self.assertEquals(v, (127, 100))
        notes()
        v = wn(100)
        self.assertEquals(v, (95, 100))
        notes()
        v = wn(100)
        self.assertEquals(v, (80, 100))
        notes()
        v = wn(100)
        self.assertEquals(v, (100, 100))
        notes()
        v = wn(60, 120)
        self.assertEquals(v, (63, 120))

