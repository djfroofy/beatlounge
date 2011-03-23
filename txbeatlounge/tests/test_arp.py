from itertools import cycle

from twisted.trial.unittest import TestCase

from txbeatlounge import arp
from txbeatlounge.arp import AscArp, DescArp, OrderedArp, RandomArp

class ArpTests(TestCase):


    def setUp(self):
        self.notes = notes = [ 0, 2, 1, 3 ]
        self.ascArp = AscArp(notes)
        self.descArp = DescArp(notes)
        self.ordArp = OrderedArp(notes)
        self.randArp = RandomArp(notes)

    def test_ascArp(self):
        notes = []
        for i in range(8):
            notes.append(self.ascArp())
        self.assertEquals(notes, [0,1,2,3,0,1,2,3])

    def test_descArp(self):
        notes = []
        for i in range(8):
            notes.append(self.descArp())
        self.assertEquals(notes, [3,2,1,0,3,2,1,0])

    def test_orderedArp(self):
        notes = []
        for i in range(8):
            notes.append(self.ordArp())
        self.assertEquals(notes, [0,2,1,3,0,2,1,3])
        
    def test_randomArp(self):
        r = cycle([1, 2, 0, 0, 2, 0, 1, 0])
        class random:
            @classmethod
            def randint(cls, *blah):
                return r.next()
        self.patch(arp, 'random', random)

        notes = []
        for i in range(8):
            notes.append(self.randArp())
        self.assertEquals(notes, [2, 3, 0, 1, 0, 2, 1, 3])


    def test_resetting(self):

        notes = []
        for i in range(2):
            notes.append(self.ascArp())
        self.ascArp.reset([5,6,7,8])   
        for i in range(2):
            notes.append(self.ascArp())
        self.assertEquals(notes, [0,1,7,8])

        notes = []
        self.ascArp.reset([0,1,2,3])
        for i in range(3):
            notes.append(self.ascArp())
        self.ascArp.reset([5,6])   
        notes.append(self.ascArp())
        self.assertEquals(notes, [0,1,2,6]) 

        notes = []
        self.ascArp.reset([0,1,2,3])
        for i in range(3):
            notes.append(self.ascArp())
        self.ascArp.reset([4,5,6,7,8,9,10,11])   
        notes.append(self.ascArp())
        self.assertEquals(notes, [0,1,2,10])

        notes = []
        for i in range(2):
            notes.append(self.descArp())
        self.descArp.reset([5,6,7,8])   
        for i in range(2):
            notes.append(self.descArp())
        self.assertEquals(notes, [3,2,6,5])

        notes = []
        self.descArp.reset([0,1,2,3])
        for i in range(3):
            notes.append(self.descArp())
        self.descArp.reset([5,6])   
        notes.append(self.descArp())
        self.assertEquals(notes, [3,2,1,5]) 

        notes = []
        self.descArp.reset([0,1,2,3])
        for i in range(3):
            notes.append(self.descArp())
        self.descArp.reset([4,5,6,7,8,9,10,11])   
        notes.append(self.descArp())
        self.assertEquals(notes, [3,2,1,5])
        




