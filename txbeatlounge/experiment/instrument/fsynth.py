
from fluidsynth import Synth


class SynthRouter:

    def __init__(self, **synth_factories):
        self.connections = cx = {}
        cx.update(synth_factories)

class SynthPool:

    def __init__(self, router):
        self.router = router
        self.pool = {}
        self.settings = {}


    def bindSettings(self, connection, gain=0.5, samplerate=44100):
        self.settings[connection] = (gain, samplerate)

    def synthObject(self, connection='mono'):
        if connection not in self.router.connections:
            raise ValueError('No connection \'%s\' in router' % connection)
        if connection in self.pool:
            fs, seq = self.pool[connection]
            nom = seq.next()
        else:
            gain, samplerate = self.settings.get(connection, (0.5, 44100))
            fs = self.router.connections[connection](gain=gain, samplerate=samplerate)
            nom = 0
            def seq():
                curr = 1
                while 1:
                    yield curr
                    curr += 1
            self.pool[connection] = (fs, seq())
        return fs


    def loadSoundFont(self, synth, sf2path, channel=0, bank=0, preset=0):
        sfid = synth.sfload(sf2path)
        synth.program_select(channel, sfid, bank, preset)
        return sfid
 

    def connectInstrument(self, synth, instr, sfpath=None, channel=0, bank=0, preset=0, sfid=None):
        if sfid is not None:
            return instr.registerId(sfid)
        sfid = self.loadSoundFont(synth, sfpath, channel, bank, preset)
        instr.registerId(sfid)

class Instrument(object):
    
    def __init__(self, sf2path, synthObject=None, preset=0, bank=0, reactor=None):
        if reactor is None:
            from txbeatlounge.scheduler2 import clock as reactor
        self.reactor = reactor


