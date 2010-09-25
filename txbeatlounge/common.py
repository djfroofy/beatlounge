import random
import logging
from copy import copy

logging.basicConfig(level=logging.DEBUG)

from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from txbeatlounge import constants
from txbeatlounge.generators import pattern1_gen, kick_gen, rising_gen
from txbeatlounge.utils import windex, midi_to_letter

def channels():
    channel = 0
    while 1:
        yield channel
        channel += 1
channels = channels()

class Instrument(object):

    def __init__(self, sf2path=None, reactor=None, channel=None, preset=0, **kw):
        if reactor is None:
            from txbeatlounge.internet import reactor
        self.reactor = reactor
        self.sf2 = sf2path
        if channel is None:
            channel = channels.next()
        self.channel = channel
        self.preset = preset
        reactor.callWhenRunning(self.start)

    def start(self):
        self.fs = self.reactor.synth
        self.sfid = self.fs.sfload(self.sf2)
        self.select_program()

    def __str__(self, *args, **kwargs):
        if not hasattr(self, 'fs'):
            return '%s instrument (stopped)' % self.sf2
        return '%s instrument on channel %s, sfid: %s' % (self.sf2, self.channel, self.sfid)

    def select_program(self, bank=0, preset=None):
        if preset is None:
            preset = self.preset
        self.fs.program_select(self.channel, self.sfid, bank, preset)

    def stopall(self):
        for n in range(128):
            self.fs.noteoff(self.channel, n)

    def playchord(self, notes, vol=50):
        for n in notes:
            self.playnote(n, vol)

    def stopchord(self, notes):
        for n in notes:
            self.fs.noteoff(self.channel, n)

    def playnote(self, n, vol=50):
        self.fs.noteon(self.channel, n, vol)

    def stopnote(self, n):
        self.fs.noteoff(self.channel, n)

    def on_octaves(self, note, vol=30, up=0):
        '''Turns on 60, 48... for note=60'''

        if up:
            while note <= 127:
                self.fs.noteon(self.channel, note, vol)
                note += 12

        else:
            while note >= 0:
                self.fs.noteon(self.channel, note, vol)
                note -= 12

    def off_octaves(self, note, up=1):
        '''Turns of 60, 72... for note=60'''

        if up:
            while note <= 127:
                self.fs.noteoff(self.channel, note)
                note += 12

        else:
            while note >= 0:
                self.fs.noteoff(self.channel, note)
                note -= 12


class BaseGenerator(object):

    def __init__(self, instrument, number=128, ones=(128, 64, 32, 16, 8, 4),
                 gen=None, volume=50, humanize=10, **kw):
        self.e = instrument
        #self.e.select_program()
        self.num = number
        self.ones = ones
        self.gen = gen or kick_gen
        self.volume = volume
        self.humanize = humanize # between 0 and 30

    def __str__(self):
        return '%s, %s, %s, %s' % (self.e, self.number, self.ones, self.gen)

    def __call__(self):
        return iter(self)

    def __iter__(self):
        return self.gen(self)

    def get_volume(self, offset=0):
        guess = random.randrange(self.volume-self.humanize, self.volume + self.humanize)
        return max([0, min([127, guess+offset])])

    @property
    def all_midi_notes(self):
        notes = []
        for n in self.notes:
            notes.extend(getattr(constants, n))
        return sorted(notes)

    @property
    def notes(self):
        return NotImplementedError('subclasses must provide, self.notes, a list of A/B/C/Df')



class PatternGenerator(BaseGenerator):

    def __init__(self, instrument, **kwargs):
        kwargs['gen'] = kwargs.get('gen', pattern1_gen)
        super(PatternGenerator, self).__init__(instrument, **kwargs)
        self.noteweights = kwargs.get('noteweights') or [('C', 20), ('E', 15), ('G', 17), ('A', 12)]

    @property
    def notes_weighted(self):
        return ''.join([i[0]*i[1] for i in self.noteweights])

    @property
    def notes(self):
        return [i[0] for i in self.noteweights]

    def get_random_note(self):
        note = random.choice(getattr(constants, windex(self.noteweights)))
        #logging.debug('random note: %s' % midi_to_letter(note))
        return note


def chords1_gen(self):
    chord_gen = self.chord_gen()
    while True:
        for i in range(self.num):
            for i in range(len(self.chords)):
                self.e.stopall()
                self.e.playchord(self.chord_to_midi(chord_gen.next()), self.get_volume())
                yield

def random_chords_gen(self):
    chord_gen = self.chord_gen()
    while True:
        for i in range(self.num):
            for i in range(len(self.chords)):
                self.e.stopall()
                self.e.playchord(self.chord_to_midi(chord_gen.next()), self.get_volume())
                yield


class ProgressionGenerator(BaseGenerator):

    def __init__(self, *args, **kwargs):
        super(ProgressionGenerator, self).__init__(*args, **kwargs)
        self.chords = kwargs.get('chords') or [('C', 'E', 'G'), ('A', 'C', 'E')]
        self.gen = kwargs.get('gen') or random_chords_gen

    def notes(self):
        notes = []
        for c in self.chords:
            notes.extend(list(c))
        return set(notes)

    def chord_to_midi(self, chord):
        notes = []
        for n in chord:
            notes.extend(getattr(constants, n))
        return notes

    def random_note_from_chord(self, chord):
        return random.choice(self.chord_to_midi(chord))

    def chord_gen(self):
        while True:
            c = copy(self.chords)
            c.reverse()
            while c:
                yield c.pop()

    def random_chord_gen(self):
        while True:
            yield random.choice(self.chords)



class BeatGenerator(BaseGenerator):

    def __init__(self, instrument, **kwargs):
        super(BeatGenerator, self).__init__(instrument, **kwargs)
        self.midi_noteweights = kwargs.get('midi_noteweights') or [(47, 10),(48, 10),(49, 10),(50, 10),(51, 10),(52, 10)]
        logging.debug('instantiated BeatGenerator with: %s, %s, %s, %s' % (self.e, self.num, self.ones, self.midi_noteweights))

    def choose_one(self):
        return windex(self.midi_noteweights)

    @property
    def all_midi_notes(self):
        return sorted([i[0] for i in self.midi_noteweights])



def bass_gen(self):
    note_gen = self.random_note_gen()
    while True:
        for i in range(self.num):
            if random.random() < .8:
                self.e.stopall()
                if random.random() < .9:
                    self.e.playnote(note_gen.next(), self.get_volume())
            yield


class BassLineGenerator(BeatGenerator):

    def __init__(self, instrument, **kwargs):
        kwargs['gen'] = kwargs.get('gen', bass_gen)
        super(BassLineGenerator, self).__init__(instrument, **kwargs)
        self.midi_noteweights = kwargs.get('midi_noteweights') or [(36,10),(33,8),(40, 8),(31, 5),(43,5),(47,2),(48,5),(50,2),(53,1),(55,3),(60,4)]

    def note_gen(self):
        while True:
            c = copy(self.midi_noteweights)
            while c:
                yield c.pop()[0]

    def random_note_gen(self):
        while True:
            yield windex(self.midi_noteweights)


class KickGenerator(BaseGenerator):

    pass


