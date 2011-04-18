

__all__ = [ 'PitchClassSet' ]

class PitchClassSet:

    def __init__(self, notes):
        notes = [ n % 12 for n in notes ]
        notes = set(notes)
        self.notes = notes

    def __repr__(self):
        return 'PitchClassSet(%r)' % list(sorted(self.notes))

    def transpose(self, amount):
        return PitchClassSet([ n + amount for n in self.notes ])

    def invert(self, amount):
        return PitchClassSet([12-n for n in self.notes])

    def octave(self, octave=0):
        return [ n + 12 * octave for n in self.notes ]

