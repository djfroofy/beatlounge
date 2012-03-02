#from twisted.python import failure, log

import pypm

from bl.utils import getClock
from bl.debug import debug

__all__ = ['init', 'initialize', 'getInput', 'getOutput', 'printDeviceSummary',
           'ClockSender', 'MidiDispatcher', 'FUNCTIONS', 'ChordHandler',
           'MonitorHandler', 'NoteEventHandler']


class PypmWrapper:
    """
    Simple wrapper around pypm calls which caches inputs and outputs.
    """

    initialized = False
    inputs = []
    outputs = []
    deviceMap = {}
    inputNames = {}
    outputNames = {}
    _channels = {}

    @classmethod
    def initialize(cls):
        """
        Initialize pypm if not already initialized.
        """
        if cls.initialized:
            return
        pypm.Initialize()
        cls._gatherDeviceInfo()
        cls.initialized = True

    @classmethod
    def _gatherDeviceInfo(cls):
        for devno in range(pypm.CountDevices()):
            info = pypm.GetDeviceInfo(devno)

            insouts = {'output': None, 'input': None}
            m = cls.deviceMap.setdefault(info[1], insouts)
            if info[3]:
                cls.outputs.append(devno)
                m['output'] = devno
            if info[2]:
                cls.inputs.append(devno)
                m['input'] = devno

        cls.inputNames = dict(
                (v['input'], k) for (k, v) in cls.deviceMap.items()
                if v['input'] is not None
        )
        cls.outputNames = dict(
                (v['output'], k) for (k, v) in cls.deviceMap.items()
                if v['output'] is not None
        )

    @classmethod
    def getInput(cls, dev):
        """
        Get an input with devive number 'dev' - dev may also be string matching
        the target device. If the input was previously loaded this will return
        the cached device.
        """
        no = dev
        if isinstance(dev, basestring):
            no = cls.deviceMap[dev]['input']
        key = ('input', no)
        if key not in cls._channels:
            cls._channels[key] = pypm.Input(no)
        return cls._channels[key]

    @classmethod
    def getOutput(cls, dev):
        """
        Get output with devive number 'dev' - dev may also be string matching
        the target device. If the output was previously loaded this will return
        the cached device.
        """
        no = dev
        if isinstance(dev, basestring):
            no = cls.deviceMap[dev]['output']
        key = ('output', no)
        if key not in cls._channels:
            cls._channels[key] = pypm.Output(no)
        return cls._channels[key]

    @classmethod
    def printDeviceSummary(cls, printer=None):
        """
        Print device summary - inputs followed by outputs.
        """
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

# @cleanup
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
    """
    Dispatcher for events received from a midi input channel.

    Example usage:

        init()
        input = getInput(3)
        def debug_event(event):
            print event
        disp = MidiDispatcher(input, [debug_event, NoteOnOffHandler(instr)])
        disp.start()
    """

    def __init__(self, midiInput, handlers, clock=None):
        self.clock = getClock(clock)
        self.midiInput = midiInput
        self.handlers = handlers

    def start(self):
        """
        Start the MidiDispatcher - this will schedule an event to call
        all it's handlers every tick with any buffered events.
        """
        self._event = self.clock.schedule(self).startLater(0, 1 / 96.)

    def __call__(self):
        """
        Call all our handlers with buffered events (max of 32 per call
        are processed).
        """
        for message in self.midiInput.Read(32):
            for call in self.handlers:
                call(message)


class MidiHandler(object):

    def __call__(self, message):
        """
        Parse method and call method on self based on midi function.  For
        example, if function is NOTEON_CHAN1, this will call our method
        noteon(), etc.  If a message has a channel as part of it's function,
        this will be the first argument.  After the first optional channel
        argument, remaining positional arguments are passed to the method in
        the same order as specified in MIDI.  Not all MIDI functions need to be
        supplied or implemented in subclass.
        """
        packet, timestamp = message
        func, arg1, arg2, _pad = packet
        args = [arg1, arg2][:FUNCTION_ARITY.get(func, 0)]
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


class MonitorHandler(MidiHandler):
    """
    A simple MidiHandler which takes a mapping of channels to instruments.
    """

    def __init__(self, instrs):
        self.instrs = instrs

    def noteon(self, channel, note, velocity, timestamp):
        """
        Immediately play instrument at channel with given note and velocity.
        The timestamp is ignored. This is a noop if no instrument is mapped
        to the given channel.
        """
        self.instrs.get(channel, _DummyInstrument).playnote(note, velocity)

    def noteoff(self, channel, note, velocity, timestamp):
        """
        Immediately stop instrument at channel with given note. The velocity
        and timestamp arguments are ignored. This is a noop if no instrument
        is mapped to the given channel.
        """
        self.instrs.get(channel, _DummyInstrument).stopnote(note)

NoteOnOffHandler = MonitorHandler


class ChordHandler(MidiHandler):
    """
    A chord handler is a simple MidiHandler which recognizes chords and sends
    to its callback.

    todo: Currently this implementation doesn't care about channels; but this
    behavior should likely change in the near future.
    """

    def __init__(self, callback, sustain=False):
        """
        callback: handler to receive chords
        sustain: if True, only call our callback with noteon events
        """
        self.callback = callback
        self.sustain = sustain
        self._chord = []

    def noteon(self, channel, note, velocity, timestamp):
        """
        Add note to chord and call our callback with updated chord.

        Note that channel, velocity and timestamp arguments are ignored.
        """
        debug('noteon channel=%s note=%s velocity=%s t=%s' % (
                        channel, note, velocity, timestamp))
        if note not in self._chord:
            self._chord.append(note)
            debug('calling %s' % self.callback)
            self.callback(list(self._chord))

    def noteoff(self, channel, note, velocity, timestamp):
        """
        Remove note from chord.
        If the attribute `sustain` is `True` then we do not
        call callback with the updated chord.

        Note that channel, velocity and timestamp arguments are ignored.
        """
        debug('noteoff channel=%s note=%s velocity=%s t=%s' % (
                        channel, note, velocity, timestamp))
        if note in self._chord:
            self._chord.remove(note)
            if not self.sustain:
                debug('calling %s' % self.callback)
                self.callback(list(self._chord))


class NoteEventHandler(MidiHandler):
    """
    A generic note event handler which sends noteon/noteoff events to some
    registered callbacks.

    Note that that noteon callback should take two arguments
    (note, velocity) and noteoff callback should take one argument (note).
    """

    def __init__(self, noteonCallback, noteoffCallback):
        self.noteonCallback = noteonCallback
        self.noteoffCallback = noteoffCallback

    def noteon(self, channel, note, velocity, timestamp):
        """
        Call noteonCallback with the note and velocity.
        """
        # todo - maybe do something smarter with the timestamp
        # ... like normalize to ticks
        self.noteonCallback(note, velocity)

    def noteoff(self, channel, note, velocity, timestamp):
        """
        Call noteoffCallback with the note.
        """
        self.noteoffCallback(note)


class ClockSender(object):
    """
    A simple midi beat clock sender which can be used to synchronize external
    MIDI devices.
    """

    def __init__(self, midiOut, clock=None):
        self.clock = getClock(clock)
        self.midiOut = midiOut
        self._started = False

    def start(self):
        """
        Start the ClockSender - on the next measure begin sending MIDI beat
        clock events.  The first run will send a START and TIMINGCLOCK event.
        Subsequent calls (24 per quarter note), will send bare TIMINGCLOCK
        events.
        """
        self._event = self.clock.schedule(self).startLater(1, 1 / 96.)

    def __call__(self):
        # where are TIMINGCLOCK, START defined?
        # @cleanup
        if not self._started:
            self.midiOut.Write([[[START], pypm.Time()]])
            self._started = True
        self.midiOut.Write([[[TIMINGCLOCK], pypm.Time()]])
