from pyo import *

#from twisted.python import log


class PyoServer:
    _started = False
    _server = None
    _error_msg = 'Cannot %s server; server must be started first'

    @classmethod
    def start(cls, audio='jack', **kw):
        """
        Start a pyo server or do nothing if a server has already been started.

        audio: the audio device (default: jack)
        kw: additional keyword arguments to pyo.Server
        """
        if cls._server:
            return
        cls._server = s = Server(audio=audio, **kw)
        s.boot()
        s.start()
        return s

    @classmethod
    def restart(cls):
        """
        Start and top the already running pyo Server.
    
        raises AssertionError if no server is running
        """
        assert cls._server, cls._error_msg % 'restart'
        cls._server.stop()
        cls._server.start()

    @classmethod
    def stop(cls):
        """
        Stop the running pyo Server.

        raises AssertionError if no server is running
        """
        assert cls._server, cls._error_msg % 'stop'
        cls._server.stop()

    @classmethod
    def shutdown(cls):
        """
        Shutdown the running pyo Server.

        raises AssertionError if no server is running
        """
        assert cls._server, cls._error_msg % 'shutdown'
        cls._server.stop()
        cls._server.shutdown()

    @classmethod
    def reboot(cls):
        """
        Reboot the running pyo Server.

        raises AssertionError if no server is running
        """
        assert cls._server, cls._error_msg % 'reboot'
        cls._server.stop()
        cls._server.shutdown()
        cls._server.boot()
        cls._server.start()

startPyo = PyoServer.start
stopPyo = PyoServer.stop
shutdownPyo = PyoServer.shutdown
restartPyo = PyoServer.restart
rebootPyo = PyoServer.reboot

# backwards compat - please use startPyo
startPYO = startPyo

# TODO
# CHANGE REQUEST
# maybe get rid of this. pyo doesn't let you have more than one server per process.
# hence, stopPyo or shutdownPro are more convenient. 
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
        self.convolve = Convolve(self.inputs, self.harmT, size=512) # bad usage!
        self.delay = Delay(self.inputs, feedback=.6, maxdelay=20)
        self.disto = Disto(self.inputs)
        self.freeverb = Freeverb(self.inputs)
        self.harmonizer = Harmonizer(self.inputs, transpo=-12)
        self.sdelay = SDelay(self.inputs, maxdelay=20)
        self.wgverb = WGVerb(self.inputs)
        self.waveguide = Waveguide(self.inputs)
        self.FX['effects'] = [
            self.chorus, self.convolve,
            self.delay, self.disto, self.freeverb, self.harmonizer, self.sdelay, self.wgverb, self.waveguide
        ]

        self.biquad = Biquad(self.inputs, freq=1000, q=1, type=0)
        self.FX['filters'] = [
            self.biquad,
        ]


    def setOuts(self, li=[["harmonizer", "disto", "chorus", "delay"], ["harmonizer", 'disto', 'chorus']], play_clean=True):
        """
        List of lists.  The input of l[n] is l[n-1] or the main input if it is first.
        each list can not reuse a param where it would change the input of the filter.
        More on this later.
        """
        for i in self.FX['effects'] + self.FX['filters']:
            i.stop()
            i.play()

        for l in li:
            inp = self.inputs
            for i,s in enumerate(l):
                this = getattr(self, s)
                this.input = inp
                inp = this

                if i == len(l)-1:
                    this.out()

        if play_clean:
            [i.out() for i in self.inputs]
        else:
            [(i.out(),i.stop()) for i in self.inputs]


    def A(self, x):
        self.delay.delay = 4*x
    def B(self, x):
        self.delay.feedback = x
    def C(self, x):
        self.chorus.feedback = x
    def D(self, x):
        self.chorus.depth = 4*x
    def E(self, x):
        self.disto.slope = x
    def F(self, x):
        self.disto.drive = x


def main():
    from txosc.dispatch import Receiver
    from txosc.async import DatagramServerProtocol, DatagramClientProtocol
    from twisted.internet import reactor
    from txbeatlounge.osc.touchosc import Rotary

    receiver = Receiver()
    reactor.listenUDP(17779, DatagramServerProtocol(receiver), interface='0.0.0.0')

    s = startPYO()
    #client = DatagramClientProtocol()
    #clientPort = reactor.listenUDP(0, client)
    r = Rack()
    Rotary(receiver, [r.A, r.B, r.C, r.D, r.E, r.F], page=3).attach()

    return s,r



