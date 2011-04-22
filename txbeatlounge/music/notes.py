
from txbeatlounge.utils import minmax
from txbeatlounge.music.constants import twelve_tone_equal_440
from txbeatlounge.music.freq import offsets


__all__ = [
    'MidiNote', 'C', 'Cs', 'Df', 'D', 'Ds', 'Ef', 'E', 'F', 'Fs', 'Gf', 'G', 'Gs', 'Af', 'A', 'As', 'Bf', 'B',
    'keys', 'keys_rev',
]

class MidiNote(object):
    """
    int is an immutable value type and whatnot.  so, this is some kind of frowned upon idea, subclassing int.
    <strike>However, these MidiNotes are immutable value types, so let's try.</strike>

    Acts like an integer with some util methods to get frequency, related notes,
    compare if another note is in the same octave.
    """

    def __init__(self, value=0):
        if not 0 <= value < 128:
            raise ValueError("Value must be between 0 and 127 inclusive")
        self.value = int(value)

    def __repr__(self):
        return "MidiNote(%s)" % self.value

    def __str__(self):
        return repr(self)

    def __hash__(self):
        return hash(self.value)


    # INTEGER, it is.

    def __int__(self):
        return self.value

    def __add__(self, other):
        return self.__class__(int(other)+int(self))

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        return self.__class__(int(self)-int(other))

    def __rsub__(self, other):
        return MidiNote(int(other) - int(self))

    def __lt__(self, other):
        return int(self) < int(other)

    def __le__(self, other):
        return int(self) <= int(other)

    def __eq__(self, other):
        return int(self) == int(other)

    def __ne__(self, other):
        return int(self) != int(other)

    def __gt__(self, other):
        return int(self) > int(other)

    def __ge__(self, other):
        return int(self) >= int(other)


    # FREQUENCIES are the thing.

    def freq(self, intone=None):
        """Tonality can be "3rd", "4th", "5th" or a numeric offset"""

        note = twelve_tone_equal_440[self.value]
        if not intone:
            return note

        if intone == "3rd":
            return note * offsets[4][0]

        if intone == "4th":
            return note * offsets[5][0]

        if intone == "5th":
            return note * offsets[7][0]

        return note*intone

C = [MidiNote(n) for n in range(0, 127, 12)]
Cs = Df = [MidiNote(n) for n in range(1, 127, 12)]
D = [MidiNote(n) for n in range(2, 127, 12)]
Ds = Ef = [MidiNote(n) for n in range(3, 127, 12)]
E = [MidiNote(n) for n in range(4, 127, 12)]
F = [MidiNote(n) for n in range(5, 127, 12)]
Fs = Gf = [MidiNote(n) for n in range(6, 127, 12)]
G = [MidiNote(n) for n in range(7, 127, 12)]
Gs = Af = [MidiNote(n) for n in range(8, 127, 12)]
A = [MidiNote(n) for n in range(9, 127, 12)]
As = Bf = [MidiNote(n) for n in range(10, 127, 12)]
B = [MidiNote(n) for n in range(11, 127, 12)]

keys = {'C':0, 'Df':1, 'Cs':1, 'D':2, 'Ds':3, 'Ef':3,
        'E':4, 'F':5, 'Fs':6, 'Gf':6, 'G':7, 'Gs':8,
        'Af':8, 'A':9, 'As':10, 'Bf':10, 'B':11}

# ok, maybe we can just use the sharps as canonical?
keys_rev = dict((v,k) for k,v in keys.iteritems() if 'f' not in k)

more = {}
for k,v in keys_rev.iteritems():
    more[k+12] = v
    more[k+24] = v

keys_rev.update(more)
del k,v


