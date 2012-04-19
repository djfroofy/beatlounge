from itertools import cycle

from twisted.trial.unittest import TestCase

from bl.scheduler import Tempo, Meter, BeatClock
from bl.testlib import TestInstrument, ClockRunner, TestReactor
from bl.orchestra.midi import Player, ChordPlayer


class PlayerTests(TestCase, ClockRunner):

    def setUp(self):
        tempo = Tempo(135)
        self.meter = Meter(4, 4, tempo=tempo)
        self.meterStandard = self.meter
        self.clock = BeatClock(tempo, meter=self.meter, reactor=TestReactor())
        self.instr1 = TestInstrument(self.clock)
        self.instr2 = TestInstrument(self.clock)
        self.dtt = self.clock.meter.dtt

    def test_player_plays_notes(self):
        notePlayer = Player(self.instr1, cycle([0, 1]).next,
                            velocity=cycle([120]).next,
                            clock=self.clock, interval=self.dtt(1, 4))
        notePlayer.resumePlaying()
        self.runTicks(96)
        expectedPlays = [
            ('note', 0, 0, 120),
            ('note', 24, 1, 120),
            ('note', 48, 0, 120),
            ('note', 72, 1, 120),
            ('note', 96, 0, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays)
        self.failIf(self.instr1.stops)

    def test_player_releases_notes(self):
        notePlayer = Player(self.instr1, cycle([0, 1]).next,
                            velocity=cycle([120]).next,
                            release=cycle([12]).next,
                            clock=self.clock, interval=self.dtt(1, 4))
        notePlayer.resumePlaying()
        self.runTicks(96)
        expectedPlays = [
            ('note', 0, 0, 120),
            ('note', 24, 1, 120),
            ('note', 48, 0, 120),
            ('note', 72, 1, 120),
            ('note', 96, 0, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays)
        self.assertEquals(self.instr1.stops,
                          [('note', 12, 0), ('note', 36, 1),
                           ('note', 60, 0), ('note', 84, 1)])

    def test_player_skips_noteoff_scheduling_on_None(self):
        notePlayer = Player(self.instr1, cycle([0, 1]).next,
                            velocity=cycle([120]).next,
                            release=cycle([12, None]).next,
                            clock=self.clock, interval=self.dtt(1, 4))
        notePlayer.resumePlaying()
        self.runTicks(96)
        expectedPlays = [
            ('note', 0, 0, 120),
            ('note', 24, 1, 120),
            ('note', 48, 0, 120),
            ('note', 72, 1, 120),
            ('note', 96, 0, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays)
        self.assertEquals(self.instr1.stops,
                          [('note', 12, 0), ('note', 60, 0)])

    def test_default_interval(self):
        notePlayer = Player(self.instr1, cycle([0, 1]).next,
                            velocity=cycle([120]).next,
                            release=cycle([12]).next,
                            clock=self.clock)
        notePlayer.resumePlaying()
        self.runTicks(48)
        self.assertEquals(self.instr1.plays, [('note', 0, 0, 120),
            ('note', 12, 1, 120), ('note', 24, 0, 120), ('note', 36, 1, 120),
            ('note', 48, 0, 120)])

    def test_default_velocity(self):
        notePlayer = Player(self.instr1, cycle([0, 1]).next,
                            release=cycle([12]).next,
                            clock=self.clock)
        notePlayer.resumePlaying()
        self.runTicks(48)
        self.assertEquals(self.instr1.plays, [('note', 0, 0, 127),
            ('note', 12, 1, 127), ('note', 24, 0, 127), ('note', 36, 1, 127),
            ('note', 48, 0, 127)])

    def test_pause_playing(self):
        notePlayer = Player(self.instr1, cycle([0, 1]).next,
                            velocity=cycle([120]).next,
                            clock=self.clock, interval=self.dtt(1, 4))
        notePlayer.resumePlaying()
        self.runTicks(96)
        expectedPlays = [
            ('note', 0, 0, 120),
            ('note', 24, 1, 120),
            ('note', 48, 0, 120),
            ('note', 72, 1, 120),
            ('note', 96, 0, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays)
        notePlayer.pausePlaying()
        self.runTicks(96)
        notePlayer.resumePlaying()
        self.runTicks(96)
        expectedPlays.extend([
            ('note', 216, 1, 120),
            ('note', 240, 0, 120),
            ('note', 264, 1, 120),
            ('note', 288, 0, 120)])
        self.assertEquals(self.instr1.plays, expectedPlays)

    def test_chord_player_plays_chords(self):
        notePlayer = ChordPlayer(self.instr1, cycle([[0, 1], [1, 0]]).next,
                                 velocity=cycle([120]).next,
                                 release=cycle([12]).next,
                                 clock=self.clock, interval=self.dtt(1, 4))
        notePlayer.resumePlaying()
        self.runTicks(96)
        expectedPlays = [
            ('chord', 0, [0, 1], 120),
            ('chord', 24, [1, 0], 120),
            ('chord', 48, [0, 1], 120),
            ('chord', 72, [1, 0], 120),
            ('chord', 96, [0, 1], 120)]
        self.assertEquals(self.instr1.plays, expectedPlays)
        self.assertEquals(self.instr1.stops,
                          [('chord', 12, [0, 1]), ('chord', 36, [1, 0]),
                           ('chord', 60, [0, 1]), ('chord', 84, [1, 0])])

    def test_player_control_changes(self):
        notePlayer = Player(self.instr1, cycle([0, 1]).next,
                            velocity=cycle([120]).next,
                            cc={'expression': cycle([100, 115, 120]).next,
                                'sustain': cycle([50, 120]).next},
                            clock=self.clock, interval=self.dtt(1, 4))
        notePlayer.resumePlaying()
        self.runTicks(96)
        expectedPlays = [
            ('note', 0, 0, 120),
            ('note', 24, 1, 120),
            ('note', 48, 0, 120),
            ('note', 72, 1, 120),
            ('note', 96, 0, 120)]
        self.assertEquals(self.instr1.plays, expectedPlays)
        self.assertEquals(self.instr1.cc,
                          [(0, {'sustain': 50, 'expression': 100}),
                           (24, {'sustain': 120, 'expression': 115}),
                           (48, {'sustain': 50, 'expression': 120}),
                           (72, {'sustain': 120, 'expression': 100}),
                           (96, {'sustain': 50, 'expression': 115})])
#    def test_chordPlayerPlaysChords(self):
#        for i in range(10):
#            self.chordPlayer.play()
#            self.clock.tick()
#        expectedPlays = [
#                     ('chord', 0, [0, 1], 100),
#                     ('chord', 1, [2, 3], 100),
#                     ('chord', 2, [0, 1], 100),
#                     ('chord', 3, [2, 3], 100),
#                     ('chord', 4, [0, 1], 100),
#                     ('chord', 5, [2, 3], 100),
#                     ('chord', 6, [0, 1], 100),
#                     ('chord', 7, [2, 3], 100),
#                     ('chord', 8, [0, 1], 100),
#                     ('chord', 9, [2, 3], 100)]
#        self.assertEquals(self.instr2.plays, expectedPlays)
#        self.failIf(self.instr2.stops)
#        self.assertEquals(len(self.chordPlayerFilter.calls), 10)
#
#    def test_stoppingNotes(self):
#        notePlayer = NotePlayer(self.instr1,
#                                snd(cycle([0, 1, 2])),
#                                TestFilter(100),
#                                stop=lambda: 2,
#                                clock=self.clock)
#        for i in range(6):
#            notePlayer.play()
#            self.clock.tick()
#        expectedStops = [('note', 2, 0), ('note', 3, 1), ('note', 4, 2),
#                         ('note', 5, 0), ('note', 6, 1)]
#        self.assertEquals(self.instr1.stops, expectedStops)
#
#    def test_stoppingChords(self):
#        chordPlayer = ChordPlayer(self.instr2,
#                                snd(cycle([[0, 1], [2, 3], [4, 5]])),
#                                TestFilter(100),
#                                stop=lambda: 2,
#                                clock=self.clock)
#        for i in range(6):
#            chordPlayer.play()
#            self.clock.tick()
#        expectedStops = [
#                        ('chord', 2, [0, 1]), ('chord', 3, [2, 3]),
#                        ('chord', 4, [4, 5]),
#                        ('chord', 5, [0, 1]), ('chord', 6, [2, 3])]
#        self.assertEquals(self.instr2.stops, expectedStops)
#
#    def test_PlayerIsAliasForNotePlayer(self):
#        self.assertIdentical(Player, NotePlayer)
#
#    def test_stopIsConvertedToFactory(self):
#        notePlayer = NotePlayer(self.instr1,
#                                snd(cycle([0, 1, 2])),
#                                TestFilter(100),
#                                stop=2,
#                                clock=self.clock)
#        self.assertEquals(notePlayer.stop(), 2)
#
#    def test_playSkipsNone(self):
#        notePlayer = NotePlayer(self.instr1,
#                                snd(cycle([0, 1, N])),
#                                TestFilter(100),
#                                clock=self.clock)
#        for i in range(6):
#            notePlayer.play()
#            self.clock.tick()
#        expectedPlays = [
#            ('note', 0, 0, 100),
#            ('note', 1, 1, 100),
#            ('note', 3, 0, 100),
#            ('note', 4, 1, 100)]
#        self.assertEquals(self.instr1.plays, expectedPlays)
#
#    def test_playerExhaustsCallChain(self):
#        # maybe this is bad
#        def f():
#            def g():
#                def h():
#                    def i():
#                        return 1
#                    return i
#                return h
#            return g
#        notePlayer = NotePlayer(self.instr1, f, TestFilter(100),
#                            clock=self.clock)
#        for i in range(2):
#            notePlayer.play()
#            self.clock.tick()
#        expectedPlays = [
#            ('note', 0, 1, 100),
#            ('note', 1, 1, 100)]
#        self.assertEquals(self.instr1.plays, expectedPlays)
#
#    def test_generatorsAreWrapperInNoteFactory(self):
#        c = cycle([1, 2])
#        notePlayer = NotePlayer(self.instr1, c, TestFilter(100),
#                            clock=self.clock)
#        for i in range(3):
#            notePlayer.play()
#            self.clock.tick()
#        expectedPlays = [
#            ('note', 0, 1, 100),
#            ('note', 1, 2, 100),
#            ('note', 2, 1, 100)]
#        self.assertEquals(self.instr1.plays, expectedPlays)
#
#    def test_velocityGetsCalledEvenOnNoneNotes(self):
#        notePlayer = NotePlayer(self.instr1,
#                                snd(cycle([0, 1, N])),
#                                Stepper([100, 90, 80]),
#                                clock=self.clock)
#        for i in range(6):
#            notePlayer.play()
#            self.clock.tick()
#        expectedPlays = [
#            ('note', 0, 0, 100),
#            ('note', 1, 1, 90),
#            ('note', 3, 0, 100),
#            ('note', 4, 1, 90)]
#        self.assertEquals(self.instr1.plays, expectedPlays)
#
#    def test_valueErrorForBadNoteFactory(self):
#        self.assertRaises(ValueError, NotePlayer, self.instr1, '1234',
#                                TestFilter(100), clock=self.clock)
#
#    def test_startPlaying(self):
#        self.notePlayer.startPlaying('a')
#        self.runTicks(96)
#        expectedPlays = [('note', 0, 0, 120), ('note', 24, 1, 120),
#                         ('note', 48, 0, 120), ('note', 72, 1, 120),
#                         ('note', 96, 0, 120)]
#        self.assertEquals(self.instr1.plays, expectedPlays)
#
#    def test_newVelocityFactory(self):
#        velocities = cycle([127, 120, 110, 100])
#
#        def v():
#            return velocities.next()
#        notePlayer = NotePlayer(self.instr1, cycle([0,1]), v,
#                                clock=self.clock, interval=self.dtt(1,4))
#        notePlayer.startPlaying('a')
#        self.runTicks(96)
#        expectedPlays = [('note', 0, 0, 127), ('note', 24, 1, 120),
#                         ('note', 48, 0, 110), ('note', 72, 1, 100),
#                         ('note', 96, 0, 127)]
#        self.assertEquals(self.instr1.plays, expectedPlays)
#
#    def test_startPlayingBeginsAtNextMeasure(self):
#        self.runTicks(1)
#        self.notePlayer.startPlaying('a')
#        self.runTicks(96 * 2 + 1)
#        expectedPlays = [('note', 96, 0, 120), ('note', 120, 1, 120),
#                         ('note', 144, 0, 120), ('note', 168, 1, 120),
#                         ('note', 192, 0, 120)]
#        self.assertEquals(self.instr1.plays, expectedPlays)
#
#    def test_stopPlaying(self):
#        self.notePlayer.startPlaying('a')
#        self.notePlayer.stopPlaying('a')
#        self.runTicks(96 * 2)
#        expectedPlays = [('note', 0, 0, 120), ('note', 24, 1, 120),
#                         ('note', 48, 0, 120), ('note', 72, 1, 120)]
#        self.assertEquals(self.instr1.plays, expectedPlays)
