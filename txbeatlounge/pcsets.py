

__all__ = [ 'PitchClassSet' ]

class PitchClassSet:

    def __init__(self, notes):
        notes = [ n % 12 for n in notes ]
        notes = set(notes)
        self.notes = notes

    def __repr__(self):
        return 'PitchClassSet(%r)' % list(sorted(self.notes))



