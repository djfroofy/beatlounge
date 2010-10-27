
from fluidsynth import Synth


class SynthRouter:

    def __init__(self, **synth_factories):
        self.connections = cx = {}
        cx.update(synth_factories)

    def __getitem__(self, key):
        return self.connections[key]


class SynthPool:

    def __init__(self, router, reactor=None, audiodev=None):
        self.router = router
        self.pool = {}
        self.settings = {}
        self._channel_gen = {}
        if reactor is None:
            from txbeatlounge.scheduler2 import clock as reactor
        self.reactor = reactor
        if audiodev is None:
            self.audiodev = reactor.synthAudioDevice
        self.reactor.callWhenRunning(self.startSynths)

    def bindSettings(self, connection, gain=0.5, samplerate=44100):
        self.settings[connection] = (gain, samplerate)

    def startSynths(self):
        for connection in self.pool:
            fs = self.pool[connection]
            #print 'starting synth %s with device %s' % (fs, self.audiodev)
            fs.start(self.audiodev)

    def synthObject(self, connection='mono'):
        if connection not in self.router.connections:
            raise ValueError('No connection \'%s\' in router' % connection)
        if connection in self.pool:
            fs = self.pool[connection]
        else:
            gain, samplerate = self.settings.get(connection, (0.5, 44100))
            fs = self.router.connections[connection](gain=gain, samplerate=samplerate)
            def seq():
                curr = 0
                while 1:
                    yield curr
                    curr += 1
            self._channel_gen[fs] = seq()
            self.pool[connection] = fs
            if self.reactor.running:
                #print 'premptively starting synth object %r with audio dev %s' % (
                #    fs, self.audiodev)
                fs.start(self.audiodev)
        return fs

    def loadSoundFont(self, synth, sf2path, channel=None, bank=0, preset=0):
        if channel is None:
            channel = self._channel_gen[synth].next()
        sfid = synth.sfload(sf2path)
        synth.program_select(channel, sfid, bank, preset)
        return sfid, channel
 

    def connectInstrument(self, synth, instr, sfpath=None,
                         channel=None, bank=0, preset=0, sfid=None):
        if sfid is not None:
            return instr.registerSoundfont(sfid, channel or 0)
        sfid, channel = self.loadSoundFont(synth, sfpath, channel, bank, preset)
        instr.registerSoundfont(sfid, channel)



def StereoPool():
    router = SynthRouter(left=Synth, right=Synth, mono=Synth)
    return SynthPool(router)


def QuadPool():
    router = SynthRouter(fleft=Synth, fright=Synth, bleft=Synth, bright=Synth, mono=Synth)
    return SynthPool(router)

def NConnectionPoool(**synth_factories):
    router = SynthRouter(**synth_factories)
    return SynthPool(router)


defaultPool = StereoPool()

class Instrument(object):
    
    def __init__(self, sfpath, synth=None, connection='mono',
                 channel=None, bank=0, preset=0, pool=None):
        if pool is None:
            pool = defaultPool 
        if synth is None:
            synth = pool.synthObject(connection=connection)
        self.synth = synth
        pool.connectInstrument(self.synth, self, sfpath, channel=channel,
                               bank=bank, preset=preset)
        self._max_velocity = 127     

    def registerSoundfont(self, sfid, channel):
        #print 'registered sound font', self.synth, sfid, channel
        self.sfid = sfid
        self.channel = channel

    
    def cap(self, maxVelocity):
        self._max_velocity = maxVelocity

    def playnote(self, note, velocity):
        velocity = min(velocity, self._max_velocity)
        #print 'playing note', self.synth, self.channel, note, velocity
        self.synth.noteon(self.channel, note, velocity)

    def stopnote(self, note):
        #print 'stopping note', self.synth, self.channel, note
        self.synth.noteoff(self.channel, note)

    def playchord(self, notes, velocity):
        for note in notes:
            self.playnote(note, velocity)

    def stopchord(self, notes):
        for note in notes:
            self.stopnote(note)

    def stopall(self):
        for note in range(128):
            self.stopnote(note)


def suggestDefaultPool(pool):
    global defaultPool
    defaultPool = pool


