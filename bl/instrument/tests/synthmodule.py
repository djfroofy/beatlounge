__all__ = ['Synth']


def _nextid(id):
    while 1:
        yield id
        id += 1
nextid = _nextid(0)


class MockSynth(object):

    def __init__(self, gain=0.3, samplerate=44100):
        self.gain = gain
        self.samplerate = samplerate
        self.sfonts = {}

    def noteon(self, note, velocity):
        pass

    def noteoff(self, note):
        pass

    def sfload(self, path):
        sfid = nextid.next()
        self.sfonts[sfid] = (None, None, None, path)
        return sfid

    def program_select(self, channel, sfid, bank, preset):
        (_, _, _, path) = self.sfonts[sfid]
        self.sfonts[sfid] = (channel, bank, preset, path)

Synth = MockSynth
