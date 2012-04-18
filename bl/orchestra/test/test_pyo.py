from itertools import cycle

from twisted.trial.unittest import TestCase

from bl.scheduler import BeatClock
from bl.testlib import ClockRunner, TestReactor
from bl.orchestra.pyo import PyoPlayer


class DummyPyoObject(object):

    def __init__(self):
        self.freq = None
        self.mul = None
        self.calls = []

    def setFreq(self, freq):
        self.freq = freq
        self.calls.append(('setFreq', freq))

    def setMul(self, mul):
        self.mul = mul
        self.calls.append(('setMul', mul))

    def __dir__(self):
        return ['mul', 'freq']


class PyoPlayerTestCase(TestCase, ClockRunner):

    def setUp(self):
        self.clock = BeatClock(reactor=TestReactor())
        self.pyo = DummyPyoObject()

    def test_method_gathering(self):
        pyo = DummyPyoObject()
        player = PyoPlayer(pyo)
        self.assertEquals(player._methods,
                          {'freq': pyo.setFreq,
                           'mul': pyo.setMul})

    def test_modulation(self):
        pyo = DummyPyoObject()
        player = PyoPlayer(pyo, interval=(1, 4),
                           clock=self.clock,
                           args={'freq': cycle([1, 2, 3]).next})
        player.resumePlaying()
        self.runTicks(96)
        expected = [('setFreq', 1), ('setFreq', 2), ('setFreq', 3),
                    ('setFreq', 1), ('setFreq', 2)]
        self.assertEqual(pyo.calls, expected)
        player.updateArgs(freq=cycle([4, 5, 6]).next,
                          mul=cycle([0.25, 0.125]).next)
        pyo.calls = []
        self.runTicks(96)
        expected = [('setMul', 0.25), ('setFreq', 4), ('setMul', 0.125),
                    ('setFreq', 5), ('setMul', 0.25), ('setFreq', 6),
                    ('setMul', 0.125), ('setFreq', 4)]

    def test_tuple_coercion(self):
        pyo = DummyPyoObject()
        player = PyoPlayer(pyo, interval=(1, 1),
                           clock=self.clock,
                           args={'freq': cycle([(1, 2)]).next})
        player.resumePlaying()
        self.runTicks(96)
        expected = [('setFreq', [1, 2]), ('setFreq', [1, 2])]
        self.assertEquals(pyo.calls, expected)

    def test_updateArgs_init_chaining(self):
        pyo = DummyPyoObject()
        player = PyoPlayer(pyo, interval=(1, 4),
                           clock=self.clock).updateArgs(freq=cycle([1]).next)
        self.assert_(player.args)
