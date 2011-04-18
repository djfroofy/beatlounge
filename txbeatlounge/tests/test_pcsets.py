from twisted.trial.unittest import TestCase

from txbeatlounge.pcsets import PitchClassSet

class PitchClassSetTests(TestCase):

    def setUp(self):
        self.pcs = PitchClassSet([67,48,64,60])

    def test_set_construction(self):
        self.assertEquals(self.pcs.notes, set([0,4,7]))

    def test_repr(self):
        self.assertEquals(repr(self.pcs), 'PitchClassSet([0, 4, 7])')

    def test_transpose(self):
        pcs3 = self.pcs.transpose(3)
        self.assertEquals(pcs3.notes, set([3,7,10]))
        pcs6 = self.pcs.transpose(6)
        self.assertEquals(pcs6.notes, set([1,6,10]))

    def test_invert(self):
        pcs_inv3 = self.pcs.invert(3)
        self.assertEquals(pcs_inv3.notes, set([0,5,8]))

    def test_ocatve(self):
        octave = self.pcs.octave()
        self.assertEquals(octave, [0,4,7])
        octave1 = self.pcs.octave(1)
        self.assertEquals(octave1, [12,16,19])

