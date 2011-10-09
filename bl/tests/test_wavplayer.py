from itertools import cycle

from pprint import pprint

from zope.interface.verify import verifyClass, verifyObject

from twisted.trial.unittest import TestCase

try:
    from bl.wavplayer import WavPlayer, PyAudioManager, IPlayer
    from bl import wavplayer
    import pyaudio
except ImportError:
    pyaudio = None


class TestPyAudioStream:

    writeAvailable = 4092

    def __init__(self, *p, **kw):
        self.writes = []

    def write(self, data):
        self.writes.append(data)

    def get_write_available(self):
        return self.writeAvailable


class TestPyAudio:

    stream = TestPyAudioStream

    def __init__(self):
        self.opened = []

    def open(self, *a, **kw):
        self.opened.append((a,kw))
        return self.stream()
    
    def get_format_from_width(self, *a, **kw):
        return

class TestPyAudioModule:

    PyAudio = TestPyAudio


class TestWavFile:

    def __init__(self):
        self.dataGen = cycle([0])
        self.reads = []

    def readframes(self, chunkSize):
        buffer = []
        for i in range(chunkSize):
            try:
                buffer.append('%c' % self.dataGen.next())
            except StopIteration:
                pass
        d = ''.join(buffer)
        self.reads.append(d)
        return d
    
    def _noop(self):
        pass

    getsampwidth = _noop
    getnchannels = _noop
    getframerate = _noop

class TestWaveModule:

    testWavFile = TestWavFile

    def __init__(self):
        self.opened = []

    def open(self, path, mode):
        self.opened.append((path, mode))
        return self.testWavFile()


class BaseTestCase(TestCase):

    def setUp(self):
        self.patch(wavplayer, 'pyaudio', TestPyAudioModule())
        self.patch(wavplayer, 'wave', TestWaveModule())
        self.patch(PyAudioManager, 'pyaudio', None)

if not pyaudio:
    BaseTestCase.skip = 'pyaudio not available'


class PyAudioManagerTests(BaseTestCase):

    def test_initIdempotency(self):
        self.failIf(PyAudioManager.pyaudio)
        pa1 = PyAudioManager.init()
        self.assert_(pa1)
        pa2 = PyAudioManager.init()
        self.assertIdentical(pa1, pa2)
        self.assertIdentical(pa1, PyAudioManager.pyaudio)


class WavPlayerTests(BaseTestCase):

    def test_fromPath(self):
        player = WavPlayer.fromPath('file.wav')
        verifyObject(IPlayer, player)
        self.assertEquals(wavplayer.wave.opened, [('file.wav', 'rb')])


    def test_play(self):
        player = WavPlayer.fromPath('file.wav', chunkSize=10)
        player.source.wavfile.dataGen = ( i for i in range(100) )
        return self._test_play(player, player.play())


    def _test_play(self, player, d):
        def check(ignore):
            self.assertEquals(player.source.wavfile.reads, expected_reads)
            self.assertEquals(player.stream.stream.writes, expected_writes)

        expected_reads = [
                '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t',
                '\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13',
                '\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d',
                '\x1e\x1f !"#$%&\'',
                '()*+,-./01',
                '23456789:;',
                '<=>?@ABCDE',
                'FGHIJKLMNO',
                'PQRSTUVWXY',
                'Z[\\]^_`abc',
                '']
        expected_writes = [
                '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t',
                '\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13',
                '\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d',
                '\x1e\x1f !"#$%&\'',
                '()*+,-./01',
                '23456789:;',
                '<=>?@ABCDE',
                'FGHIJKLMNO',
                'PQRSTUVWXY',
                'Z[\\]^_`abc']
        return d.addCallback(check)


    def test_pauseAndResume(self):
        player = WavPlayer.fromPath('file.wav', chunkSize=10)
        player.source.wavfile.dataGen = ( i for i in range(100) )
        d = player.play()
    
        player.pause()

        def check(ignore):
            d = player.resume()
            return self._test_play(player, d)

        return d.addCallback(check) 

