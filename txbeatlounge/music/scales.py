



###############
# Scales as list of MidiNotes.
# I think classes that mirror this would be better.
#


from txbeatlounge.music.notes import *

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


