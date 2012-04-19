from twisted.trial.unittest import TestCase

from bl.ugen import N
from bl.nostalgia.bcut import explode, cut


class BcutTestCase(TestCase):

    def test_explode(self):
        s = [1, 2, 3, 4]
        exploded = explode(s)
        self.assertEquals(exploded, [1, N, 2, N, 3, N, 4, N])
        exploded = explode(s, 4)
        self.assertEquals(exploded, [1, N, N, N, 2, N, N, N, 3, N, N, N, 4, N,
                                     N, N])
        s = [1, N, 2, N, N, 3, 4, N]
        exploded = explode(s)
        self.assertEquals(exploded, [1, N, N, N, 2, N, N, N, N, N, 3, N, 4, N,
                                     N, N])
        exploded = explode(s, 4)
        self.assertEquals(exploded, [1, N, N, N, N, N, N, N, 2, N, N, N, N, N,
                                     N, N, N, N, N, N, 3, N, N, N, 4, N, N, N,
                                     N, N, N, N])

    def test_cut(self):
        s = explode([1, N, 2, N, N, 3, 4, N], 4)
        for i in range(512):
            chopped = cut(s)
            self.assertEquals(len(chopped), 32)
