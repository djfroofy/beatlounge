from txbeatlounge.music.constants import twelve_tone_equal_440
from txbeatlounge.music.freq import offsets

class MidiNote(object):
    """
    You probably shouldn't subclass this thing.
    """

    def __init__(self, value=0):
        if not 0 <= value < 128:
            raise ValueError("Value must be between 0 and 127 inclusive")
        self.value = value
        #int.__init__(self, value)

    def __repr__(self):
        return "MidiNote(%s)" % self.value

    def __str__(self):
        return repr(self)

    def __iter__(self):
        """Octaves from the root until the highest, < 127"""

        n = self.value
        while n < 128:
            yield self.__class__(n)
            n += 12

    def __getitem__(self, num):
        return MidiNote(self.value + num*12)

    def __len__(self):
        n = 0
        for i in self:
            n += 1
        return n

    def __int__(self):
        return self.value

    def __add__(self, other):
        return self.__class__(int(other)+int(self))

    def __sub__(self, other):
        return self.__class__(int(self)-int(other))

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

    def freqs(self, intone=None):
        fs = []
        for n in self:
            note = MidiNote(int(n))
            fs.append(note.freq(intone))
        return fs

C = MidiNote(0)
Cs = Df = MidiNote(1)
D = MidiNote(2)
Ds = Ef = MidiNote(3)
E = MidiNote(4)
F = MidiNote(5)
Fs = Gf = MidiNote(6)
G = MidiNote(7)
Gs = Af = MidiNote(8)
A = MidiNote(9)
As = Bf = MidiNote(10)
B = MidiNote(11)

keys = {'C':0, 'Df':1, 'Cs':1, 'D':2, 'Ds':3, 'Ef':3,
        'E':4, 'F':5, 'Fs':6, 'Gf':6, 'G':7, 'Gs':8,
        'Af':8, 'A':9, 'As':10, 'Bf':10, 'B':11}

# ok, maybe we can just use the sharps as canonical?
keys_rev = dict((v,k) for k,v in keys.iteritems() if 'f' not in k)


