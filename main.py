#!/usr/bin/env python

import random

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

import fluidsynth

fs = fluidsynth.Synth()
fs.start()

sfid = fs.sfload("sf2/example.sf2")
bass_sfid = fs.sfload("sf2/hs_magic_techno_drums.sf2")
johan_sfid = fs.sfload("sf2/Johansson_BeautifulPad.sf2")
fs.program_select(0, sfid, 0, 0)
fs.program_select(1, sfid, 0, 0)
fs.program_select(2, sfid, 0, 0)
fs.program_select(3, sfid, 0, 0)

V = VOLUME = 127

def beep():
    while 1:
        fs.noteon(0, 60, V)
        fs.noteon(0, 67, V)
        fs.noteon(0, 76, V)
        yield
        fs.noteoff(0, 60)
        fs.noteoff(0, 67)
        fs.noteoff(0, 76)
        

def durnnn(amp=0.75):
    looped = 0
    while 1:
        if divmod(looped, 3)[1] == 1:
            reactor.callLater(1, burrer.next)
            reactor.callLater(1.25, burrer.next)
        fs.noteon(1, 12, int(V * amp))
        fs.noteon(1, 48, int(V * amp))
        fs.noteon(1, 60, int(V * amp))
        yield
        fs.noteoff(1, 127)
        fs.noteoff(1, 127)
        fs.noteoff(1, 127)
        looped += 1

def schluup(amp=0.75):
    looped = 0
    while 1:
        if looped % 3 == 1:
            def crank_it():
                while 1:
                    v = int(V * random.choice([0.5, 0.75]))
                    fs.noteon(3, 90, v)
                    fs.noteon(3, 90, v)
                    fs.noteon(3, 90, v)
                    yield
                    fs.noteoff(3, 90)
                    fs.noteoff(3, 90)
                    fs.noteoff(3, 90)
            cranker = crank_it()
            lc = LoopingCall(lambda : cranker.next())
            lc.start(0.2, True)
            reactor.callLater(3.0, lc.stop)
            reactor.callLater(2.0, burrer.next)
            reactor.callLater(2.5, burrer.next)
            reactor.callLater(3.0, burrer.next)
            reactor.callLater(3.5, burrer.next)
            reactor.callLater(4.0, burrer.next)
            reactor.callLater(4.5, burrer.next)
        fs.noteon(2, 80, int(V * amp))
        fs.noteon(2, 60, int(V * amp))
        fs.noteon(2, 80, int(V * amp))
        def smooth_it():
            fs.noteon(3, 80, int(V * amp))
            fs.noteon(3, 60, int(V * amp))
            fs.noteon(3, 80, int(V * amp))
        reactor.callLater(0.25, smooth_it)
        yield
        fs.noteoff(2, 80)
        fs.noteoff(2, 60)
        fs.noteoff(2, 80)
        looped += 1


# Gorrila code end - non-gorilla code haxing begin

INIT_ID = 4 

def with_soundft(sndftid):
    """
    this is the magix shits. yoga for the piles.
    """
    next_id = with_soundft.next_id
    with_soundft.next_id += 1
    fs.program_select(next_id, sndftid, 0, 0) 
    def attach_snd_id(f):
        f.snd_id = next_id
        return f
    return attach_snd_id
with_soundft.next_id = INIT_ID


@with_soundft(bass_sfid)
def burr(amp=1.0):
    snd_id = burr.snd_id
    looped = 0
    while 1:
        fs.noteon(snd_id, 50, int(V))
        fs.noteon(snd_id, 50, int(V))
        fs.noteon(snd_id, 50, int(V))
        yield
        fs.noteoff(snd_id, 50)
        fs.noteoff(snd_id, 50)
        fs.noteoff(snd_id, 50)
        looped += 1

@with_soundft(johan_sfid)
def johan(amp=1.0):
    snd_id = burr.snd_id
    looped = 0
    while 1:
        v = int(V * random.random())
        fs.noteon(snd_id, 90, v)
        fs.noteon(snd_id, 50, v)
        fs.noteon(snd_id, 90, v)
        yield
        fs.noteoff(snd_id, 90)
        fs.noteoff(snd_id, 50)
        fs.noteoff(snd_id, 90)
        looped += 1

beeper = beep()
durnnner = durnnn()
schluuper = schluup()
burrer = burr()
johaner = johan()

beep_task = LoopingCall(lambda : beeper.next())
durnnn_task = LoopingCall(lambda : durnnner.next())
schluup_task = LoopingCall(lambda : schluuper.next())
johan_task = LoopingCall(lambda : johaner.next())
#burrer_task = LoopingCall(lambda : burrer.next())
beep_task.start(2.0, False)
durnnn_task.start(0.25, True)
schluup_task.start(6.0, False)
johan_task.start(0.25, False)
#burrer_task.start(3.0, False)
reactor.run()

