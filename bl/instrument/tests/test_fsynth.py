from zope.interface.verify import verifyClass, verifyObject

from twisted.trial.unittest import TestCase

from bl.instrument.interfaces import IMIDIInstrument
from bl.instrument import fsynth

import synthmodule


Synth = synthmodule.Synth
SynthRouter = fsynth.SynthRouter
SynthPool = fsynth.SynthPool
Instrument = fsynth.Instrument
MultiInstrument = fsynth.MultiInstrument
Layer = fsynth.Layer


class SynthRouterTests(TestCase):

    def setUp(self):
        self.patch(fsynth, 'Synth', Synth)

    def test_connectionsDict(self):
        router = SynthRouter(left=Synth, right=Synth)
        self.assertEquals(router.connections, {'left': Synth, 'right': Synth})


class TestInstrument:

    def __init__(self):
        self.sfid = None

    def registerSoundfont(self, id, channel):
        self.sfid = id
        self.channel = channel

    def stopall(self):
        pass


class SynthPoolTests(TestCase):

    def setUp(self):
        self.router = SynthRouter(left=Synth, right=Synth, mono=Synth)
        self.pool = SynthPool(self.router)

    def tearDown(self):
        synthmodule.nextid = synthmodule._nextid(0)

    def test_synthObject_retrieval(self):
        obj = self.pool.synthObject()
        self.assertEquals(obj.gain, 0.5)
        self.assertEquals(obj.samplerate, 44100)

    def test_synthObject_idempotence(self):
        obj1 = self.pool.synthObject()
        obj2 = self.pool.synthObject()
        obj3 = self.pool.synthObject(connection='right')

        self.assertIdentical(obj1, obj2)
        self.failIfIdentical(obj1, obj3)

    def test_bindSettings(self):
        self.pool.bindSettings('left', gain=1, samplerate=1234)
        obj = self.pool.synthObject(connection='left')
        self.assertEquals(obj.gain, 1)
        self.assertEquals(obj.samplerate, 1234)
        obj = self.pool.synthObject()
        self.assertEquals(obj.gain, 0.5)
        self.assertEquals(obj.samplerate, 44100)

    def test_loadSoundFont(self):
        synth = self.pool.synthObject()
        self.pool.loadSoundFont(synth, 'sound.sf2')
        self.assertEquals(synth.sfonts, {0: (0, 0, 0, 'sound.sf2')})

    def test_connectInstrument(self):
        synth = self.pool.synthObject()
        instr = TestInstrument()
        self.pool.connectInstrument(synth, instr)
        self.assertEquals(instr.sfid, 0)
        self.assertEquals(instr.channel, 0)
        instr2 = TestInstrument()
        self.pool.connectInstrument(synth, instr2)
        self.assertEquals(instr2.sfid, 1)
        self.assertEquals(instr2.channel, 1)

    def test_connectInstrumentWithSoundFontId(self):
        synth = self.pool.synthObject()
        instr = TestInstrument()
        self.pool.connectInstrument(synth, instr, sfid=99)
        self.assertEquals(instr.sfid, 99)
        self.assertEquals(instr.channel, 0)

    def test_connectInstrumentWithChannel(self):
        synth = self.pool.synthObject()
        instr = TestInstrument()
        self.pool.connectInstrument(synth, instr, sfid=99, channel=7)
        self.assertEquals(instr.sfid, 99)
        self.assertEquals(instr.channel, 7)
        instr = TestInstrument()
        self.pool.connectInstrument(synth, instr, channel=7)
        self.assertEquals(instr.sfid, 0)
        self.assertEquals(instr.channel, 7)


class InstrumentTests(TestCase):

    def setUp(self):
        self.patch(fsynth, 'Synth', Synth)
        defaultPool = fsynth.defaultPool
        self.addCleanup(fsynth.suggestDefaultPool, defaultPool)
        fsynth.suggestDefaultPool(fsynth.StereoPool())

    def tearDown(self):
        synthmodule.nextid = synthmodule._nextid(0)

    def test_iface(self):
        verifyClass(IMIDIInstrument, Instrument)
        verifyObject(IMIDIInstrument, Instrument('sf2/instrument.sf2'))

    def test_instrumentsAreLoaded(self):
        instr1 = Instrument('sf2/instrument.sf2')
        self.assertEquals(instr1.sfid, 0)
        self.assertEquals(instr1.channel, 0)
        instr1 = Instrument('sf2/instrument2.sf2')
        self.assertEquals(instr1.sfid, 1)
        self.assertEquals(instr1.channel, 1)

    def test_instrumentIsConnectedCorrectly(self):
        fsynth.defaultPool.bindSettings('mono', gain=0.2)
        fsynth.defaultPool.bindSettings('left', gain=0.3)
        fsynth.defaultPool.bindSettings('right', gain=0.4)
        instr_mono = Instrument('sf2/instrument2.sf2')
        self.assertEquals(instr_mono.synth.gain, 0.2)
        instr_left = Instrument('sf2/instrument2.sf2', connection='left')
        self.assertEquals(instr_left.synth.gain, 0.3)
        instr_right = Instrument('sf2/instrument2.sf2', connection='right')
        self.assertEquals(instr_right.synth.gain, 0.4)


class MockInstrument:

    def __init__(self):
        self.record = []

    def noteon(self, note, velocity):
        self.record.append(('play', note, velocity))

    def noteoff(self, note):
        self.record.append(('stop', note))


class MultiInstrumentTests(TestCase):

    def setUp(self):
        self.patch(fsynth, 'Synth', Synth)
        defaultPool = fsynth.defaultPool
        self.addCleanup(fsynth.suggestDefaultPool, defaultPool)
        fsynth.suggestDefaultPool(fsynth.StereoPool())

    def test_multiInstrumentMapping(self):
        Instrument = MockInstrument
        instr1 = Instrument()
        instr2 = Instrument()
        instr3 = Instrument()
        minstr = MultiInstrument([(instr1, ((0, 43), (1, 44), (2, 46),
                                            (3, 47))),
                                 (instr2, ((4, 23), (5, 24), (6, 25))),
                                 (instr3, ((7, 43), (8, 44)))])

        minstr.noteon(0, 120)
        minstr.noteon(1, 110)
        minstr.noteon(2, 100)
        minstr.noteon(3, 90)
        minstr.noteoff(0)
        minstr.noteon(4, 80)
        minstr.noteon(8, 70)
        expected_instr1 = [('play', 43, 120), ('play', 44, 110),
                           ('play', 46, 100), ('play', 47, 90), ('stop', 43)]
        expected_instr2 = [('play', 23, 80)]
        expected_instr3 = [('play', 44, 70)]
        self.assertEquals(instr1.record, expected_instr1)
        self.assertEquals(instr2.record, expected_instr2)
        self.assertEquals(instr3.record, expected_instr3)
        instr1.record, instr2.record, instr3.record = [], [], []
        minstr.playchord([0, 5, 8], 120)
        minstr.stopchord([0, 5, 8])
        self.assertEquals(instr1.record, [('play', 43, 120), ('stop', 43)])
        self.assertEquals(instr2.record, [('play', 24, 120), ('stop', 24)])
        self.assertEquals(instr3.record, [('play', 44, 120), ('stop', 44)])
        instr1.record, instr2.record, instr3.record = [], [], []
        minstr.noteon(120, 100)
        for instr in instr1, instr2, instr3:
            self.failIf(instr.record)
        minstr.stopall()
        self.assertEquals(instr1.record, [('stop', 43), ('stop', 44),
                                          ('stop', 46), ('stop', 47)])
        self.assertEquals(instr2.record, [('stop', 23), ('stop', 24),
                                          ('stop', 25)])
        self.assertEquals(instr3.record, [('stop', 43), ('stop', 44)])


class LayerTests(TestCase):

    def setUp(self):
        self.patch(fsynth, 'Synth', Synth)
        defaultPool = fsynth.defaultPool
        self.addCleanup(fsynth.suggestDefaultPool, defaultPool)
        fsynth.suggestDefaultPool(fsynth.StereoPool())
        Instrument = MockInstrument
        self.instr1 = Instrument()
        self.instr2 = Instrument()
        self.layer = Layer([self.instr1, (self.instr2, ([24, 25],))])

    def test_instruments_initialization(self):
        midi = Layer.MIDI
        midi2 = dict(midi)
        midi2[24] = 25
        layer = self.layer
        self.assertEquals(layer.instruments[0][0], self.instr1)
        self.assertEquals(layer.instruments[0][1], midi)
        self.assertEquals(layer.instruments[1][0], self.instr2)
        self.assertEquals(layer.instruments[1][1], midi2)

    def test_noteon_noteoff(self):
        layer = self.layer
        layer.noteon(45, 127)
        layer.noteon(24, 100)
        layer.noteon(30)
        layer.noteoff(45)
        layer.noteoff(24)
        self.assertEquals(self.instr1.record,
                          [('play', 45, 127), ('play', 24, 100),
                           ('play', 30, 80), ('stop', 45), ('stop', 24)])
        self.assertEquals(self.instr2.record,
                          [('play', 45, 127), ('play', 25, 100),
                           ('play', 30, 80), ('stop', 45), ('stop', 25)])
