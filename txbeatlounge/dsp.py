from pyo import *

#from twisted.python import log


def startPYO():
    s = Server(audio='jack').boot()
    s.start()
    return s

def stop(s):
    s.stop()
    s.shutdown()


class Rack(object):
    """Effectz rack for filtering the input to pyo

    >>> r = Rack()
    >>> r.setOuts(
        [["disto","delay"],["convolve","sdelay"..]
    )
    >>> r.disto.mul = r.lfoA

    """


    def __init__(self, channels=[0,1], bpm=120):

        # TODO, don't have this side-effect in the __init__

        self.inputs = []
        for c in channels:
            n = "chan%s" % c
            i = Input(c)
            setattr(self, n, i)
            self.inputs.append(i)

        self.FX = {}

        self.chebyT = ChebyTable()
        self.cosT = CosTable()
        self.curveT = CurveTable()
        self.expT = ExpTable()
        self.hannT = HannTable()
        self.harmT = HarmTable()
        self.linT = LinTable()
        self.sawT = SawTable()
        self.squareT = SquareTable()
        self.tables = [
            self.chebyT, self.cosT, self.curveT, self.expT, self.hannT, self.harmT, self.linT, self.sawT, self.squareT
        ]

        self.lfoA = Sine(freq=bpm/60.)
        self.lfoB = Sine(freq=bpm/60./2.)
        self.lfos = [
            self.lfoA, self.lfoB
        ]

        self.chorus = Chorus(self.inputs)
        #self.convolve = Convolve(self.inputs, self.chebyT, size=8192) # bad usage!
        self.delay = Delay(self.inputs, maxdelay=20)
        self.disto = Disto(self.inputs)
        self.freeverb = Freeverb(self.inputs)
        self.harmonizer = Harmonizer(self.inputs)
        self.sdelay = SDelay(self.inputs, maxdelay=20)
        self.wgverb = WGVerb(self.inputs)
        self.waveguide = Waveguide(self.inputs)
        self.FX['effects'] = [
            self.chorus, #self.convolve,
            self.delay, self.disto, self.freeverb, self.harmonizer, self.sdelay, self.wgverb, self.waveguide
        ]

        self.biquad = Biquad(self.inputs, freq=1000, q=1, type=0)
        self.FX['filters'] = [
            self.biquad,
        ]


    def setOuts(self, li=[["chorus", "disto", "freeverb", "delay", "harmonizer"]]):
        """
        List of lists.  The input of l[n] is l[n-1] or the main input if it is first.
        each list can not reuse a param where it would change the input of the filter.
        More on this later.
        """
        print li
        for l in li:
            inp = self.inputs
            for i,s in enumerate(l):
                this = getattr(self, s)
                this.inp = inp
                inp = this

                if i == len(l)-1:
                    this.out()


