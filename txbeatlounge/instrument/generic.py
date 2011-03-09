

class GenericInstrument(object):

    def playnote(self, note, velocity):
        pass

    def stopnote(self, note):
        pass

    def playchord(self, chord, velocity):
        for note in chord:
            self.playnote(note, velocity)

    def stopchord(self, chord):
        for note in chord:
            self.stopnote(note)

    def stopall(self):
        pass



NO_RESET = object()

class AttributeInstrument(GenericInstrument):

    attributes = ()
    reset = NO_RESET

    def _get_attribute(self, note):
        attrib = self.attributes[note].split('.')
        v = self
        base = attrib[:-1]
        while base:
            v = getattr(v, base.pop(0))
        return v, attrib[-1]

    def playnote(self, note, velocity):
        v, name = self._get_attribute(note)
        setattr(v, name, velocity)


    def stopnote(self, note):
        if self.reset is not NO_RESET:
            v, name = self._get_attribute(note)
            setattr(v, name, self.reset)


#### Example shit - don't use

class PyoAttributeInstrument(AttributeInstrument):
    """
    # Will sound horrible - but for example:
    freqs = [ 55, 57.5, 110, 112.5, 110 * 1.5, 220, 222.6, 220 * 1.5 ]
    instr = PyoAttributeInstrument()
    player = Player(instr, cycle([0,1]), Stepper(freqs), interval=0.125)
    player.startPlaying()
    """

    attributes = ('sineL.freq.input.value',
                  'sineR.freq.input.value')

    def __init__(self):
        from pyo import Sine, Port, Sig
        self.sineL = Sine(Port(Sig(110), 0.2, 0.2), add=0.5, mul=0.5).out()
        self.sineR = Sine(Port(Sig(112.5), 0.2, 0.2), add=0.5, mul=0.5).out(1)

