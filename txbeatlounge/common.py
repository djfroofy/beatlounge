#!/usr/bin/env python
import types
import random
import logging

logging.basicConfig(level=logging.DEBUG)

import fluidsynth

from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from txbeatlounge import constants


def windex(lst):
    '''an attempt to make a random.choose() function that makes weighted choices

    accepts a list of tuples with the item and probability as a pair'''

    wtotal = sum([x[1] for x in lst])
    n = random.uniform(0, wtotal)
    for item, weight in lst:
        if n < weight:
            break
        n = n - weight
    return item

def midi_to_letter(midi):
    for l in constants.NOTES:
        if midi in getattr(constants, l):
            return l



fs = fluidsynth.Synth()
fs.start()


class Enunciator(object):

    def __init__(self, *args, **kwargs):
        self.sf2 = kwargs['sf2path']
        self.channel = kwargs.get('channel', 0)
        self.fs = fs
        self.sfid = self.fs.sfload(self.sf2)

        super(Enunciator, self).__init__()

    def __str__(self, *args, **kwargs):
        return '%s instrument on channel %s, sfid: %s' % (self.sf2, self.channel, self.sfid)

    def program_select(self, bank=0, preset=0):
        self.fs.program_select(self.channel, self.sfid, bank, preset)

    select_program = program_select

    def stopall(self):
        for n in range(128):
            self.noteoff(n)

    def playchord(self, notes, vol=50):
        for n in notes:
            self.noteon(n, vol)

    def stopchord(self, notes):
        for n in notes:
            self.noteoff(n)

    def on_octaves(self, note, vol=30, up=0):
        '''Turns on 60, 48... for note=60'''

        if up:
            while note <= 127:
                self.noteon(note, vol)
                note += 12

        else:
            while note >= 0:
                self.noteon(note, vol)
                note -= 12

    def off_octaves(self, note, up=0):
        '''Turns of 60, 72... for note=60'''

        if up:
            while note <= 127:
                self.noteoff(note)
                note += 12

            while note >= 0:
                self.noteoff(note)
                note -= 12


# Proxy normal methods taking a channel on Synth
for attr in dir(fluidsynth.Synth):
    if attr[0] == '_':
        continue
    method = getattr(fluidsynth.Synth, attr)
    if not type(method) == types.MethodType:
        continue
    if hasattr(Enunciator, attr):
        continue
    varnames = method.im_func.func_code.co_varnames
    if varnames[1:3] == ('chan', 'sfid'):
        def make_wrapper(method_name):
            def method(self, *p, **kw):
                return getattr(self.fs, method_name)(self.channel, self.sfid, *p, **kw)
            return method
        setattr(Enunciator, attr, make_wrapper(attr))
    elif varnames[1:2] == ('chan',):
        def make_wrapper(method_name):
            def method(self, *p, **kw):
                return getattr(self.fs, method_name)(self.channel, *p, **kw)
            return method
        setattr(Enunciator, attr, make_wrapper(attr))
    elif varnames[1:2] == ('sfid',):
        def make_wrapper(method_name):
            def method(self, *p, **kw):
                return getattr(self.fs, method_name)(self.sfid, *p, **kw)
            return method
        setattr(Enunciator, attr, make_wrapper(attr))
    else:
        def make_wrapper(method_name):
            def method(self, *p, **kw):
                return getattr(self.fs, method_name)(*p, **kw)
            return method
        setattr(Enunciator, attr, make_wrapper(attr))
                   

Enunciator.playnote = Enunciator.noteon
Enunciator.stopnote = Enunciator.noteoff

class PatternGenerator(object):

    def __init__(self, *args, **kwargs):
        self.e = args[0]
        #self.note = kwargs.get('note') or 'c'
        self.number = kwargs.get('number') or 128
        self.ones = kwargs.get('ones') or [128, 64, 32, 16, 8, 4, 2]
        self.noteweights = kwargs.get('noteweights') or [('C', 20), ('E', 15), ('G', 17), ('A', 12)]
        super(PatternGenerator, self).__init__()
        logging.debug('instantiated PatternGenerator with: %s, %s, %s, %s' % (self.e, self.number, self.ones, self.noteweights))

    def __str__(self):
        return '%s, %s, %s, %s' % (self.e, self.number, self.ones, self.noteweights)

    @property
    def notes_weighted(self):
        return ''.join([i[0]*i[1] for i in self.noteweights])

    @property
    def notes(self):
        return [i[0] for i in self.noteweights]

    @property
    def all_midi_notes(self):
        notes = []
        for n in self.notes:
            notes.extend(getattr(constants, n))

        return sorted(notes)

    def get_random_note(self):
        note = random.choice(getattr(constants, windex(self.noteweights)))
        logging.debug('random note: %s' % midi_to_letter(note))
        return note

    def get_generator(self):
        def gen():
            while True:
                for i in range(self.number):
                    self.e.select_program()
                    note = random.choice(self.notes)
                    notes = getattr(constants, note)
                    if not any([divmod(i, o)[1] for o in self.ones]):
                        self.e.playchord(self.all_midi_notes, 10)

                    else:
                        self.e.stopchord(self.all_midi_notes[12:])
                        self.e.playchord(notes[4:6], random.choice(range(5,35)))

                        for n in range(3):
                            self.e.playnote(self.get_random_note(), random.choice(range(10,20)))

                    logging.debug('yielding from %s' % self)
                    yield

        return gen()


