from twisted.trial.unittest import TestCase

from txbeatlounge.notes import *

class InversionTests(TestCase):

    def test_zerothInversion(self):
        self.assertEquals(invert(Cmaj[0], 0), Cmaj[0])

    def test_firstInversion(self):        
        inv = invert(Cmaj[0])
        self.assertEquals(inv, [C[1], E[0], G[0]])
        inv = invert(Cmaj7[0])
        self.assertEquals(inv, [C[1], E[0], G[0], B[0]])
        inv = invert(Cmaj9[0])
        self.assertEquals(inv, [C[1], E[0], G[0], B[0], D[1]])
        
    def test_secondInversion(self):
        inv = invert(Cmaj[0], 2)
        self.assertEquals(inv, [C[1], E[1], G[0]])
        inv = invert(Cmaj7[0], 2)
        self.assertEquals(inv, [C[1], E[1], G[0], B[0]])
        inv = invert(Cmaj9[0], 2)
        self.assertEquals(inv, [C[1], E[1], G[0], B[0], D[1]])

    def test_thirdInversion(self):
        inv = invert(Cmaj[0], 3)
        self.assertEquals(inv, [C[1], E[1], G[1]])
        inv = invert(Cmaj7[0], 3)
        self.assertEquals(inv, [C[1], E[1], G[1], B[0]])
        inv = invert(Cmaj9[0], 3)
        self.assertEquals(inv, [C[1], E[1], G[1], B[0], D[1]])

    def test_fourthInversion(self):
        inv = invert(Cmaj[0], 4)
        self.assertEquals(inv, [C[1], E[1], G[1]])
        inv = invert(Cmaj9[0], 4)
        self.assertEquals(inv, [C[1], E[1], G[1], B[1], D[1]])

    def test_bogusInversions(self):
        self.assertRaises(ValueError, invert, Cmaj[0], -1)
        self.assertRaises(ValueError, invert, Cmaj[0], 5)

