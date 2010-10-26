
from twisted.trial.unittest import TestCase


from txbeatlounge.experiment.instrument import fsynth

import synthmodule

Synth = synthmodule.Synth
SynthRouter = fsynth.SynthRouter
SynthPool = fsynth.SynthPool
Instrument = fsynth.Instrument

class SynthRouterTests(TestCase):

    def setUp(self):
        self.patch(fsynth, 'Synth', Synth)


    def test_connectionsDict(self):
        router = SynthRouter(left=Synth, right=Synth)
        self.assertEquals(router.connections, {'left':Synth, 'right':Synth})
        

class TestInstrument:

    def __init__(self):
        self.sfid = None

    def registerSoundfont(self, id, channel):
        self.sfid = id
        self.channel = channel


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
        soundft = self.pool.loadSoundFont(synth, 'sound.sf2')
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

   

