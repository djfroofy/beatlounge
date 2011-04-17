
from twisted.python import failure, log

import pypm

from txbeatlounge.utils import getClock
from txbeatlounge.debug import debug

__all__ = ['init', 'initialize', 'getInput', 'getOutput', 'printDeviceSummary',
           'ClockSender', 'MidiDispatcher', 'FUNCTIONS', 'ChordHandler',
           'NoteOnOffHandler' ]

class PypmWrapper:

    initialized = False
    inputs = []
    outputs = []
    deviceMap = {}
    inputNames = {}
    outputNames = {}
    _channels = {}

    @classmethod
    def initialize(cls):
        if cls.initialized:
            return
        pypm.Initialize()
        cls._gatherDeviceInfo()
        cls.initialized = True

    @classmethod
    def _gatherDeviceInfo(cls):
        for devno in range(pypm.CountDevices()):
            info = pypm.GetDeviceInfo(devno)

            m = cls.deviceMap.setdefault(info[1], {'output':None, 'input':None})
            if info[3]:
                cls.outputs.append(devno)
                m['output'] = devno
            if info[2]:
                cls.inputs.append(devno)
                m['input'] = devno
        cls.inputNames = dict((v['input'],k) for (k,v) in cls.deviceMap.items()
                                if v['input'] is not None)
        cls.outputNames = dict((v['output'],k) for (k,v) in cls.deviceMap.items()
                                if v['output'] is not None)

    @classmethod
    def getInput(cls, dev):
        no = dev
        if isinstance(dev, basestring):
            no = cls.deviceMap[dev]['input']
        key = ('input', no)
        if key not in cls._channels:
            cls._channels[key] = pypm.Input(no)
        return cls._channels[key]


    @classmethod
    def getOutput(cls, dev):
        no = dev
        if isinstance(dev, basestring):
            no = cls.deviceMap[dev]['output']
        key = ('output', no)
        if key not in cls._channels:
            cls._channels[key] = pypm.Output(no)
        return cls._channels[key]

    @classmethod
    def printDeviceSummary(cls, printer=None):
        if printer is None:
            def printer(line):
                print line
        printer('Inputs:')
        for devno in cls.inputs:
            printer('... %d %r' % (devno, cls.inputNames[devno]))
        printer('Outputs:')
        for devno in cls.outputs:
            printer('... %d %r' % (devno, cls.outputNames[devno]))


initialize = init = PypmWrapper.initialize
getInput = PypmWrapper.getInput
getOutput = PypmWrapper.getOutput
printDeviceSummary = PypmWrapper.printDeviceSummary

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
        self._event = self.clock.schedule(self).startLater(0, 1/96.)

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
                debug('No handler defined for midi event of type: %s' % type)
            method(channel, *args)

    def noteon(self, channel, note, velocity, timestamp):
        pass

    def noteoff(self, channel, note, velocity, timestamp):
        pass



class _DummyInstrument:

    @classmethod
    def playnote(cls, note, velocity):
        pass

    @classmethod
    def stopnote(cls, note):
        pass


class NoteOnOffHandler(MidiHandler):

    def __init__(self, instrs):
        self.instrs = instrs

    def noteon(self, channel, note, velocity, timestamp):
        self.instrs.get(channel, _DummyInstrument).playnote(note, velocity)

    def noteoff(self, channel, note, velocity, timestamp):
        self.instrs.get(channel, _DummyInstrument).stopnote(note)


class ChordHandler(MidiHandler):

    def __init__(self, callback, sustain=False):
        self.callback = callback
        self.sustain = sustain
        self._chord = []

    def noteon(self, channel, note, velocity, timestamp):
        debug('noteon channel=%s note=%s velocity=%s t=%s' % (channel, note, velocity, timestamp))
        if note not in self._chord:
            self._chord.append(note)
            debug('calling %s' % self.callback)
            self.callback(list(self._chord))

    def noteoff(self, channel, note, velocity, timestamp):
        debug('noteoff channel=%s note=%s velocity=%s t=%s' % (channel, note, velocity, timestamp))
        if note in self._chord:
            self._chord.remove(note)
            if not self.sustain:
                debug('calling %s' % self.callback)
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



