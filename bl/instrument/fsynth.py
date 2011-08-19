import os
import random
from warnings import warn


from twisted.python import log

from fluidsynth import Synth


__all__ = [ 'SynthRouter', 'SynthPool', 'StereoPool', 'QuadPool', 'NConnectionPool',
            'Instrument', 'MultiInstrument', 'Layer', 'suggestDefaultPool' ]


class SynthRouter:

    def __init__(self, *p, **synth_factories):
        if not synth_factories:
            synth_factories = p[0]
        self.connections = cx = {}
        cx.update(synth_factories)

    def __getitem__(self, key):
        return self.connections[key]


class SynthPool:

    def __init__(self, router, audiodev=None):
        self.router = router
        self.pool = {}
        self.settings = {}
        self._channel_gen = {}
        self.audiodev = audiodev

    def bindSettings(self, connection, gain=0.5, samplerate=44100):
        self.settings[connection] = (gain, samplerate)

    def startSynths(self):
        for connection in self.pool:
            fs = self.pool[connection]
            fs.start(self.audiodev)

    def synthObject(self, connection=0):
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
            #if self.reactor.running:
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


def MonoPool(audiodev):
    router = SynthRouter(mono=Synth)
    return SynthPool(router, audiodev=audiodev)

def StereoPool(audiodev):
    router = SynthRouter(left=Synth, right=Synth, mono=Synth)
    return SynthPool(router, audiodev=audiodev)


def QuadPool(audiodev):
    router = SynthRouter(fleft=Synth, fright=Synth, bleft=Synth, bright=Synth, mono=Synth)
    return SynthPool(router, audiodev=audiodev)

def NConnectionPool(audiodev, *p, **synth_factories):
    router = SynthRouter(*p, **synth_factories)
    return SynthPool(router, audiodev=audiodev)


defaultPool = None

CC_VIBRATO = 1
CC_VOLUME = 7
CC_PAN = 10
CC_EXPRESSION = 11
CC_SUSTAIN = 64
CC_REVERB = 91
CC_CHORUS = 93


class ChordPlayerMixin(object):

    def playchord(self, notes, velocity=80):
        for note in notes:
            self.playnote(note, velocity)

    def stopchord(self, notes):
        for note in notes:
            self.stopnote(note)

    def stopall(self):
        for note in range(128):
            self.stopnote(note)


class Instrument(ChordPlayerMixin):

    def __init__(self, sfpath, synth=None, connection=0,
                 channel=None, bank=0, preset=0, pool=None):
        if pool is None:
            pool = defaultPool
        if synth is None:
            synth = pool.synthObject(connection=connection)
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
        self.sfid = sfid
        self.channel = channel

    def cap(self, maxVelocity):
        self._max_velocity = maxVelocity

    def playnote(self, note, velocity=80):
        velocity = min(velocity, self._max_velocity)
        self.synth.noteon(self.channel, note, velocity)

    def stopnote(self, note):
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


class Layer(ChordPlayerMixin):

    MIDI = dict([[n,n] for n in range(128)])

    def __init__(self, instruments):
        self.instruments = []
        for entry in instruments:
            if type(entry) in (tuple, list):
                self.instruments.append((entry[0], dict(self.MIDI)))
                self.instruments[-1][1].update(entry[1])
            else:
                self.instruments.append((entry, dict(self.MIDI)))

    def playnote(self, note, velocity=80):
        for (instr, mapping) in self.instruments:
            realNote = mapping.get(note, None)
            if realNote is None:
                continue
            instr.playnote(realNote, velocity)

    def stopnote(self, note):
        for (instr, mapping) in self.instruments:
            realNote = mapping.get(note, None)
            if realNote is None:
                continue
            instr.stopnote(realNote)


def suggestDefaultPool(pool):
    global defaultPool
    defaultPool = pool

def initialize(channels=1, audiodev='jack'):
    synths = dict( (n, Synth) for n in range(channels) )
    pool = NConnectionPool(audiodev, synths)
    suggestDefaultPool(pool)
    log.msg('initialized pool: %s'% pool)
    return pool





