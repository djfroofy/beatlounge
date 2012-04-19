import random

from twisted.trial.unittest import TestCase

from bl.ugen import (N, R, Random, RandomPhrase, RP, RandomWalk, RW, Weight, W,
                     C, Cycle, O, Oscillate)


class UGensTestCase(TestCase):

    def setUp(self):
        random.seed(0)

    def test_N(self):
        self.assertEqual(N(), None)
        self.failIf(N)
        self.failIf(bool(N))
        self.assertEqual(repr(N), 'N')
        self.assertEqual(str(N), 'N')

    def test_Cycle(self):
        self.assertIdentical(C, Cycle)
        c = C(1, 2, 3, 4, 5)
        results = [c() for i in range(10)]
        self.assertEqual(results, [1, 2, 3, 4, 5, 1, 2, 3, 4, 5])

    def test_Oscillate(self):
        self.assertIdentical(O, Oscillate)
        o = O(1, 2, 3, 4, 5)
        results = [o() for i in range(10)]
        self.assertEqual(results, [1, 2, 3, 4, 5, 4, 3, 2, 1, 2])

    def test_Random(self):
        self.assertIdentical(R, Random)
        r = R(1, 2, 3, 4, 5)
        results = [r() for i in range(10)]
        self.assertEqual(results, [5, 4, 3, 2, 3, 3, 4, 2, 3, 3])

    def test_RandomPhrase(self):
        self.assertIdentical(RP, RandomPhrase)
        p = RP([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        results = [p() for i in range(15)]
        self.assertEqual(results, [7, 8, 9, 7, 8, 9, 4, 5, 6, 1,
                                   2, 3, 4, 5, 6])
        self.assertRaises(ValueError, RP, [[1, 2], [1, 2, 3]], 2)
        p = RP([[1, 2, 3], [4, 5, 6], [7, 8, 9]], 3)
        results = [p() for i in range(15)]
        self.assertEqual(results, [4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 4, 5,
                                   6])

    def test_RandomWalk(self):
        self.assertIdentical(RW, RandomWalk)
        walk = RW([1, 2, 3, 4, 5, 6, 7, 8, 9])
        results = [walk() for i in range(100)]
        self.assertEqual(results, [
            8, 7, 6, 5, 6, 7, 6, 5, 4, 5, 4, 5, 6, 5, 6, 7, 6, 7, 6, 7, 8, 7,
            8, 7, 6, 5, 4, 5, 4, 5, 6, 5, 4, 5, 4, 3, 4, 5, 4, 5, 6, 7, 6, 5,
            4, 5, 6, 5, 4, 5, 4, 3, 2, 1, 2, 1, 2, 1, 2, 3, 2, 3, 2, 3, 2, 3,
            2, 3, 4, 3, 2, 3, 4, 5, 6, 5, 6, 7, 8, 7, 8, 7, 8, 7, 8, 7, 6, 7,
            8, 7, 8, 7, 8, 7, 8, 9, 8, 9, 8, 9])
        walk = RW([1, 2, 3, 4, 5, 6, 7, 8, 9], startIndex=5)
        results = [walk() for i in range(100)]
        self.assertEqual(results, [
            6, 5, 6, 7, 6, 5, 6, 5, 4, 5, 6, 7, 6, 5, 6, 7, 8, 7, 6, 7, 6, 7,
            6, 5, 6, 5, 6, 7, 8, 7, 6, 5, 6, 7, 8, 9, 8, 9, 8, 9, 8, 7, 6, 5,
            4, 3, 4, 5, 6, 5, 4, 3, 4, 5, 6, 5, 6, 5, 4, 5, 4, 3, 4, 3, 2, 1,
            2, 1, 2, 3, 4, 5, 6, 5, 6, 7, 8, 7, 6, 7, 8, 7, 6, 5, 4, 3, 4, 5,
            6, 7, 6, 7, 6, 7, 8, 9, 8, 9, 8, 7])

    def test_Weight(self):
        self.assertIdentical(W, Weight)
        a = W((60, 10), (64, 1), (67, 2), (69, 1))
        results = [a() for i in range(15)]
        self.assertEqual(results, [60, 60, 60, 60, 67, 60, 60, 67, 60, 60, 69,
                                   64, 60, 64, 60])
