from twisted.trial.unittest import TestCase

from txbeatlounge.pcsets import PitchClassSet

class PitchClassSetTests(TestCase):

    def setUp(self):
        self.pcs = PitchClassSet([67,48,64,60])

    def test_set_construction(self):
        self.assertEquals(self.pcs.notes, set([0,4,7]))

    def test_repr(self):
        self.assertEquals(repr(self.pcs), 'PitchClassSet([0, 4, 7])')


