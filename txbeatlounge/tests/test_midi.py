from pprint import pformat

from twisted.trial.unittest import TestCase, SkipTest

from txbeatlounge.testlib import ClockRunner, TestReactor
from txbeatlounge.scheduler import BeatClock, Meter

try:
    import pypm
    from txbeatlounge.midi import PypmWrapper, init, getInput, getOutput
    from txbeatlounge.midi import MidiHandler, MidiDispatcher
    from txbeatlounge.midi import NoteOnOffHandler
    from txbeatlounge.midi import printDeviceSummary
    from txbeatlounge.midi import (NOTEON_CHAN1, NOTEON_CHAN2,
        NOTEOFF_CHAN1, NOTEOFF_CHAN2,
        NOTEON_CHAN3, NOTEOFF_CHAN3)
except ImportError:
    pypm = None

from txbeatlounge.testlib import ClockRunner, TestReactor
from txbeatlounge.tests.test_player import TestInstrument

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
        self.meters = [ Meter(4,4), Meter(3,4) ]
        self.clock = BeatClock(135, meters=self.meters, reactor=TestReactor())
        self.midiin = FakeMidiInput()
        self.midiin._buffer.extend([[NOTEON_CHAN1, i%128, 100, 0], i] for i in range(32*3+5))
        self.handler = TestHandler()
        self.dispatcher = MidiDispatcher(self.midiin, [self.handler], clock=self.clock)
        self.dispatcher.start()

    def test_scheduling(self):
        self.runTicks(1)
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
        self.clock = BeatClock(135, reactor=TestReactor())
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
