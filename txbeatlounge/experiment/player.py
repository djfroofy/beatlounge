from zope.interface import Interface, Attribute, implements


__all__ = [ 'IPlayer', 'INotePlayer', 'IChordPlayer',
            'BasePlayer', 'NotePlayer', 'ChordPlayer',
            'N', 'F', 'Num', 'generateSounds' ]


class IPlayer(Interface):
    instr = Attribute('Instrument that provides playnote(note, velocity)')
    velocity = Attribute('IFilter to get current velocity')
    stop = Attribute('Callable to get stop time on current note/chord, or None for non-stop')

class INotePlayer(Interface):
    note = Attribute('Callable to get the current note to play')

class IChordPlayer(Interface):
    chord = Attribute('Callable to get the current chord to play')   
 


class BasePlayer(object):
    implements(IPlayer)

    def __init__(self, instr, velocity, stop, clock=None):
        self.instr = instr
        self.velocity = velocity
        self.stop = stop
        if clock is None:
            from txbeatlounge.scheduler2 import clock
        self.clock = clock

    def play(self):
        v, o = self.velocity(110, None)
        n = self._next()
        if callable(n):
            n = n()
        if n is None:
            return
        self._on_method(n, v)
        stop = self.stop()
        if stop is not None:
            self.clock.callLater(stop, self._off_method, n)


class NotePlayer(BasePlayer):
    implements(INotePlayer)

    def __init__(self, instr, note, velocity, stop=lambda : None, clock=None):
        super(NotePlayer, self).__init__(instr, velocity, stop, clock)
        self.note = note
        self._on_method = self.instr.playnote
        self._off_method = self.instr.stopnote

    def _next(self):
        return self.note


Player = NotePlayer

class ChordPlayer(BasePlayer):
    implements(IChordPlayer)
    
    def __init__(self, instr, note, velocity, stop=lambda : None, clock=None):
        super(ChordPlayer, self).__init__(instr, velocity, stop, clock)
        self.chord = chord
        self._on_method = self.instr.playchord
        self._off_method = self.instr.stopchord

    def _next(self):
        return self.chord

def generateSounds(g):
    def f():
        s = g.next()
        if callable(s):
            return s()
        return s
    return f


def N():
    return None

def F(numerator, denominator):
    _result = numerator / float(denominator)
    def f():
        return _result
    return f

def Num(n):
    def f():
        return n
    return f

def _numberwang():
    g = globals()
    for i in range(128):
        g['n%s' % i] = Num(i)
        __all__.append('n%s' % i)
_numberwang()


