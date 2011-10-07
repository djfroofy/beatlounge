import time
import wave

from warnings import warn
try:
    import pyaudio
except ImportError:
    warn('(bl.wavplayer) requirement pyaudio not available - try installing')
    pyaudio = None

from twisted.python import log
from twisted.internet import reactor as globalReactor
from twisted.internet.threads import deferToThread
from twisted.internet.task import coiterate

from bl.debug import DEBUG
from bl.utils import getClock


DEFAULT_CHUNK_SIZE = 4096 / 2


__all__ = ['PyAudioManager', 'WavPlayer']


class PyAudioManager:

    pyaudio = None

    @classmethod
    def init(cls):
        """
        An idempodent init for pyaudio runtime.
        """
        if cls.pyaudio is None:
            cls.pyaudio = pyaudio.PyAudio()
        return cls.pyaudio


class WavPlayer:

    volume = 1

    def __init__(self, filename, chunkSize=DEFAULT_CHUNK_SIZE, clock=None):
        self._filename = filename
        wf = self.wavinput = wave.open(self._filename, 'rb')
        self.clock = getClock(clock)
        self.chunkSize = chunkSize
        self._playing = False
        p = PyAudioManager.init()
        self.stream = s = p.open(
                format = p.get_format_from_width(wf.getsampwidth()),
                channels = wf.getnchannels(),
                rate = wf.getframerate(),
                output = True)
        if DEBUG:
            log.msg('WavPlayer: %s rate=%s channels=%s' % (
                    filename, wf.getframerate(), wf.getnchannels()))

    def play(self, loop=False):
        if self._playing:
            return
        self._playing = True
        return coiterate(self._play(loop))

    def _play(self, loop):
        while self._playing:
            data = self.wavinput.readframes(self.chunkSize)
            while data and self._playing:
                if DEBUG:
                    log.msg('write available: %s' % self.stream.get_write_available())
                if self.stream.get_write_available():
                    self.stream.write(data)
                    data = self.wavinput.readframes(self.chunkSize)
                    yield data
            if loop and self._playing:
                self.wavinput.setpos(0)
            else:
                break
        self._playing = False

    def seek(self, position=0):
        self.wavinput.setpos(position)

    def stop(self):
        self._playing = False

    def close(self):
        self.stream.close()
        self.wavinput.close()





