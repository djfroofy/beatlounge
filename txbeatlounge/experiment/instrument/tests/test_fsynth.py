
from twisted.trial.unittest import TestCase


from txbeatlounge.experiment.instrument import fsynth

import synthmodule

Synth = synthmodule.Synth

SynthRouter = fsynth.SynthRouter
SynthPool = fsynth.SynthPool


class SynthRouterTests(TestCase):

    def setUp(self):
        self.patch(fsynth, 'Synth', Synth)


    def test_connectionsDict(self):
        router = SynthRouter(left=Synth, right=Synth)
        self.assertEquals(router.connections, {'left':Synth, 'right':Synth})
        

class TestInstrument:

    def __init__(self):
        self.sfid = None

    def registerId(self, id):
        self.sfid = id


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
        instr2 = TestInstrument()
        self.pool.connectInstrument(synth, instr2)
        self.assertEquals(instr2.sfid, 1)

    def test_connectInstrumentWithSoundFontId(self):
        synth = self.pool.synthObject()
        instr = TestInstrument()
        self.pool.connectInstrument(synth, instr, sfid=99)
        self.assertEquals(instr.sfid, 99)




