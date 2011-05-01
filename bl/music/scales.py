from bl.music.notes import MidiNote


__all__ = [

]

class Scale(object):

    def __init__(self, proto, key=0):
        """
        proto is a scale in the form [0,2,4,5,7,9,11]
        """
        self.list = [MidiNote(n+key) for n in proto]
        self.key = key or self.list[0]

    def __repr__(self):
        return "Scale(%s)" % self.list

    def __iter__(self):
        for n in self.list:
            yield n

    def __len__(self):
        return len(self.list)

    def __add__(self, other):
        return Scale(self.list+list(other))

    def modulate(self, index):
        """
        Modulate the Scale in place.
        """
        s = self.modulated(index)
        if index < 0:
            s = s.transposed(-12)

        self.list = s.list
        self.key = self.list[0]

        return self


    def modulated(self, index):
        """
        Invert to index and transpose there.
        """

        n = self.list[index]
        return self.inverted(index).transposed(n)

    def inverted(self, index):

        n = self.list[index]
        new = []

        for i in self.list[index:]:
            new.append(i-n)
        for i in self.list[:index]:
            new.append(12+i-n)

        return Scale(new)

    def transposed(self, fact):
        return Scale([fact+n for n in self.list])






proto = {

    "insen": [0,1,5,7,10],
    "hirajoshi": [0,1,7,9,10],
    "iwato": [0,1,5,6,10],

    "majorpenta": [0,2,4,7,9],
    "suspenta": [0,2,5,7,10],
    "ritusen": [0,2,5,7,9],

    "minorpenta": [0,3,5,7,10],
    "mangong": [0,3,5,8,10],


}






###############
# Scales as list of MidiNotes.
# I think classes that mirror this would be better.
#


from bl.music.notes import *

# Scale definitions and function

def keyScale(scale, key='C', octave=0):
    base = keys[key]
    octave = octave * 12
    return [ n + base + octave for n in scale ]


#############
# pentatonic
#############


hirajoshi = hirachoshi = [ C[0], D[0], Ef[0], G[0], Af[0],  ]
kumoi = [ C[0], Df[0], F[0], G[0], Af[0],  ]

# hexatonic

wholetone = [ C[0], D[0], E[0], Fs[0], Gs[0], As[0],  ]
augmented = [ C[0], Ef[0], E[0], G[0], Gs[0], B[0],  ]
prometheus = [ C[0], D[0], E[0], Fs[0], A[0], Bf[0],  ]
blues = [ C[0], Ef[0], F[0], Fs[0], G[0], Bf[0],  ]
tritone = [ C[0], Df[0], E[0], Gf[0], G[0], Bf[0],  ]
tstritone = twoSemitoneTritone = [ C[0], Df[0], D[0], Fs[0], G[0], Bf[0],  ]

# heptatonic

major = ionian = [ C[0], D[0], E[0], F[0], G[0], A[0], B[0],  ]
melodic = melodiciMinor = [ C[0], D[0], Ef[0], F[0], G[0], A[0], B[0],  ]
dorian = [ C[0], D[0], Ef[0], F[0], G[0], A[0], Bf[0],  ]
aeolian = naturalMinor = [ C[0], D[0], Ef[0], F[0], G[0], Af[0], Bf[0],  ]
mixolydian = [ C[0], D[0], E[0], F[0], G[0], A[0], Bf[0],  ]
lydian = [ C[0], D[0], E[0], Fs[0], G[0], A[0], B[0],  ]
byzantine = hungarian = egyptian = [ C[0], D[0], Ef[0], Fs[0], G[0], Af[0], B[0],  ] 
phrygian = [ C[0], Df[0], Ef[0], F[0], G[0], Af[0], Bf[0],  ]
phrygianDominant = [ C[0], Df[0], E[0], F[0], G[0], Af[0], Bf[0],  ]
locrian = [ C[0], Df[0], Ef[0], F[0], Gf[0], Af[0], Bf[0],  ]  
arabic = [ C[0], Df[0], E[0], F[0], G[0], Af[0], B[0],  ]

# ocotatonic

diminished = [ C[0], D[0], Ef[0], F[0], Gf[0], Af[0], A[0], B[0],  ]


