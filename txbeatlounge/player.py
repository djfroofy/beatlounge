import random
from itertools import cycle

from zope.interface import Interface, Attribute, implements

from twisted.python import log

from txbeatlounge.utils import getClock
from txbeatlounge.debug import DEBUG
from txbeatlounge.scheduler import mtt


__all__ = [ 'IPlayer', 'INotePlayer', 'IChordPlayer', 'BasePlayer', 'Player',
    'NotePlayer', 'ChordPlayer', 'N', 'R', 'noteFactory', 'nf', 'generateSounds',
    'snd', 'rp', 'randomPhrase', 'randomWalk', 'rw', 'StepSequencer', 'weighted',
    'w', 'Shifter', 'quarter', 'Q', 'eighth', 'E', 'quaver', 'sixteenth', 'S',
    'semiquaver', 'thirtysecond', 'T', 'demisemiquaver', 'sequence', 'seq', 'cut',
    'explode', 'lcycle', 'Conductor', 'START', 'callMemo', 'cm']


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
        pass

    def stopPlaying(node=None):
        pass

    
class PlayableMixin(object):
    implements(IPlayable)
    clock = getClock()

    def startPlaying(self, node=None):
        self._playSchedule = self.clock.schedule(self.play).startLater(
            0, self.interval)
   
    def stopPlaying(self, node=None):
        se = self._playSchedule
        # Stop one tick before the next measure -
        # This means if you try to schedule something at a granularity of 1
        # you're kind of screwed - though I'm not sure of a nicer way to prevent
        # the non-determinism on something stopping before it starts again when
        # the stop and start are scheduled for the same tick

        ticksd = self.clock.ticks % self.meter.ticksPerMeasure
        ticks = self.meter.ticksPerMeasure - 1 - ticksd
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
        n = self._next()
        if callable(n):
            n = n()
        if n is None:
            return
        v, o = self.velocity(110, None)
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
        self._on_method = lambda n, v : self.instr.playnote(n, v)
        self._off_method = lambda n : self.instr.stopnote(n)

    def _next(self):
        return self.noteFactory

Player = NotePlayer

class ChordPlayer(BasePlayer):
    implements(IChordPlayer)
    
    def __init__(self, instr, chordFactory, velocity, stop=lambda : None, clock=None,
                 interval=None):
        super(ChordPlayer, self).__init__(instr, velocity, stop, clock, interval)
        self.chordFactory = chordFactory
        self._on_method = lambda c, v : self.instr.playchord(c, v)
        self._off_method = lambda  c : self.instr.stopchord(c)

    def _next(self):
        return self.chordFactory

START = None

class Conductor(object):
    """
    A Conductor plays a score graphs which consists of nodes which each give
    the duration in measures to play a node, a list of players (IPlayable) to start
    and stop at the beginning and end of the duration and a list of trasitions
    (other keys into) the graph to randomly transtition to.  The reserved key START
    (equal to None) is for designating which node to start at.  The length of the
    measure is determined by the supplied clock's (or the default global clock's)
    default Meter (i.e. clock.meters[0]).

    An example score graph and conductor:

        score = { START: 'a',
                 'a': { 'players' : [player1, player2], 'duration': 2, 
                        'transitions' : ['a', 'b']},
                 'b': { 'players' : [player1, player3], 'duration': 1,
                        'transitions' : ['a']} }
        conductor = Conductor(score)
        conductor.start()

    In the above example, the conductor once started will play player1 and
    player2 for 2 measures, then transition to itself or the next node 'b' with
    50/50 chance of either. When node 'b' is stated player1 and player3 with play
    for one measure and then always transition back to 'a'. 
    """

    def __init__(self, scoreGraph, clock=None):
        self.clock = getClock(clock)
        self.scoreGraph = scoreGraph
        self.currentNode = {'players':()}
        self.nextNode = self.currentNode
        self._hold = None

    def start(self):
        """
        Start the conductor.
        
        (Note that the actual start time is generally after two measures a 1
        measure pause to resume at the start of the next measure and then an additional
        measure before the the players begin after the initial call to startPlaying())
        """
        node = self.scoreGraph[START]
        self.clock.callAfterMeasures(1, self._resume, node)

    def _resume(self, node):
        schedule = self.clock.schedule
        if self._hold:
            node = self._hold
        if node is None:
            node = random.choice(self.currentNode['transitions'])
        next = self.scoreGraph[node]
        if DEBUG:
            log.msg('[Conductor] transitioning %s' % next)
        self._duration = duration = next["duration"]
        for player in next['players']:
            player.startPlaying(node)
        self.currentNode = next
        self.currentNode['key'] = node
        self.clock.callAfterMeasures(duration-1, self._stop, node)
        self.clock.callAfterMeasures(duration, self._resume, None)

    def _stop(self, node):
        for player in self.currentNode.get('players', ()):
            player.stopPlaying(node)

    def hold(self):
        """
        Stop transitioning an continue playing current node for blocks of measures
        given by the current node's duration. After calling release(), the conductor
        will resume regular transitioning.
        """
        self._hold = self.currentNode['key']

    def release(self):
        """
        Continue transitioning - don't hold current node anymore.
        """
        self._hold = None


def noteFactory(g):
    """
    Close a generator `g` of note/chord values or
    callables which return note/chord values
    with a note factory function which can be passed
    to a NotePlayer or ChordPlayer's constructor.
    """
    def f():
        s = g.next()
        if callable(s):
            return s()
        return s
    return f

nf = noteFactory

# Deprecated aliases for backwards compat
generateSounds = noteFactory
snd = noteFactory


class _Nothing(object):
    
    def __str__(self):
        return 'N'
    
    def __repr__(self):
        return 'N'

    def __call__(self):
        return None

    def __bool__(self):
        return False

N = _Nothing()


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


def weighted(*notes):
    ws = []
    for (note, weight) in notes:
        ws.extend([note for w in range(weight)])
    random.shuffle(ws)
    return ws 
w = weighted


class Shifter(object):
    """
    shifter = Shifter()
    shifter.amount = 60
    shift_cycle = cycle([0,4,7,12])
    s = nf(shifter.shift(shift_cycle))
    p = Player(instr, s, v1, interval... )
    p.startPlaying()
    shifter.amount = 55
    shifter.shift(other_cycle)
    """

    def __init__(self, gen=None):
        self.gen = gen
        self.amount = 0
    
    def shift(self, gen=None):
        self.gen = gen or self.gen
        return iter(self)

    def __iter__(self):
        while 1:
            next = self.gen.next()
            n = next
            if callable(next):
                n = next()
            if n is None:
                yield next
            elif type(n) in (list, tuple):
                yield [ i + self.amount for i in n ]
            else:
                yield n + self.amount


def quarter(n=0):
    return mtt(n * 0.25)
Q = quarter

def eighth(n=0):
    return mtt(n * 0.125)
E = quaver = eighth

def sixteenth(n=0):
    return mtt(n * 0.0625)
S = semiquaver = sixteenth

def thirtysecond(n=0):
    return mtt(n * 0.03125)
T = demisemiquaver = thirtysecond


def sequence(schedule, length=8):
    filler = [ N ] 
    notes = [ ]
    last = 0
    for (note, when) in schedule:
        fill = ( when - last )
        notes.extend(filler * fill)
        notes.append(note)
        last = when + 1
    if last != length :
        notes.extend(filler * (length - last))
    return notes

seq = sequence

class callMemo:
    """
    Wrap a callable with one which will memo the last returned
    value on the attribute `currentValue`. This is useful if you
    need to access the last value (generally, a note or chord) later;
    in the context of a custom velocity factory, for example.
    """

    def __init__(self, func):
        self._func = func
        self.currentValue = None

    def __call__(self, *a, **kw):
        self.currentValue = self._func(*a, **kw)
        return self.currentValue
       
cm = callMemo
  

def explode(notes, factor=2):
    notes2 = []
    f = factor-1
    for note in notes:
        notes2.append(note)
        for i in range(f):
            notes2.append(N)
    return notes2


#def cut(list, start, end1, end2, strict=True):
#    c = (end2 - start) / (end1 - start)
#    thecut = list[:start] + list[start:end1] * c + list[end2:]
#    print thecut
#    assert len(thecut) == len(list), 'dude %d %d' % (len(thecut), len(list))
#    return thecut


def cut(notes, aprob=0.25, bprob=0.25):
    size = len(notes)
    m = size / 2
    if random.random() <= bprob:
        #print 'cutting right'
        if random.random() <= 0.5: # half chop
            #print 'cutting middleway'
            slice = _cut(notes[m:])
            notes = notes[:m] + slice
        else: # quarter chop
            #print 'cutting quarter way'
            if random.random() <= bprob:
                slice = _cut(notes[m+m/2:])
                notes = notes[:m+m/2] + slice 
            else:
                slice = _cut(notes[m:m+m/2])
                notes = notes[:m] + slice + notes[m+m/2:]
    if random.random() <= aprob:
        #print 'cutting left', len(notes)
        if random.random() <= 0.5:
            #print 'cutting midway'
            slice = _cut(notes[:m])
            #print '%d %d' % (len(slice), len(notes[m:]))
            notes = slice + notes[m:]
        else:
            #print 'cutting quarter way'
            if random.random() <= bprob:
                slice = _cut(notes[:m/2])
                notes = slice + notes[m/2:] 
            else:
                slice = _cut(notes[m/2:m])
                notes = notes[:m/2] + slice + notes[m:]
    return notes



def _cut(notes):
    #print 'cutting', notes
    size = len(notes)
    #print 'size', size
    if notes[0] == N:
        for (first, note) in enumerate(notes):
            if note != N:
                break
        repeat = size / (first+1)
        notes = (notes[:first+1] * repeat)[:size]
        notes.extend([N] * (size - len(notes)))
        #print '1.', notes
        return notes
    if size >= 8 and random.random() <= 0.10:
        rv = notes[:4] * (size / 4)
        #print '2.', rv
        return rv
    if size >= 4 and random.random() <= 0.75:
        rv = notes[:2] * (size / 2)
        #print '3.', rv
        return rv
    rv = [notes[0]] * size
    #print '4.', rv
    return rv


def lcycle(length, list):
    if len(list) != length:
        raise ValueError('Cycle %s not of length %s' % (list, length))
    return cycle(list)


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



