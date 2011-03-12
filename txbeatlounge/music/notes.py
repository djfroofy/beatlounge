from decimal import Decimal
##############
# Midi notes #
##############

#C = [0, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120]
#Df = Cs = [1, 13, 25, 37, 49, 61, 73, 85, 97, 109, 121]
#D = [2, 14, 26, 38, 50, 62, 74, 86, 98, 110, 122]
#Ef = Ds = [3, 15, 27, 39, 51, 63, 75, 87, 99, 111, 123]
#E = [4, 16, 28, 40, 52, 64, 76, 88, 100, 112, 124]
#F = [5, 17, 29, 41, 53, 65, 77, 89, 101, 113, 125]
#Gf = Fs = [6, 18, 30, 42, 54, 66, 78, 90, 102, 114, 126]
#G = [7, 19, 31, 43, 55, 67, 79, 91, 103, 115, 127]
#Af = Gs = [8, 20, 32, 44, 56, 68, 80, 92, 104, 116]
#A = [9, 21, 33, 45, 57, 69, 81, 93, 105, 117]
#Bf = As = [10, 22, 34, 46, 58, 70, 82, 94, 106, 118]
#B = [11, 23, 35, 47, 59, 71, 83, 95, 107, 119]
#MIDI_NOTES = [C, Df, D, Ef, E, F, Gf, G, Af, A, Bf, B]

class MidiNote(int):

    def __init__(self, value=0): # value can be one of 0-11
        self.value = value
        int.__init__(self, value)

    def __iter__(self):
        n = self.value
        while n < 128:
            yield n
            n += 12

    def __getitem__(self, num):
        return self.value + num*12

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
        return self.__class__(int(other)-int(self))

    def freq(self, octave=0, intone=None):
        """
        Tonality can be "3rd", "4th", "5th" or a numeric offset.
        """
        note = twelve_tone_equal_440[self[octave]]
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
        n = self.value
        octave = 0
        while n < 128:
            fs.append(self.freq(octave, intone))
            octave += 1
            n += 12
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
# notice that this is bad
keys_rev = dict((v,k) for k,v in keys.iteritems())

def notesStringsForList(li):
    """
    Pass in a list and get out the str() letters that are in there.
    """

    retD = {}
    for note in li:
        if note in C:
            retD['C'] = True
        elif note in Df:
            retD['Df'] = True
        elif note in D:
            retD['D'] = True
        elif note in Ef:
            retD['Ef'] = True
        elif note in E:
            retD['E'] = True
        elif note in F:
            retD['F'] = True
        elif note in Gf:
            retD['Gf'] = True
        elif note in G:
            retD['G'] = True
        elif note in Af:
            retD['Af'] = True
        elif note in A:
            retD['A'] = True
        elif note in Bf:
            retD['Bf'] = True
        elif note in B:
            retD['B'] = True

    return set(retD.keys())

def flattenLists(li):
    """
    Takes a list of lists and returns a flat list of the submembers
    """
    ret = []
    for l in li:
        ret.extend(l)
    return ret

"""
chord_choices = [
    A11, A13, A9, AM7s5, Aaug, Aaug7, Adim, Adim7, Adom7, Af11, Af13, Af9, AfM7s5, Afaug, Afaug7,
    Afdim, Afdim7, Afdom7, Afm7f5, AfmM7, Afmaj, Afmaj11, Afmaj13, Afmaj7, Afmaj9, Afmin, Afmin11, Afmin13,
    Afmin7, Afmin9, Afsus2, Afsus4, Am7f5, AmM7, Amaj, Amaj11, Amaj13, Amaj7, Amaj9, Amin, Amin11, Amin13,
    Amin7, Amin9, As11, As13, As9, AsM7s5, Asaug, Asaug7, Asdim, Asdim7, Asdom7, Asm7f5, AsmM7, Asmaj,
    Asmaj11, Asmaj13, Asmaj7, Asmaj9, Asmin, Asmin11, Asmin13, Asmin7, Asmin9, Assus2, Assus4, Asus2, Asus4,
    B11, B13, B9, BM7s5, Baug, Baug7, Bdim, Bdim7, Bdom7, Bf11, Bf13, Bf9, BfM7s5, Bfaug, Bfaug7, Bfdim, Bfdim7,
    Bfdom7, Bfm7f5, BfmM7, Bfmaj, Bfmaj11, Bfmaj13, Bfmaj7, Bfmaj9, Bfmin, Bfmin11, Bfmin13, Bfmin7, Bfmin9,
    Bfsus2, Bfsus4, Bm7f5, BmM7, Bmaj, Bmaj11, Bmaj13, Bmaj7, Bmaj9, Bmin, Bmin11, Bmin13, Bmin7, Bmin9, Bsus2,
    Bsus4, C11, C13, C9, CM7s5, Caug, Caug7, Cdim, Cdim7, Cdom7, Cm7f5, CmM7, Cmaj, Cmaj11, Cmaj13, Cmaj7, Cmaj9,
    Cmin, Cmin11, Cmin13, Cmin7, Cmin9, Cs11, Cs13, Cs9, CsM7s5, Csaug, Csaug7, Csdim, Csdim7, Csdom7, Csm7f5,
    CsmM7, Csmaj, Csmaj11, Csmaj13, Csmaj7, Csmaj9, Csmin, Csmin11, Csmin13, Csmin7, Csmin9, Cssus2, Cssus4,
    Csus2, Csus4, D11, D13, D9, DM7s5, Daug, Daug7, Ddim, Ddim7, Ddom7, Df11, Df13, Df9, DfM7s5, Dfaug,
    Dfaug7, Dfdim, Dfdim7, Dfdom7, Dfm7f5, DfmM7, Dfmaj, Dfmaj11, Dfmaj13, Dfmaj7, Dfmaj9, Dfmin, Dfmin11, Dfmin13,
    Dfmin7, Dfmin9, Dfsus2, Dfsus4, Dm7f5, DmM7, Dmaj, Dmaj11, Dmaj13, Dmaj7, Dmaj9, Dmin, Dmin11, Dmin13, Dmin7,
    Dmin9, Ds11, Ds13, Ds9, DsM7s5, Dsaug, Dsaug7, Dsdim, Dsdim7, Dsdom7, Dsm7f5, DsmM7, Dsmaj, Dsmaj11,
    Dsmaj13, Dsmaj7, Dsmaj9, Dsmin, Dsmin11, Dsmin13, Dsmin7, Dsmin9, Dssus2, Dssus4, Dsus2, Dsus4,
    E11, E13, E9, EM7s5, Eaug, Eaug7, Edim, Edim7, Edom7, Ef11, Ef13, Ef9, EfM7s5, Efaug, Efaug7, Efdim,
    Efdim7, Efdom7, Efm7f5, EfmM7, Efmaj, Efmaj11, Efmaj13, Efmaj7, Efmaj9, Efmin, Efmin11, Efmin13, Efmin7,
    Efmin9, Efsus2, Efsus4, Em7f5, EmM7, Emaj, Emaj11, Emaj13, Emaj7, Emaj9, Emin, Emin11, Emin13, Emin7, Emin9,
    Esus2, Esus4, F11, F13, F9, FM7s5, Faug, Faug7, Fdim, Fdim7, Fdom7, Fm7f5, FmM7, Fmaj, Fmaj11, Fmaj13,
    Fmaj7, Fmaj9, Fmin, Fmin11, Fmin13, Fmin7, Fmin9, Fs11, Fs13, Fs9, FsM7s5, Fsaug, Fsaug7, Fsdim, Fsdim7,
    Fsdom7, Fsm7f5, FsmM7, Fsmaj, Fsmaj11, Fsmaj13, Fsmaj7, Fsmaj9, Fsmin, Fsmin11, Fsmin13, Fsmin7, Fsmin9,
    Fssus2, Fssus4, Fsus2, Fsus4, G11, G13, G9, GM7s5, Gaug, Gaug7, Gdim, Gdim7, Gdom7, Gf11, Gf13, Gf9,
    GfM7s5, Gfaug, Gfaug7, Gfdim, Gfdim7, Gfdom7, Gfm7f5, GfmM7, Gfmaj, Gfmaj11, Gfmaj13, Gfmaj7, Gfmaj9, Gfmin,
    Gfmin11, Gfmin13, Gfmin7, Gfmin9, Gfsus2, Gfsus4, Gm7f5, GmM7, Gmaj, Gmaj11, Gmaj13, Gmaj7, Gmaj9, Gmin,
    Gmin11, Gmin13, Gmin7, Gmin9, Gs11, Gs13, Gs9, GsM7s5, Gsaug, Gsaug7, Gsdim, Gsdim7, Gsdom7, Gsm7f5,
    GsmM7, Gsmaj, Gsmaj11, Gsmaj13, Gsmaj7, Gsmaj9, Gsmin, Gsmin11, Gsmin13, Gsmin7, Gsmin9, Gssus2, Gssus4,
    Gsus2, Gsus4
]
"""


_midi = lambda v : (v > 127) and (v - 12) or v

def invert(chord, inversion=1):
    if inversion < 0 or inversion > 4:
        raise ValueError('inversion argument must be one of: 0, 1, 2, 3, 4')
    if not inversion:
        return chord
    first = _midi(chord[0] + 12)
    second = chord[1]
    third = chord[2]
    if inversion >= 2:
        second = _midi(chord[1] + 12)
    if inversion >= 3:
        third = _midi(chord[2] + 12)
    if len(chord) >= 4:
        fourth = chord[3]
        if inversion >= 4:
            fourth = _midi(chord[3] + 12)
    if len(chord) == 3:
        return [ first, second, third ]
    return [ first, second, third, fourth ] + chord[4:]



# Scale definitions and function

def keyScale(scale, key='C', octave=0):
    base = keys[key]
    octave = octave * 12
    return [ n + base + octave for n in scale ]


# pentatonic

majorpenta = pentatonic = [ C[0], D[0], E[0], G[0], A[0],  ]
minorpenta = [ C[0], Ef[0], F[0], G[0], Bf[0],  ] 
egyptpenta = suspenta = [ C[0], D[0], F[0], G[0], Bf[0],  ]
bluesminor = mangong = [ C[0], Ef[0], F[0], Af[0], Bf[0],  ]
bluesmajor = ritusen = [ C[0], D[0], F[0], G[0], A[0],  ] 
insen = [ C[0], Df[0], F[0], G[0], Bf[0],  ]
hirajoshi = hirachoshi = [ C[0], D[0], Ef[0], G[0], Af[0],  ]
iwato = [ C[0], Df[0], F[0], Gf[0], Bf[0],  ]  
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

# Some human-level manipulations of the above objects

def getChordsFromNote(note="C"):
    import txbeatlounge
    chords = []
    for candidate in chord_choices:
        if any([n in flattenLists(candidate) for n in getattr(txbeatlounge.notes, note)]):
            chords.append(candidate)
    return chords

key_strings = ["C", "Df", "D", "Ef", "E", "F", "Gf", "G", "Af", "A", "Bf", "B"]

scale_strings = (
    "majorpenta", "minorpenta", "suspenta", "mangong", "ritusen", "insen", "hirajoshi",
    "iwato", "kumoi", "wholetone", "augmented", "prometheus", "blues", "tritone",
    "tstritone", "major", "melodic", "dorian", "aeolian", "mixolydian", "lydian",
    "byzantine", "phrygian", "phrygianDominant", "locrian", "arabic"
)

def getScalesKeysFromNote(note="C"):
    import txbeatlounge
    scale_keys = []
    for scale_string in scale_strings:
        scale = getattr(txbeatlounge.notes, scale_string)
        for key in key_strings:
            scale = keyScale(scale, key)
            if any([n in scale for n in getattr(txbeatlounge.notes, note)]):
                scale_keys.append((scale_string, key))
    return scale_keys


twelve_tone_equal_440 = [440*(2**(i/12.)) for i in range(-57,71)]

def freqForNote(note="C"):
    import txbeatlounge
    freqs = []
    for n in getattr(txbeatlounge.notes, note):
        freqs.append(twelve_tone_equal_440[n])
    return freqs


shrutis = {
0: (1/1.,),
1: (256/243., 16/15.),
2: (10/9., 9/8.),
3: (32/27., 6/5.),
4: (5/4., 81/64.),
5: (4/3.,),
# 27/20.,
6: (45/32., 729/512.),
7: (3/2.,),
8: (128/81., 8/5.),
9: (5/3., 27/16.),
10: (16/9., 9/5.),
11: (15/8., 243/128.),
12: (2,),
14: (18/8.,),
17: (12/5.,),
21: (10/3.,),
}

offsets = {}
for k, v in shrutis.iteritems():
    offsets[k] = []
    for val in v:
        offsets[k].append(440*val/twelve_tone_equal_440[57+k])





