from pprint import pformat

from twisted.trial.unittest import TestCase, SkipTest

try:
    import pypm
    from txbeatlounge.midi import PypmWrapper, init, getInput, getOutput
    from txbeatlounge.midi import printDeviceSummary
    from txbeatlounge.midi import (NOTEON_CHAN1, NOTEON_CHAN2,
        NOTEOFF_CHAN1, NOTEOFF_CHAN2)
except ImportError:
    pypm = None

from txbeatlounge.testlib import ClockRunner, TestReactor

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


#class FakeMidiInput:
#
#    def __init__(self):
#        self._buffer = []
#
#    def Read(self, entries):
#        read = self._buffer[:entries]
#        self._buffer[:] = self._buffer[entries:]
#        return read
#
#
#class MidiDispatcherTests(TestCase, ClockRunner):
#
#    def setUp(self):
#        self.meters = [ Meter(4,4), Meter(3,4) ]
#        self.clock = BeatClock(135, meters=self.meters, reactor=TestReactor())
#        self.midiin = FakeMidiInput()
#        self.midiIn._buffer.append()
#        self.dispatcher = MidiDispatcher(self.midiIn, [self.handler], clock=self.clock)
#
#    def test_scheduling(self):
#        self.runTicks(1)
