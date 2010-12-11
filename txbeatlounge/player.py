import random

from zope.interface import Interface, Attribute, implements

from twisted.python import log

from txbeatlounge.debug import DEBUG

__all__ = [ 'IPlayer', 'INotePlayer', 'IChordPlayer',
            'BasePlayer', 'Player', 'NotePlayer', 'ChordPlayer',
            'N', 'R', 'generateSounds', 'snd', 'rp', 'randomPhrase',
            'randomWalk', 'rw', 'StepSequencer']


class IPlayer(Interface):
    instr = Attribute('Instrument that provides playnote(note, velocity)')
    velocity = Attribute('IFilter to get current velocity')
    stop = Attribute('Callable to get stop time on current note/chord, or None '
                     'for non-stop')


class INotePlayer(IPlayer):
    noteFactory = Attribute('Callable to get the current note to play')


class IChordPlayer(IPlayer):
    chordFactory = Attribute('Callable to get the current chord to play')   


class IPlayable(Interface):
    
    def startPlaying(node=None):
        pasobjects

    def stopPlayering(node=None):
        pass

    
class PlayableMixin(object):
    implements(IPlayable)

    def startPlaying(self, node=None):
        self._playSchedule = self.clock.schedule(self.play).startLater(
            1, self.interval)
   
    def stopPlaying(self, node=None):
        se = self._playSchedule
        # Stop one tick before the next measure -
        # This means if you try to schedule something at a granularity of 1
        # you're kind of screwed - though I'm not sure of a nicer way to prevent
        # the non-determinism on something stopping before it starts again when
        # the stop and start are scheduled for the same tick
        ticks = self.meter.ticksPerMeasure - 1
        self.clock.callLater(ticks, se.stop)
        self._playSchedule = None


class BasePlayer(PlayableMixin):
    implements(IPlayer)

    def __init__(self, instr, velocity, stop, clock=None, interval=None, meter=None):
        self.instr = instr
        self.velocity = velocity
        if isinstance(stop, int):
            s = stop
            stop = lambda : s
        self.stop = stop
        if clock is None:
            from txbeatlounge.scheduler import clock
        self.clock = clock
        self.interval = interval
        self._scheduledEvent = None
        if meter is None:
            meter = self.clock.meters[0]
        self.meter = meter


    def play(self):
        v, o = self.velocity(110, None)
        n = self._next()
        if callable(n):
            n = n()
        if n is None:
            return
        if DEBUG:
            log.msg('%s %s %s %s' % (self.instr, n,
                    self.clock.meters[0].beat(self.clock.ticks), v))
        self._on_method(n, v)
        stop = self.stop()
        if stop is not None:
            self.clock.callLater(stop, self._off_method, n)


class NotePlayer(BasePlayer):
    implements(INotePlayer)

    def __init__(self, instr, noteFactory, velocity, stop=lambda : None,
                 clock=None, interval=None):
        super(NotePlayer, self).__init__(instr, velocity, stop, clock, interval)
        self.noteFactory = noteFactory
        self._on_method = self.instr.playnote
        self._off_method = self.instr.stopnote

    def _next(self):
        return self.noteFactory

Player = NotePlayer

class ChordPlayer(BasePlayer):
    implements(IChordPlayer)
    
    def __init__(self, instr, chordFactory, velocity, stop=lambda : None, clock=None,
                 interval=None):
        super(ChordPlayer, self).__init__(instr, velocity, stop, clock, interval)
        self.chordFactory = chordFactory
        self._on_method = self.instr.playchord
        self._off_method = self.instr.stopchord

    def _next(self):
        return self.chordFactory

def generateSounds(g):
    def f():
        s = g.next()
        if callable(s):
            return s()
        return s
    return f
snd = generateSounds

def N():
    return None


def R(*c):
    def f():
        return random.choice(c)
    return f



def _randomPhraseGen(phrases):
    while 1:
        phrase = random.choice(phrases)
        for next in phrase:
            yield next

def randomPhrase(*phrases):
    length = 0
    if phrases and type(phrases[0]) is int:
        length = phrases[0]
        phrases = phrases[1:]
    if length:
        for phrase in phrases:
            if len(phrase) != length:
                raise ValueError('Phrase %s is not of specified length: %s' %
                                (phrase, length))
    return _randomPhraseGen(phrases)
rp = randomPhrase


def randomWalk(sounds):
    ct = len(sounds)
    index = random.randint(0, ct - 1)
    direction = 1
    while 1:
        yield sounds[index]
        if index == 0:
            direction = 1
        elif index == ct - 1:
            direction = -1
        else:
            if random.randint(0, 1):
                direction *= -1
        index += direction
rw = randomWalk 


class StepSequencer(PlayableMixin):
    """
    A step sequencer allows you to pass an instr (typically a drum kit)
    and a set of notes of chords (representing the rows in a step sequencer graph).
    """

    def __init__(self, instr, notes, beats=16, clock=None, meter=None):
        if clock is None:
            from txbeatlounge.scheduler import clock
        if meter is None:
            meter = clock.meters[0]
        self.clock = clock
        self.meter = meter
        self.instr = instr
        self.notes = notes
        self._play = self.instr.playnote
        if type(notes[0]) in (list, tuple):
            self.play = self.instr.playchord
        self.velocity = [60] * beats
        self.beats = beats
        self.interval = 1. / beats
        self.step = 0
        self.on_off = [([0] * len(notes)) for i in range(beats)]

    def setVelocity(self, beat, velocity):
        if DEBUG:
            log.msg('[StepSequencer.setVelocity] setting velocity at beat=%d to %d' %
                    (beat, velocity))
        self.velocity[beat] = velocity

    def setStep(self, beat, note, on_off):
        if DEBUG:
            log.msg('[StepSequencer.setStep] setting %dx%d=%d' % (beat, note, on_off))
        self.on_off[beat][note] = on_off    

    def play(self):
        v = self.velocity[self.step]
        index = 0
        for note in self.notes:
            if self.on_off[self.step][index]:
                self._play(note, v)
            index += 1
        self.step = (self.step + 1) % self.beats



