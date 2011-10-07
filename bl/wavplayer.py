import wave

from warnings import warn
try:
    import pyaudio
except ImportError:
    warn('(bl.wavplayer) requirement pyaudio not available - try installing')
    pyaudio = None

from twisted.internet import reactor as globalReactor
from twisted.internet.threads import deferToThread
from twisted.internet.task import coiterate

from bl.utils import getClock


DEFAULT_CHUNK_SIZE = 8


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
        wf = self._wf = wave.open(self._filename, 'rb')
        self.clock = getClock(clock)
        self.chunkSize = chunkSize
        self._playing = False
        self._stopped = False
        p = PyAudioManager.init()
        self.stream = p.open(
                format = p.get_format_from_width(wf.getsampwidth()),
                channels = wf.getnchannels(),
                rate = wf.getframerate(),
                output = True)

    def play(self, loop=False):
        if self._playing:
            return
        self._playing = True
        deferToThread(self._play, loop)

    def _play(self, loop):
        while not self._stopped:
            data = self._wf.readframes(self.chunkSize)
            while data:
                self.stream.write(data)
                data = self._wf.readframes(self.chunkSize)
            if loop:
                self._wf.setpos(0)
            else:
                break
        self._wf.setpos(0)
        self._playing = False

    def stop(self):
        self._stopped = True

    def close(self):
        self.stream.close()
        self._wf.close()


