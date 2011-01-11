import os
import random
from warnings import warn

from fluidsynth import Synth

from txbeatlounge.utils import getClock

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
            from txbeatlounge.scheduler import clock as reactor
        self.reactor = reactor
        self.audiodev = audiodev
        self.reactor.callWhenRunning(self.startSynths)

    def bindSettings(self, connection, gain=0.5, samplerate=44100):
        self.settings[connection] = (gain, samplerate)

    def startSynths(self):
        if self.audiodev is None:
            self.audiodev = self.reactor.synthAudioDevice
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

CC_VIBRATO = 1
CC_VOLUME = 7
CC_PAN = 10
CC_EXPRESSION = 11
CC_SUSTAIN = 64
CC_REVERB = 91
CC_CHORUS = 93


class ChordPlayerMixin(object):

    clock = None
    strumming = False

    def strum(self, notes, velocity=80):
        v = lambda : velocity
        if callable(velocity):
            v = lambda : velocity()
        for (i, note) in enumerate(notes):
            later = 1
            self.clock.callLater(i*later, self.playnote, note, v())


    def playchord(self, notes, velocity=80):
        if self.strumming:
            return self.strum(notes, velocity)
        for note in notes:
            self.playnote(note, velocity)

    def stopchord(self, notes):
        for note in notes:
            self.stopnote(note)

    def stopall(self):
        for note in range(128):
            self.stopnote(note)


class Instrument(ChordPlayerMixin):

    def __init__(self, sfpath, synth=None, connection='mono',
                 channel=None, bank=0, preset=0, pool=None, clock=None):
        if pool is None:
            pool = defaultPool
        if synth is None:
            synth = pool.synthObject(connection=connection)
        self.clock = getClock(clock)
        self.synth = synth
        self._file = os.path.basename(sfpath)
        self.sfpath = sfpath
        self._options = dict( sfpath=sfpath, connection=connection,
                              channel=channel, bank=bank, preset=preset )
        pool.connectInstrument(self.synth, self, sfpath, channel=channel,
                               bank=bank, preset=preset)
        self._max_velocity = 127

    def __str__(self):
        return 'Instrument path=%s sfid=%s channel=%s' % (self._file, self.sfid, self.channel)

    def registerSoundfont(self, sfid, channel):
        #print 'registered sound font', self.synth, sfid, channel
        self.sfid = sfid
        self.channel = channel

    def cap(self, maxVelocity):
        self._max_velocity = maxVelocity

    def playnote(self, note, velocity=80):
        velocity = min(velocity, self._max_velocity)
        #print 'playing note', self.synth, self.channel, note, velocity
        self.synth.noteon(self.channel, note, velocity)

    def stopnote(self, note):
        #print 'stopping note', self.synth, self.channel, note
        self.synth.noteoff(self.channel, note)


    def controlChange(self, vibrato=None, volume=None, pan=None, expression=None,
                      sustain=None, reverb=None, chorus=None):
        if vibrato is not None:
            self.synth.cc(self.channel, CC_VIBRATO, vibrato)
        if pan is not None:
            self.synth.cc(self.channel, CC_PAN, pan)
        if expression is not None:
            self.synth.cc(self.channel, CC_EXPRESSION, expression) 
        if sustain is not None:
            self.synth.cc(self.channel, CC_SUSTAIN, sustain)
        if reverb is not None:
            self.synth.cc(self.channel, CC_REVERB, reverb)
        if chorus is not None:
            self.synth.cc(self.channel, CC_CHORUS, chorus)

    def pitchBend(self, value):
        self.synth.pitch_bend(self.channel, value)


class MultiInstrument(ChordPlayerMixin):

    def __init__(self, instrumentMapping, strict=True):
        self._mapping = {}
        self.instruments = []
        for (instrument, noteMapping) in instrumentMapping:
            self.instruments.append(instrument)
            for (to, from_) in noteMapping:
                if self._mapping.has_key(to):
                    msg = 'Reduant entry in instrumentMapping: %s' % to
                    if strict:
                        raise ValueError(msg)
                    else:
                        warn(msg)
                else:
                    self._mapping[to] = (instrument, from_)
        

    def playnote(self, note, velocity=80):
        instr, realNote = self._mapping.get(note, (None, None))
        if instr is None:
            return
        instr.playnote(realNote, velocity)

    def stopnote(self, note):
        instr, realNote = self._mapping.get(note, (None, None))
        if instr is None:
            return
        instr.stopnote(realNote)


def suggestDefaultPool(pool):
    global defaultPool
    defaultPool = pool


