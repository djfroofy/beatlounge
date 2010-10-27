import random
import logging
import warnings
from copy import copy

logging.basicConfig(level=logging.DEBUG)

from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from txbeatlounge import constants
# TODO make all compositions import properly their imports :/
from txbeatlounge.generators import *
from txbeatlounge.utils import windex, midi_to_letter

def channels():
    channel = 0
    while 1:
        yield channel
        channel += 1
channels = channels()

class Instrument(object):
    '''A fluidsynth instrument from an sf2path'''

    def __init__(self, sf2path=None, reactor=None, channel=None, preset=0, **kw):
        warnings.warn('txbeatlounge.common.Instrument is deprecated; '
                      'use txbeatlounge.instrument.fsynth.Instrument instead')
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

import sndobj
import math
import uuid

class SndObjInstrument(object):
    '''# basically an oscillator and a filter'''

    def __init__(self, name, driver='jack'):
        self.amp = .01
        self.tab = sndobj.HarmTable(16384, 25, sndobj.SQUARE)
        self.env = sndobj.Interp(0, 0, 0.02)
        self.osc = sndobj.Oscili(self.tab, 440, 0, None, self.env)
        self.fil = sndobj.Lp(100,0.5,self.osc)
        #self.outp = sndobj.SndRTIO(self.fil)
        if driver == 'jack':
            self.outp = sndobj.SndJackIO(name) #TODO jack_client_new is deprecated
            self.outp.SetOutput(1,self.osc)
            self.outp.SetOutput(2,self.osc)
        else:
            raise NotImplementedError('currently you must use jack to use a SndObjInstrument')
        #self.thread = sndobj.SndThread(0, None, self.outp)
        self.thread = sndobj.SndThread() #0, None, self.outp)
        self.thread.AddObj(self.env)
        self.thread.AddObj(self.osc)
        self.thread.AddObj(self.fil)
        self.thread.AddObj(self.outp, sndobj.SNDIO_OUT)
        self.thread.ProcOn()

        self.is_on = False

    def output(self):
       sig = self.fil.Output(0)
       return abs(sig)

    def set_freq(self,freq):
       self.osc.SetFreq(freq)

    def set_amp(self,amp):
       self.amp = amp
       self.osc.SetAmp(self.amp)
       self.fil.SetFreq(self.amp*0.5, None)

    def on(self):
        self.is_on = True
        self.env.SetCurve(0,self.amp)
        self.env.Restart()

    def off(self):
        self.is_on = False
        self.env.SetCurve(self.amp, 0)
        self.osc.SetAmp(0, self.env)
        self.env.Restart()


class MultiOscillator(object):

    pass



def slider(osc):
    while True:
        for i in range(881):
            osc.SetFreq(i)
            time.sleep(.0001)
            yield
        for i in range(881)[::-1]:
            osc.SetFreq(i)
            time.sleep(.0001)
            yield

def volume_warb(osc):
    while True:
        for i in range(0,100000):
            osc.SetAmp(i*.0001)
            time.sleep(.0001)
            yield
        for i in range(0,100000)[::-1]:
            osc.SetAmp(i*.0001)
            time.sleep(.0001)
            yield


