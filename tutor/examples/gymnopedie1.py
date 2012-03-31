from comps.core import *

from bl.player import Conductor

meter34 = Meter(3,4)
clock.meters = [ meter34 ]


piano = piano_f()
piano.controlChange(sustain=127, reverb=80)

bottomNotes = nf(lcycle(31, [G[4], D[4]] * 8 + [Fs[4], B[3], E[3], E[3], D[3], A[3]] +  [D[3]] * 9))
bottomPlayer = Player(piano, bottomNotes, Sustainer(85), interval=0.75)

mv = Stepper([85] * 24 + [ 105 ] + [85] * 9 + [65] + [85] * 58)
middleNotes = nf(lcycle(93,
                        [N, [Fs[5],D[5],B[5]],  N,
                         N, [Fs[5],Cs[5],A[5]], N] * 8 + 
                        [N, [Fs[5],Cs[5],A[5]], N,
                         N, [Fs[5],D[5],B[5]],  N] +
                        [N,[B[4],G[4]],N, N,[G[5], D[5], B[5]],N, N,[D[5],A[5],F[5]],N, N,[E[5],C[5], A[5]],N, N,[E[5],B[5],G[5]],N,
                         N,[E[5],B[5],G[5],D[5]],N, N,[D[5],A[5],E[5],C[5]],N, N,[D[5],A[5],Fs[5],C[5]],N, N,[F[5],C[5],A[5]],N,
                         N,[E[5],C[5],A[5]],N, N,[E[5],B[5],G[5],D[5]],N, N,[D[5],A[5],E[5],C[5]],N, N,[D[5],A[5],Fs[5],C[5]],N]))
middlePlayer = ChordPlayer(piano, middleNotes, mv, interval=0.25)


tv = Stepper([ 80 ] * 12 + [80,83,86,89,92,95,95,92,88,85,80,80] + [80] * 9 +
             [ 80, 80, 83, 86, 89, 92, 95, 97, 97, 95, 93, 91, 89, 87, 85, 83 ] +  [80] * 8 +
             [80,83,86,89,92,95,95,92,88,85,80,80,80,80,80,80,80,83,86,89,92,95,95,92,88,85,80,80,80,80,80,80,80,80,80,80])
tv.steps = [ s - 4 for s in tv.steps ]
topNotes = nf(lcycle(93,
                     [N] * 12 +
                     [N, Fs[6], A[5], G[6],  Fs[6], Cs[6], B[5],
                     Cs[6], D[6], A[5], N, N] + [Fs[5],N,N] * 3 +
                     [N,Fs[6],A[5],   G[6],Fs[6],Cs[6],
                      B[5],Cs[6],D[6], A[5],N,N,
                     Cs[6],N,N,Fs[6],N,N] +
                     [E[6],N,N] * 3 + [A[5], B[5], C[6], E[6], D[6], B[5], D[6], C[6], B[5]] + 
                     [D[6], N, N] * 2 + [D[6], E[6], F[6], G[6], A[6], C[5], D[5], E[5], D[5], B[4]] + 
                     [D[6], N, N] * 2 + [D[6],N]))           
topPlayer = Player(piano, topNotes, tv, interval=0.25)


# Alternative 1

bottomNotesAlt1 = nf(lcycle(8,
                    [[E[4]], [Fs[4]], [B[4]], [E[4]],
                     [E[4]], [E[3]], [G[3],A[2]], [D[2],A[2],D[2]]]))
bottomPlayerAlt1 = ChordPlayer(piano, bottomNotesAlt1, Sustainer(100), interval=0.75)

middleNotesAlt1 = nf(lcycle(24,
                    [N, [G[5], E[5], B[5]], N,
                     N, [Fs[5], Cs[5], A[5]], N,
                     N, [Fs[5], D[5], B[5]], N,
                     N, [A[5], E[5], Cs[5]], N,
                     N, [A[5], Fs[5], Cs[5], A[5]], N,
                     N, [D[4], A[4]], [G[4], D[4], B[4]],
                     N, N, N, N, N, N]))
middlePlayerAlt1 = ChordPlayer(piano, middleNotesAlt1, Sustainer(100), interval=0.25)

topNotesAlt1 = nf(lcycle(24,
                    [[G[6]], N, N,
                     [Fs[6]], N, N,
                     [B[5]], [A[5]], [B[5]],
                     [Cs[6]], [D[6]], [E[6]],
                     [Cs[6]], [D[6]], [E[6]],
                     [Fs[6]], N, N,
                     [C[5], A[4], E[5],C[6]], N, N,
                     [D[5], A[4], Fs[5],D[6]], N, N]))
topPlayerAlt1 = ChordPlayer(piano, topNotesAlt1, Sustainer(100), interval=0.25)

# Alternate 2

bottomNotesAlt2 = nf(lcycle(8,
                    [[E[4]], [E[4]], [E[4]], [E[4]],
                     [E[4]], [E[3]], [G[3],A[2]], [D[2],A[2],D[2]]]))
bottomPlayerAlt2 = ChordPlayer(piano, bottomNotesAlt2, Sustainer(100), interval=0.75)


middleNotesAlt2 = nf(lcycle(24,
                    [N, [G[5], E[5], B[5]], N,
                     N, [A[4], F[5], D[5], A[5]], N,
                     N, [F[5], C[5], A[4]], N,
                     N, [A[4], E[5], C[5]], N,
                     N, [A[4], F[5], C[5], A[5]], N,
                     N, [D[4], A[3]], [G[4], D[4], B[3]],
                     N, N, N, N, N, N]))
middlePlayerAlt2 = ChordPlayer(piano, middleNotesAlt2, Sustainer(100), interval=0.25)

topNotesAlt2 = nf(lcycle(24,
                    [[G[6]], N, N,
                     [F[6]], N, N,
                     [B[4]], [C[6]], [F[6]],
                     [E[6]], [D[6]], [C[6]],
                     [E[6]], [D[6]], [C[6]],
                     [F[5]], N, N,
                     [C[7], A[5], E[6],C[6]], N, N,
                     [D[6], A[5], F[6],D[7]], N, N]))
topPlayerAlt2 = ChordPlayer(piano, topNotesAlt2, Sustainer(100), interval=0.25)


score = {
    None: 'a',
   'a': {'duration': 31, 'transitions': ['v1'], 'players': [bottomPlayer, middlePlayer, topPlayer]},
   'v1': {'duration': 8, 'transitions': ['b'], 'players': [bottomPlayerAlt1, middlePlayerAlt1, topPlayerAlt1]},
   'b': {'duration': 31, 'transitions': ['v2'], 'players': [bottomPlayer, middlePlayer, topPlayer]},
   'v2': {'duration': 8, 'transitions': ['a'], 'players': [bottomPlayerAlt2, middlePlayerAlt2, topPlayerAlt2]},
}
conductor = Conductor(score)

start = conductor.start
#def start():
#    bottomPlayer.startPlaying()
#    middlePlayer.startPlaying()
#    topPlayer.startPlaying()

if __name__ == '__main__':
    start()
    clock.run()

