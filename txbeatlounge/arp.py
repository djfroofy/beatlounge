# Arpegiattors

import random

from zope.interface import Interface, Attribute, implements

from txbeatlounge.utils import getClock 


__all__ = [ 'IArp', 'AscArp', 'DescArp', 'OrderedArp', 'ArpSwitcher',
            'OctaveArp', 'RandomArp']


class IArp(Interface):
    """
    An interface for arpeggiators.
    """

    values =  Attribute("Values to arpeggiate")
    
    def reset(values):
        """
        Reset `values` to the given list.
        """

    def __call__():
        """
        Get the next value in the arpeggiation.
        """
    

class BaseArp(object):
    implements(IArp)

    values = ()

    def __init__(self, values=()):
        self.reset(values)


    def reset(self, values):
        self.values = values


    def __call__(self):
        raise NotImplentedError


def sortNumeric(values, sort=None):
    if sort is None:
        sort = lambda l : list(sorted(l))
    numbers = [ v for v in values if type(v) in (int, float, list, tuple) ]
    numbers = sort(numbers)
    newvalues = []
    for v in values:
        if type(v) in (int, float):
            newvalues.append(numbers.pop(0))
        else:
            newvalues.append(v)
    return newvalues


class IndexedArp(BaseArp):
    index = 0
    count = 0
    direction = 1

    def sort(self, values):
        raise NotImplementedError

    def reset(self, values):
        values = self.sort(values)
        self.count = len(values)
        if self.values:
            factor = len(values) / float(len(self.values))
            if factor != 1:
                self.index = int(self.index * factor)
                self.index = self.index % self.count
        self.values = values

    def __call__(self):
        v = self.values[self.index]
        self.index += self.direction
        self.index = self.index % self.count
        return v

class AscArp(IndexedArp):
   
    def sort(self, values):
        return sortNumeric(values)

class DescArp(IndexedArp):

    def sort(self, values):
        return sortNumeric(values, lambda l : list(reversed(sorted(l))))

class OrderedArp(IndexedArp):

    def sort(self, values):
        return values


def RevOrderedArp(values=()):
    arp = OrderedArp(values)
    arp.direction = -1
    arp.index = len(values) - 1
    return arp


def exhaustCall(v):
    while callable(v):
        v = v()
    return v

class RandomArp(BaseArp):

    def reset(self, values):
        self._current = list(values)
        self._next = []
        self.count = len(values)
        self.values = values

    def __call__(self):
        if not self._current:
            self._current = self._next
        if not self._current:
            return
        l = len(self._current)
        index = random.randint(0, l-1)
        next = self._current.pop(index)
        self._next.append(next)
        return next

class ArpSwitcher(BaseArp):

    def __init__(self, arp, values):
        self.arp = arp
        self.arp.reset(values)
        self.values = values
        self.count = len(self.values)
    
    def reset(self, values):
        self.values = values
        self.arp.reset(values)
        self.count = len(values)

    def switch(self, arp):
        arp.reset(self.values)
        self.arp = arp

    def __call__(self):
        return self.arp()



class OctaveArp(ArpSwitcher):

    def __init__(self, arp, values, octaves=3, direction=1, oscillate=False):
        ArpSwitcher.__init__(self, arp, values)
        self.octaves = octaves
        self.currentOctave = 0
        self.index = 0
        if direction == -1:
            self.currentOctave = -1
        self.direction = direction
        self.oscillate = oscillate


    def __call__(self):
        v = exhaustCall(self.arp())
        self.index += 1
        self.index = self.index % self.count
        if self.index == 0:
            self.currentOctave += self.direction
            if self.octaves:
                self.currentOctave = self.currentOctave % (self.octaves + 1)
                if self.oscillate and self.currentOctave == 0:
                    self.direction *= -1
            else:
                self.currentOctave = 0
        if v is None:
            return
        return v + (self.currentOctave * 12)



