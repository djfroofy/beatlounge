from pprint import pformat

from twisted.trial.unittest import TestCase, SkipTest

from bl.testlib import ClockRunner, TestReactor
from bl.scheduler import BeatClock, Meter, Tempo

try:
    import pypm
    from bl.midi import PypmWrapper, init, getInput, getOutput
    from bl.midi import MidiHandler, MidiDispatcher
    from bl.midi import NoteOnOffHandler, ChordHandler, NoteEventHandler
    from bl.midi import ClockSender
    from bl.midi import printDeviceSummary
    from bl.midi import (NOTEON_CHAN1, NOTEON_CHAN2,
        NOTEOFF_CHAN1, NOTEOFF_CHAN2,
        NOTEON_CHAN3, NOTEOFF_CHAN3)
except ImportError:
    pypm = None

from bl.testlib import ClockRunner, TestReactor
from bl.tests.test_player import TestInstrument

def checkPypm():
    if pypm is None:
        raise SkipTest('pypm not installed')

class PypmWrapperTests(TestCase):

    def setUp(self):
        checkPypm()
        init()

    def _check_inputs(self):
        if not PypmWrapper.inputs:
            raise SkipTest('No input midi channels to test')

    def _check_outputs(self):
        if not PypmWrapper.outputs:
            raise SkipTest('No output midi channels to test')

    def test_getInput(self):
        self._check_inputs()
        # get by name
        entry = PypmWrapper.inputNames.items()[0]
        inputa = getInput(entry[1])
        # get by device no
        inputb = getInput(entry[0])
        self.assert_(inputa)
        self.assertIdentical(inputa, inputb)

    def test_getOutput(self):
        self._check_outputs()
        # get by name
        entry = PypmWrapper.outputNames.items()[0]
        outa = getOutput(entry[1])
        # get by device no
        outb = getOutput(entry[0])
        self.assert_(outa)
        self.assertIdentical(outa, outb)

    def test_init_idempodency(self):
        inputa = getInput(0)
        init()
        inputb = getInput(0)
        self.assertIdentical(inputa, inputb)

    def test_printDeviceSummary(self):
        messages = []
        printer = messages.append
        printDeviceSummary(printer)
        self.assert_(messages)


class FakeMidiInput:

    def __init__(self):
        self._buffer = []

    def Read(self, entries):
        read = self._buffer[:entries]
        self._buffer[:] = self._buffer[entries:]
        return read


class TestHandler(MidiHandler):

    def __init__(self):
        self.events = []

    def noteon(self, channel, note, velocity, timestamp):
        self.events.append(('noteon', channel, note, velocity, timestamp))


class MidiDispatcherTests(TestCase, ClockRunner):

    def setUp(self):
        checkPypm()
        tempo = Tempo(153)
        self.meter = Meter(4,4,tempo=tempo)
        self.clock = BeatClock(tempo=tempo, meter=self.meter, reactor=TestReactor())
        self.midiin = FakeMidiInput()
        self.midiin._buffer.extend([[NOTEON_CHAN1, i%128, 100, 0], i] for i in range(32*3+5))
        self.handler = TestHandler()
        self.dispatcher = MidiDispatcher(self.midiin, [self.handler], clock=self.clock)
        self.dispatcher.start()

    def test_scheduling(self):
        self.runTicks(97)
        expected = [ ('noteon', 1, i%128, 100, i) for i in range(64) ]
        self.assertEquals(self.handler.events, expected)

        self.handler.events[:] = []
        self.runTicks(1)
        expected = [ ('noteon', 1, i%128, 100, i) for i in range(64,96) ]
        self.assertEquals(self.handler.events, expected)

        self.handler.events[:] = []
        self.runTicks(1)
        expected = [ ('noteon', 1, i%128, 100, i) for i in range(96, 101) ]
        self.assertEquals(self.handler.events, expected)

        self.handler.events[:] = []
        self.runTicks(1)
        self.failIf(self.handler.events)


class NoteOnOffHandlerTests(TestCase):

    def setUp(self):
        checkPypm()
        tempo = Tempo(135)
        self.clock = BeatClock(tempo, reactor=TestReactor())
        self.instr1 = TestInstrument(self.clock)
        self.instr2 = TestInstrument(self.clock)
        self.handler = NoteOnOffHandler({1:self.instr1, 2:self.instr2})


    def test_noteon(self):
        self.handler([[NOTEON_CHAN1, 60, 120, 0],1])
        self.assertEquals(self.instr1.plays, [('note', 0, 60, 120)])
        self.failIf(self.instr2.plays)

        self.handler([[NOTEON_CHAN2, 75, 127, 0],2])
        self.assertEquals(self.instr1.plays, [('note', 0, 60, 120)])
        self.assertEquals(self.instr2.plays, [('note', 0, 75, 127)])

    def test_noteoff(self):
        self.handler([[NOTEOFF_CHAN1, 60, 120, 0],1])
        self.assertEquals(self.instr1.stops, [('note', 0, 60)])
        self.failIf(self.instr2.stops)

        self.handler([[NOTEOFF_CHAN2, 75, 127, 0],2])
        self.assertEquals(self.instr1.stops, [('note', 0, 60)])
        self.assertEquals(self.instr2.stops, [('note', 0, 75)])

    def test_wrong_channel(self):
        self.handler([[NOTEON_CHAN3, 60, 120, 0],1])
        self.handler([[NOTEOFF_CHAN3, 60, 120, 0],1])
        self.failIf(self.instr1.plays)
        self.failIf(self.instr2.plays)
        self.failIf(self.instr1.stops)
        self.failIf(self.instr2.stops)


class ChordHandlerTests(TestCase):

    def setUp(self):
        self.chords = []
        self.handler = ChordHandler(self.callback)

    def callback(self, chord):
        self.chords.append(chord)

    def test_noteon(self):
        self.handler.noteon(1, 60, 120, 0)
        self.assertEquals(self.chords, [[60]])
        self.handler.noteon(1, 64, 120, 0)
        self.assertEquals(self.chords, [[60], [60, 64]])
        self.handler.noteon(1, 67, 120, 0)
        self.assertEquals(self.chords, [[60], [60, 64], [60, 64, 67]])

    def test_noteoff(self):
        self.handler.noteon(1, 60, 120, 0)
        self.assertEquals(self.chords, [[60]])
        self.handler.noteon(1, 64, 120, 0)
        self.assertEquals(self.chords, [[60], [60, 64]])
        self.handler.noteon(1, 67, 120, 0)
        self.assertEquals(self.chords, [[60], [60, 64], [60, 64, 67]])
        self.chords[:] = []
        self.handler.noteoff(1, 60, 120, 0)
        self.assertEquals(self.chords, [[64, 67]],)
        self.handler.noteoff(1, 64, 120, 0)
        self.assertEquals(self.chords, [[64, 67], [67]])
        self.handler.noteoff(1, 67, 120, 0)
        self.assertEquals(self.chords, [[64, 67], [67], []])

    def test_noteoff_with_sustain(self):
        self.handler.sustain = 1
        self.handler.noteon(1, 60, 120, 0)
        self.assertEquals(self.chords, [[60]])
        self.handler.noteon(1, 64, 120, 0)
        self.assertEquals(self.chords, [[60], [60, 64]])
        self.handler.noteon(1, 67, 120, 0)
        self.assertEquals(self.chords, [[60], [60, 64], [60, 64, 67]])
        self.handler.noteoff(1, 60, 120, 0)
        self.assertEquals(self.chords, [[60], [60, 64], [60, 64, 67]])
        self.handler.noteon(1, 48, 120, 0)
        self.assertEquals(self.chords, [[60], [60, 64], [60, 64, 67], [64,67,48]])
        self.handler.noteoff(1, 64, 120, 0)
        self.handler.noteoff(1, 67, 120, 0)
        self.handler.noteoff(1, 48, 120, 0)
        self.assertEquals(self.chords, [[60], [60, 64], [60, 64, 67], [64,67,48]])
        self.handler.noteon(1, 52, 120, 0)
        self.assertEquals(self.chords, [[60], [60, 64], [60, 64, 67], [64,67,48], [52]])


class FakeMidiOutput:

    def __init__(self):
        self._buffer = []

    def Write(self, message):
        self._buffer.append(message)


class FakeTime:

    def __init__(self, clock):
        self.clock = clock

    def Time(self):
        return self.clock.ticks

class ClockSenderTests(TestCase, ClockRunner):

    def setUp(self):
        checkPypm()
        tempo = Tempo(120)
        self.clock = BeatClock(tempo, reactor=TestReactor())
        self.patch(pypm, 'Time', FakeTime(self.clock).Time)
        self.midiout = FakeMidiOutput()
        self.clockSender = ClockSender(self.midiout, clock=self.clock)
        self.clockSender.start()

    def test_sends(self):
        self.runTicks(96)
        self.assertEquals(self.midiout._buffer, [[[[250], 96]], [[[248], 96]]])
        self.midiout._buffer[:] = []
        self.runTicks(1)
        self.assertEquals(self.midiout._buffer, [[[[248], 97]]])
        self.midiout._buffer[:] = []
        self.runTicks(1)
        self.assertEquals(self.midiout._buffer, [[[[248], 98]]])


class NoteEventHandlerTests(TestCase):


    def setUp(self):
        self.events = []
        self.handler = NoteEventHandler(self.noteon, self.noteoff)

    def noteon(self, note, velocity):
        self.events.append(('noteon', note, velocity))

    def noteoff(self, note):
        self.events.append(('noteoff', note))


    def test_noteonoff_events(self):
        self.handler.noteon(1, 60, 120, 0)
        self.handler.noteon(1, 64, 100, 0)
        self.handler.noteoff(1, 60, 120, 0)
        self.assertEquals(self.events, [
                ('noteon', 60, 120), ('noteon', 64, 100), ('noteoff', 60)])


