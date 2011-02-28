
from twisted.python import failure, log

import pypm

from txbeatlounge.utils import getClock


__all__ = ['init', 'initialize', 'getInput', 'getOutput', 'printDeviceSummary',
           'ClockSender', 'DemoHandler', 'MidiDispatcher', 'FUNCTIONS']

class PypmWrapper:

    inputs = ()
    outputs = ()

    def initialize(self):
        pypm.Initialize()
        self.outputs = []
        self.inputs = []
        self.deviceMap = {}
        self._gatherDeviceInfo()

    def _gatherDeviceInfo(self):
        for devno in range(pypm.CountDevices()):
            info = pypm.GetDeviceInfo(devno)
            
            m = self.deviceMap.setdefault(info[1], {'output':None, 'input':None})
            if info[3]:
                self.outputs.append(devno)
                m['output'] = devno
            if info[2]:
                self.inputs.append(devno)
                m['input'] = devno
        self.inputNames = dict((v['input'],k) for (k,v) in self.deviceMap.items()
                                if v['input'] is not None)
        self.outputNames = dict((v['output'],k) for (k,v) in self.deviceMap.items()
                                if v['output'] is not None)

    def getInput(self, dev):
        if type(dev) is int:
            return pypm.Input(self.inputs[dev])
        return pypm.Input(self.deviceMap[dev]['input'])


    def getOutput(self, dev):
        if type(dev) is int:
            return pypm.Output(self.outputs[dev])
        return pypm.Output(self.deviceMap[dev]['output'])

    def printDeviceSummary(self, printer=None):
        if printer is None:
            def printer(line):
                print line
        printer('Inputs:')
        for devno in self.inputs:
            printer('... %d %r' % (devno, self.inputNames[devno]))
        printer('Outputs:')
        for devno in self.outputs:
            printer('... %d %r' % (devno, self.outputNames[devno]))
            

pypmwrap = PypmWrapper()
initialize = init = pypmwrap.initialize
getInput = pypmwrap.getInput
getOutput = pypmwrap.getOutput
printDeviceSummary = pypmwrap.printDeviceSummary

FUNCTIONS = {}

g = globals()
def a(name, v):
    g[name] = v
    FUNCTIONS[v] = name
    __all__.append(name) 

for i in range(16):
    no = i + 1
    a('NOTEOFF_CHAN%d' % no, 0x80 + i)
    a('NOTEON_CHAN%d' % no, 0x90 + i)
    a('POLYAFTERTOUCH_CHAN%d' % no, 0xA0 + i)
    a('CONTROLCHANGE_CHAN%d' % no, 0xB0 + i)
    a('PROGRAMCHANGE_CHAN%d' % no, 0xC0 + i)
    a('CHANAFTERTOUCH_CHAN%d' % no, 0xD0 + i)
    a('PITCHWHEEL_CHAN%d' % no, 0xE0 + i)

a('SYSTEMEXCL', 0xf0)
a('MTC_QFRAME', 0xf1)
a('SONGPOSPOINTER', 0xf2)
a('SONGSELECT', 0xF3)
a('RESERVED1', 0xF4)
a('RESERVED2', 0xF5)
a('TUNEREQ', 0xF6)
a('EOX',  0xF7)
a('TIMINGCLOCK', 0xF8)
a('RESERVED3', 0xF9)
a('START',  0xFA)
a('CONTINUE', 0xFB)
a('STOP', 0xFC)
a('ACTIVESENSING', 0xFE)
a('SYSTEMRESET', 0xFF)

class MidiDispatcher(object):

    def __init__(self, midiInput, handlers, clock=None):
        self.clock = getClock(clock)
        self.midiInput = midiInput
        self.handlers = handlers

    def start(self):
        self._event = self.clock.schedule(self).startLater(1, 1/96.)

    def __call__(self):
        for message in self.midiInput.Read(32):
            for call in self.handlers:
                call(message)


class DemoHandler(object):

    def __init__(self, instr):
        self.instr = instr

    def __call__(self, message):
        try:
            packet, ms = message
            func, arg1, arg2, wth = packet
            if func == NOTEON_CHAN1:
                self.instr.playnote(arg1, arg2)
            elif func == NOTEOFF_CHAN1:
                self.instr.stopnote(arg1)
            else:
                func = FUNCTIONS.get(func, '?')
                log.msg('Ingoring midi function: %s' % func)
        except:
            f = failure.Failure()
            log.err(f)

class ClockSender(object):

    def __init__(self, midiOut, clock=None):
        self.clock = getClock(clock)
        self.midiOut = midiOut
        self._started = False

    def start(self):
        self._event = self.clock.schedule(self).startLater(1, 1/96.)

    def __call__(self):
        if not self._started:
            self.midiOut.Write([[[START], pypm.Time()]])
            self._started = True
        self.midiOut.Write([[[TIMINGCLOCK], pypm.Time()]])



