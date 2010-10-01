
from twisted.trial.unittest import TestCase

from txbeatlounge.testing import FakeClock, TestReactor
from txbeatlounge.effects import FadeIn, FadeOut, FadeInOut
from txbeatlounge.scheduler import Scheduler

class FadeTests(TestCase):

    def setUp(self):
        super(FadeTests, self).setUp()
        self.clock = FakeClock()
        self.schedule = Scheduler(self.clock,
                                  reactor=TestReactor()).schedule

    def test_fadein(self):
        fadein = FadeIn(min=0, max=40)
        self.schedule(fadein).start(1, False)
        velocities = []
        self.schedule(lambda : velocities.append(fadein.current)).start(1, False)
        self.clock.tickUntil(127)
        self.assertEquals(velocities, range(1, 41) + [40] * 87)
    

    def test_fadeout(self):
        fadeout = FadeOut(min=0, max=40)
        self.schedule(fadeout).start(1, False)
        velocities = []
        self.schedule(lambda : velocities.append(fadeout.current)).start(1, False)
        self.clock.tickUntil(127)
        self.assertEquals(velocities, range(39, -1, -1) + [0] * 87)


    def test_fadeinout(self):
        called = [ False ]
        def outro():
            called[0] = True
        fadeinout = FadeInOut(min=0, max=40, outro=outro, hold_for_iterations=10)
        self.schedule(fadeinout).start(1, False) 
        velocities = []
        self.schedule(lambda : velocities.append(fadeinout.current)).start(1, False)
        self.clock.tickUntil(127)
        self.assertEquals(velocities, range(1, 40) + [40] * 10 + range(39,-1,-1) + [0] * 38)
        self.assert_(called[0])


