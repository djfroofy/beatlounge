#!/usr/bin/env python
import random
import fluidsynth
import logging
from copy import copy

logging.basicConfig(level=logging.DEBUG)

from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from txbeatlounge import constants
from txbeatlounge.generators import pattern1_gen, kick_gen, rising_gen
from txbeatlounge.utils import windex, midi_to_letter


fs = fluidsynth.Synth()
fs.start('coreaudio') # 'jack' ... make python settings module?


class Instrument(object):

    def __init__(self, *args, **kwargs):
        self.sf2 = kwargs['sf2path']
        self.channel = kwargs.get('channel', 0)
        self.fs = fs
        self.sfid = self.fs.sfload(self.sf2)

        super(Instrument, self).__init__()

    def __str__(self, *args, **kwargs):
        return '%s instrument on channel %s, sfid: %s' % (self.sf2, self.channel, self.sfid)

    def select_program(self):
        self.fs.program_select(self.channel, self.sfid, 0, 0)

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

    def __init__(self, *args, **kwargs):
        self.e = args[0]
        self.e.select_program()
        self.num = kwargs.get('number') or 128
        self.ones = kwargs.get('ones') or [128, 64, 32, 16, 8, 4]
        self.gen = kwargs.get('gen') or kick_gen
        self.volume = kwargs.get('volume') or 50 # between 30 and 97
        self.humanize = kwargs.get('humanize') or 10 # between 0 and 30

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

    def __init__(self, *args, **kwargs):
        super(PatternGenerator, self).__init__(*args, **kwargs)
        self.gen = kwargs.get('gen') or pattern1_gen
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
    chord_gen = self.random_chord_gen()
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

    def chord_gen(self):
        while True:
            c = copy(self.chords)
            while c:
                yield c.pop()

    def random_chord_gen(self):
        while True:
            yield random.choice(self.chords)


class BeatGenerator(BaseGenerator):

    def __init__(self, *args, **kwargs):
        super(BeatGenerator, self).__init__(*args, **kwargs)
        self.midi_noteweights = kwargs.get('midi_noteweights') or [(47, 10),(48, 10),(49, 10),(50, 10),(51, 10),(52, 10)]
        logging.debug('instantiated BeatGenerator with: %s, %s, %s, %s' % (self.e, self.num, self.ones, self.midi_noteweights))

    def choose_one(self):
        return windex(self.midi_noteweights)

    @property
    def all_midi_notes(self):
        return sorted([i[0] for i in self.midi_noteweights])


class KickGenerator(BaseGenerator):

    pass


