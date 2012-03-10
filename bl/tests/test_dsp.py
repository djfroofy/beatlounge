from twisted.trial.unittest import TestCase

try:
    from bl import dsp
except ImportError:
    dsp = None


class FakeServer:

    calls = []

    def __init__(self, **kw):
        FakeServer.calls.append(('__init__', kw))

    def start(self, **kw):
        FakeServer.calls.append(('start', kw))

    def stop(self, **kw):
        FakeServer.calls.append(('stop', kw))

    def boot(self, **kw):
        FakeServer.calls.append(('boot', kw))

    def shutdown(self, **kw):
        FakeServer.calls.append(('shutdown', kw))

    @classmethod
    def reset(cls):
        cls.calls = []


class PyoServerTests(TestCase):

    def setUp(self):
        FakeServer.reset()
        self.patch(dsp, 'Server', FakeServer)
        self.patch(dsp.PyoServer, '_server', None)


    def testStart(self):
        dsp.startPyo()
        self.assertEquals(FakeServer.calls, [('__init__', {'audio':'jack'}), ('boot', {}), ('start',{})])

    def testStartWithArguments(self):
        dsp.startPyo(audio='alsa', nchnls=4)
        self.assertEquals(FakeServer.calls, [('__init__', {'audio':'alsa', 'nchnls':4}), ('boot', {}), ('start',{})])


    def testStartIsIdempotent(self):
        dsp.startPyo()
        server  = dsp.PyoServer._server
        dsp.startPyo()
        self.assertIdentical(dsp.PyoServer._server, server) 

    def testStop(self):
        dsp.startPyo()
        FakeServer.reset()
        dsp.stopPyo()
        self.assertEquals(FakeServer.calls, [('stop',{})])
        
    def testShutdown(self):
        dsp.startPyo()
        FakeServer.reset()
        dsp.shutdownPyo()
        self.assertEquals(FakeServer.calls, [('stop',{}),('shutdown',{})])
    
    def testRestart(self):
        dsp.startPyo()
        FakeServer.reset()
        dsp.restartPyo()
        self.assertEquals(FakeServer.calls, [('stop',{}),('start',{})])
    
    def testReboot(self):
        dsp.startPyo()
        FakeServer.reset()
        dsp.rebootPyo()
        self.assertEquals(FakeServer.calls, [('stop',{}),('shutdown',{}),('boot',{}),('start',{})])

    def testCannotDoShitUntilServerStarts(self):
        self.assertRaises(AssertionError, dsp.stopPyo) 
        self.assertRaises(AssertionError, dsp.shutdownPyo) 
        self.assertRaises(AssertionError, dsp.restartPyo) 
        self.assertRaises(AssertionError, dsp.rebootPyo) 


if dsp is None:        
    PyoServerTests.skip = 'dsp module not available - skipping'

