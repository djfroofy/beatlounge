
from twisted.python import failure, log

import pypm

from txbeatlounge.utils import getClock
from txbeatlounge.debug import DEBUG

__all__ = ['init', 'initialize', 'getInput', 'getOutput', 'printDeviceSummary',
           'ClockSender', 'DemoHandler', 'MidiDispatcher', 'FUNCTIONS', 'ChordHandler', ]

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
FUNCTION_ARITY = {}

g = globals()
def a(name, arity, v):
    g[name] = v
    FUNCTIONS[v] = name
    FUNCTION_ARITY[v] = arity
    __all__.append(name)

for i in range(16):
    no = i + 1
    a('NOTEOFF_CHAN%d' % no, 2, 0x80 + i)
    a('NOTEON_CHAN%d' % no, 2, 0x90 + i)
    a('POLYAFTERTOUCH_CHAN%d' % no, 2, 0xA0 + i)
    a('CONTROLCHANGE_CHAN%d' % no, 2, 0xB0 + i)
    a('PROGRAMCHANGE_CHAN%d' % no, 2, 0xC0 + i)
    a('CHANAFTERTOUCH_CHAN%d' % no, 2, 0xD0 + i)
    a('PITCHWHEEL_CHAN%d' % no, 2, 0xE0 + i)

a('SYSTEMEXCL', 2, 0xf0)
a('MTC_QFRAME', 2, 0xf1)
a('SONGPOSPOINTER', 2, 0xf2)
a('SONGSELECT', 2, 0xF3)
a('RESERVED1', 2, 0xF4)
a('RESERVED2', 2, 0xF5)
a('TUNEREQ', 2, 0xF6)
a('EOX',  2, 0xF7)
a('TIMINGCLOCK', 2, 0xF8)
a('RESERVED3', 2, 0xF9)
a('START',  2, 0xFA)
a('CONTINUE', 2, 0xFB)
a('STOP', 2, 0xFC)
a('ACTIVESENSING', 2, 0xFE)
a('SYSTEMRESET', 2, 0xFF)

del a, g

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


class MidiHandler(object):

    def __call__(self, message):
        packet, timestamp = message
        func, arg1, arg2, _pad = packet
        args = [ arg1, arg2 ][:FUNCTION_ARITY.get(func, 0)]
        args.append(timestamp)
        funcname = FUNCTIONS[func]
        tokens = funcname.split('_')
        if len(tokens) == 2:
            type, channel = tokens
            channel = int(channel[4:])
            method = getattr(self, type.lower(), None)
            if method is None:
                log.msg('No handler for midi event of type: %s' % type)
            method(channel, *args)

    def noteon(self, channel, note, velocity, timestamp):
        pass

    def noteoff(self, channel, note, velocity, timestamp):
        pass

    def polyaftertouch(self, channel, note, pressure, timestamp):
        pass


    # TODO define some others

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


class ChordHandler(MidiHandler):

    def __init__(self, callback, sustain=False):
        self.callback = callback
        self.sustain = sustain
        self._chord = []

    def noteon(self, channel, note, velocity, timestamp):
        log.msg('noteon channel=%s note=%s velocity=%s t=%s' % (channel, note, velocity, timestamp))
        if note not in self._chord:
            self._chord.append(note)
            log.msg('calling %s' % self.callback)
            self.callback(list(self._chord))

    def noteoff(self, channel, note, velocity, timestamp):
        log.msg('noteoff channel=%s note=%s velocity=%s t=%s' % (channel, note, velocity, timestamp))
        if note in self._chord:
            self._chord.remove(note)
            if not self.sustain:
                log.msg('calling %s' % self.callback)
                self.callback(list(self._chord))


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



