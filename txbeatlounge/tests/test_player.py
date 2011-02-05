import random

from itertools import cycle

from zope.interface.verify import verifyClass, verifyObject

from twisted.trial.unittest import TestCase

from txbeatlounge.player import NotePlayer, ChordPlayer, Player, noteFactory, N, R
from txbeatlounge.player import INotePlayer, IChordPlayer, randomPhrase, sequence, Q
from txbeatlounge.player import Conductor, START
from txbeatlounge.player import explode, cut, callMemo 
from txbeatlounge.scheduler import BeatClock, Meter, mtt
from txbeatlounge.filters import BaseFilter, Stepper
from txbeatlounge.testlib import TestReactor, ClockRunner

snd = noteFactory

class TestInstrument:

    def __init__(self, clock):
        self.clock = clock
        self.plays = []
        self.stops = []

    def playnote(self, note, velocity):
        self.plays.append(('note', self.clock.ticks, note, velocity))

    def stopnote(self, note):
        self.stops.append(('note', self.clock.ticks, note))

    def playchord(self, chord, velocity):
        self.plays.append(('chord', self.clock.ticks, chord, velocity))

    def stopchord(self, chord):
        self.stops.append(('chord', self.clock.ticks, chord))


class TestFilter(BaseFilter):

    def __init__(self, sustain):
        self.calls = []
        self.sustain = sustain

    def filter(self, v, o):
        self.calls.append((v, o))
        return self.sustain, o


class PlayerTests(TestCase, ClockRunner):
    
    def setUp(self):
        self.meters = [ Meter(4,4), Meter(3,4) ]
        self.meterStandard = self.meters[0]
        self.meter34 = self.meters[1]
        self.clock = BeatClock(135, meters=self.meters, reactor=TestReactor())
        self.instr1 = TestInstrument(self.clock)
        self.instr2 = TestInstrument(self.clock)
        self.notePlayer = NotePlayer(self.instr1, snd(cycle([0,1])), TestFilter(120),
                                     clock=self.clock, interval=0.25)
        self.chordPlayer = ChordPlayer(self.instr2, snd(cycle([[0,1],[2,3]])), TestFilter(100),
                                     clock=self.clock, interval=0.125)
        

    def test_interfaces(self):
        verifyClass(INotePlayer, NotePlayer)
        verifyObject(INotePlayer, self.notePlayer)
        verifyClass(IChordPlayer, ChordPlayer)
        verifyObject(IChordPlayer, self.chordPlayer)

    def test_notePlayerPlaysNotes(self):
        for i in range(10):
            self.notePlayer.play()
            self.clock.tick()
        expectedPlays = [
                    ('note', 0, 0, 120),
                    ('note', 1, 1, 120),
                    ('note', 2, 0, 120),
                    ('note', 3, 1, 120),
                    ('note', 4, 0, 120),
                    ('note', 5, 1, 120),
                    ('note', 6, 0, 120),
                    ('note', 7, 1, 120),
                    ('note', 8, 0, 120),
                    ('note', 9, 1, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays)
        self.failIf(self.instr1.stops)
        self.assertEquals(len(self.notePlayer.velocity.calls), 10)

    def test_chordPlayerPlaysChords(self):
        for i in range(10):
            self.chordPlayer.play()
            self.clock.tick()
        expectedPlays = [
                     ('chord', 0, [0, 1], 100),
                     ('chord', 1, [2, 3], 100),
                     ('chord', 2, [0, 1], 100),
                     ('chord', 3, [2, 3], 100),
                     ('chord', 4, [0, 1], 100),
                     ('chord', 5, [2, 3], 100),
                     ('chord', 6, [0, 1], 100),
                     ('chord', 7, [2, 3], 100),
                     ('chord', 8, [0, 1], 100),
                     ('chord', 9, [2, 3], 100)]
        self.assertEquals(self.instr2.plays, expectedPlays)
        self.failIf(self.instr2.stops)
        self.assertEquals(len(self.chordPlayer.velocity.calls), 10)

    def test_stoppingNotes(self):
        notePlayer = NotePlayer(self.instr1, snd(cycle([0,1,2])), TestFilter(100),
                                stop=lambda:2, clock=self.clock)
        for i in range(6):
            notePlayer.play()
            self.clock.tick()
        expectedStops = [('note', 2, 0), ('note', 3, 1), ('note', 4, 2),
                         ('note', 5, 0), ('note', 6, 1)]
        self.assertEquals(self.instr1.stops, expectedStops)

    def test_stoppingChords(self):
        chordPlayer = ChordPlayer(self.instr2, snd(cycle([[0,1],[2,3],[4,5]])), TestFilter(100),
                                stop=lambda:2, clock=self.clock)
        for i in range(6):
            chordPlayer.play()
            self.clock.tick()
        expectedStops = [('chord', 2, [0, 1]), ('chord', 3, [2, 3]), ('chord', 4, [4, 5]),
                         ('chord', 5, [0, 1]), ('chord', 6, [2, 3])]
        self.assertEquals(self.instr2.stops, expectedStops)

    def test_PlayerIsAliasForNotePlayer(self):
        self.assertIdentical(Player, NotePlayer)

    def test_stopIsConvertedToFactory(self):
        notePlayer = NotePlayer(self.instr1, snd(cycle([0,1,2])), TestFilter(100),
                                stop=2, clock=self.clock)
        self.assertEquals(notePlayer.stop(), 2)

    def test_playSkipsNone(self):
        notePlayer = NotePlayer(self.instr1, snd(cycle([0,1,N])), TestFilter(100),
                            clock=self.clock)
        for i in range(6):
            notePlayer.play()
            self.clock.tick()
        expectedPlays = [
            ('note', 0, 0, 100),
            ('note', 1, 1, 100),
            ('note', 3, 0, 100),
            ('note', 4, 1, 100),]
        self.assertEquals(self.instr1.plays, expectedPlays)

    def test_playerExhaustsCallChain(self):
        # maybe this is bad
        def f():
            def g():
                def h():
                    def i():
                        return 1
                    return i
                return h
            return g
        notePlayer = NotePlayer(self.instr1, f, TestFilter(100),
                            clock=self.clock)
        for i in range(2):
            notePlayer.play()
            self.clock.tick()
        expectedPlays = [
            ('note', 0, 1, 100),
            ('note', 1, 1, 100),]
        self.assertEquals(self.instr1.plays, expectedPlays)
        

    def test_generatorsAreWrapperInNoteFactory(self):
        c = cycle([1,2])
        notePlayer = NotePlayer(self.instr1, c, TestFilter(100),
                            clock=self.clock)
        for i in range(3):
            notePlayer.play()
            self.clock.tick()
        expectedPlays = [
            ('note', 0, 1, 100),
            ('note', 1, 2, 100),
            ('note', 2, 1, 100),]
        self.assertEquals(self.instr1.plays, expectedPlays)


    def test_velocityGetsCalledEvenOnNoneNotes(self):
        notePlayer = NotePlayer(self.instr1, snd(cycle([0,1,N])), Stepper([100, 90, 80]),
                            clock=self.clock)
        for i in range(6):
            notePlayer.play()
            self.clock.tick()
        expectedPlays = [
            ('note', 0, 0, 100),
            ('note', 1, 1, 90),
            ('note', 3, 0, 100),
            ('note', 4, 1, 90),]
        self.assertEquals(self.instr1.plays, expectedPlays)

    def test_valueErrorForBadNoteFactory(self):
        self.assertRaises(ValueError, NotePlayer, self.instr1, '1234', TestFilter(100),
                            clock=self.clock)


    def test_startPlaying(self):
        self.notePlayer.startPlaying('a')
        self.runTicks(96)
        expectedPlays = [('note', 0, 0, 120), ('note', 24, 1, 120),
                         ('note', 48, 0, 120), ('note', 72, 1, 120),
                         ('note', 96, 0, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays) 

    def test_startPlayingBeginsAtNextMeasure(self):
        self.runTicks(1)
        self.notePlayer.startPlaying('a')
        self.runTicks(96 * 2 + 1)
        expectedPlays = [('note', 96, 0, 120), ('note', 120, 1, 120),
                         ('note', 144, 0, 120), ('note', 168, 1, 120),
                         ('note', 192, 0, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays) 

    def test_stopPlaying(self):
        self.notePlayer.startPlaying('a')
        #self.runTicks(7)
        self.notePlayer.stopPlaying('a')
        self.runTicks(96 * 2)
        expectedPlays = [('note', 0, 0, 120), ('note', 24, 1, 120),
                         ('note', 48, 0, 120), ('note', 72, 1, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays) 


class ConductorTests(TestCase, ClockRunner):
    
    def setUp(self):
        self.meters = [ Meter(3,4) ]
        self.clock = BeatClock(135, meters=self.meters, reactor=TestReactor())
        self.instr1 = TestInstrument(self.clock)
        self.instr2 = TestInstrument(self.clock)
        self.instr3 = TestInstrument(self.clock)
        self.notePlayer1 = NotePlayer(self.instr1, snd(cycle([0,1,2])), TestFilter(120),
                                     clock=self.clock, interval=0.25)
        self.notePlayer2 = NotePlayer(self.instr2, snd(cycle([3,4,5,6,7,8])), TestFilter(120),
                                     clock=self.clock, interval=0.125)
        self.chordPlayer = ChordPlayer(self.instr3, snd(cycle([[0,1],[2,3],[4,5]])), TestFilter(100),
                                     clock=self.clock, interval=0.125)
        score = { START : 'a',
                 'a': { 'transitions': ['b'], 'players': [self.notePlayer1, self.notePlayer2], 'duration': 2},
                 'b': { 'transitions': ['a'], 'players': [self.notePlayer1, self.chordPlayer], 'duration': 1} }
        self.score = score
        self.conductor = Conductor(score, self.clock)

    def test_start(self):
        self.conductor.start()
        self.runTicks(72)
        self.assertEquals(self.instr1.plays, [('note', 72, 0, 120)])
        self.assertEquals(self.instr2.plays, [('note', 72, 3, 120)])
        self.failIf(self.instr3.plays)

    def test_transitions(self):
        self.conductor.start()
        # Run players for 4 measures
        self.runTicks(72 + 72 * 4 - 1)
        expected1 = [('note', 72, 0, 120),
                     ('note', 96, 1, 120),
                     ('note', 120, 2, 120),
                     ('note', 144, 0, 120),
                     ('note', 168, 1, 120),
                     ('note', 192, 2, 120),
                     ('note', 216, 0, 120),
                     ('note', 240, 1, 120),
                     ('note', 264, 2, 120),
                     ('note', 288, 0, 120),
                     ('note', 312, 1, 120),
                     ('note', 336, 2, 120)]
        self.assertEquals(self.instr1.plays, expected1)
        expected2 = [('note', 72, 3, 120),
                     ('note', 84, 4, 120),
                     ('note', 96, 5, 120),
                     ('note', 108, 6, 120),
                     ('note', 120, 7, 120),
                     ('note', 132, 8, 120),
                     ('note', 144, 3, 120),
                     ('note', 156, 4, 120),
                     ('note', 168, 5, 120),
                     ('note', 180, 6, 120),
                     ('note', 192, 7, 120),
                     ('note', 204, 8, 120),
                     ('note', 288, 3, 120),
                     ('note', 300, 4, 120),
                     ('note', 312, 5, 120),
                     ('note', 324, 6, 120),
                     ('note', 336, 7, 120),
                     ('note', 348, 8, 120)]
        self.assertEquals(self.instr2.plays, expected2)
        expected3 = [('chord', 216, [0, 1], 100),
                     ('chord', 228, [2, 3], 100),
                     ('chord', 240, [4, 5], 100),
                     ('chord', 252, [0, 1], 100),
                     ('chord', 264, [2, 3], 100),
                     ('chord', 276, [4, 5], 100)]
        self.assertEquals(self.instr3.plays, expected3)


    def test_hold(self):
        self.conductor.start()
        self.runTicks(144 + 72 + 24)
        self.conductor.hold()
        self.runTicks(72 + 71 - 24)
        self._expected_held = [
                    ('chord', 216, [0, 1], 100),
                    ('chord', 228, [2, 3], 100),
                    ('chord', 240, [4, 5], 100),
                    ('chord', 252, [0, 1], 100),
                    ('chord', 264, [2, 3], 100),
                    ('chord', 276, [4, 5], 100),
                    ('chord', 288, [0, 1], 100),
                    ('chord', 300, [2, 3], 100),
                    ('chord', 312, [4, 5], 100),
                    ('chord', 324, [0, 1], 100),
                    ('chord', 336, [2, 3], 100),
                    ('chord', 348, [4, 5], 100)]
        self.assertEquals(self.instr3.plays, self._expected_held)
        self.assertEquals(self.conductor.currentNode['key'], 'b')

    def test_release(self):
        self.test_hold()
        self.conductor.release()
        self.runTicks(72)
        self.assertEquals(self.instr3.plays, self._expected_held)
        self.assertEquals(self.conductor.currentNode['key'], 'a')

class UtilityTests(TestCase):

    def test_noteFactory(self):
        g = noteFactory(cycle([1,2,3, lambda : 4]))
        snds = []
        for i in range(8):
            snds.append(g())
        self.assertEquals(snds, [1,2,3,4] * 2)

    def test_miscFactories(self):
        self.assertEquals(N(), None)
        self.assert_(R(1,2,3)() in [1,2,3])

    def test_randomPhrases(self):

        phrases = [(1,2,3),(4,5,6),(7,8,9)]
        chosen = [phrases[0]]
        def choose(phrases):
            self.assertIn(chosen[0], phrases)
            return chosen[0]

        self.patch(random, 'choice', choose)
        
        g = randomPhrase(*phrases)
        self.assertEquals(g.next(), 1)
        self.assertEquals(g.next(), 2)
        chosen[0] = phrases[2]
        self.assertEquals(g.next(), 3)
        self.assertEquals(g.next(), 7)
        self.assertEquals(g.next(), 8)
        self.assertEquals(g.next(), 9)
        self.assertEquals(g.next(), 7)
        self.assertEquals(g.next(), 8)


    def test_randomPhrasesLength(self):
        g = randomPhrase(3, (1,2,3), (4,5,6))
        
        self.assertRaises(ValueError, randomPhrase, 4, (1,2,3,4), (5,6,7,8,9))

        def choose(phrases):
            self.assertEquals(phrases, ((1,2,3), (4,5,6)))
            return (1,2,3)
        self.patch(random, 'choice', choose)
        g.next()


    def test_sequence(self):
        notes = sequence([(1, 0),(2, 2),(3, 4),(4, 6)], 8)
        self.assertEquals(notes, [1,N,2,N,3,N,4,N])
        notes = sequence([(3, 4)], 8)
        self.assertEquals(notes, [N,N,N,N,3,N,N,N])

        chords = sequence([((1,2,3),2),([4,5],4)], 8)
        self.assertEquals(chords, [N,N,(1,2,3),N,[4,5],N,N,N])

        # semiquaver triplet
        notes = sequence([(4,3),(5,5),(1,21),(2,22),(3,23)], 24)
        self.assertEquals(notes,
            [N,N,N, 4,N,5,
             N,N,N, N,N,N,
             N,N,N, N,N,N,
             N,N,N, 1,2,3])

    def test_explode(self):
        s = [1,2,3,4]
        exploded = explode(s)
        self.assertEquals(exploded, [1, N, 2, N, 3, N, 4, N])
        exploded = explode(s, 4)
        self.assertEquals(exploded, [1, N, N, N, 2, N, N, N, 3, N, N, N, 4, N, N, N])
        s = [1,N,2,N,N,3,4,N]
        exploded = explode(s)
        self.assertEquals(exploded, [1, N, N, N, 2, N, N, N, N, N, 3, N, 4, N, N, N])
        exploded = explode(s, 4)
        self.assertEquals(exploded, [1, N, N, N, N, N, N, N, 2, N, N, N, N, N, N, N,
                                     N, N, N, N, 3, N, N, N, 4, N, N, N, N, N, N, N])

    def test_cut(self):
        s = explode([1,N,2,N,N,3,4,N], 4)
        for i in range(512):
            chopped = cut(s)
            self.assertEquals(len(chopped), 32)


    def test_callMemo(self):
        start = [0]
        def func():
            start[0] = start[0] + 1
            return start[0]
        f = callMemo(func)
        values = []
        cur = 1
        for i in range(2):
            v = f()
            self.assertEquals(v, cur)
            cur += 1
            values.append(f.currentValue)
        self.assertEquals(values, [1,2])
       




        

