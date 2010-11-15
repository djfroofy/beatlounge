from itertools import cycle

from zope.interface.verify import verifyClass, verifyObject

from twisted.trial.unittest import TestCase

from txbeatlounge.player import NotePlayer, ChordPlayer, Player, generateSounds, N, R
from txbeatlounge.player import INotePlayer, IChordPlayer
from txbeatlounge.scheduler import BeatClock, Meter
from txbeatlounge.filters import BaseFilter
from txbeatlounge.testlib import TestReactor, ClockRunner

snd = generateSounds

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

    def test_startPlaying(self):
        self.notePlayer.startPlaying('a')
        self._runTicks(96 * 2)
        expectedPlays = [('note', 96, 0, 120), ('note', 120, 1, 120),
                         ('note', 144, 0, 120), ('note', 168, 1, 120),
                         ('note', 192, 0, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays) 

    def test_stopPlaying(self):
        self.notePlayer.startPlaying('a')
        self._runTicks(96)
        self.notePlayer.stopPlaying('a')
        self._runTicks(96 * 2)
        expectedPlays = [('note', 96, 0, 120), ('note', 120, 1, 120),
                         ('note', 144, 0, 120), ('note', 168, 1, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays) 


class UtilityTests(TestCase):

    def test_generateSounds(self):
        g = generateSounds(cycle([1,2,3, lambda : 4]))
        snds = []
        for i in range(8):
            snds.append(g())
        self.assertEquals(snds, [1,2,3,4] * 2)

    def test_miscFactories(self):
        self.assertEquals(N(), None)
        self.assert_(R(1,2,3)() in [1,2,3])
 
