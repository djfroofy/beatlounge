"""
A Player for pyo Pyo instances
"""
from bl.utils import getClock
from bl.orchestra.base import (SchedulePlayer, OneSchedulePlayerMixin,
                               timing, schedule)


class PyoPlayer(OneSchedulePlayerMixin):
    """
    A pyo player. This is more specifically a Player for PyoObject instances
    whose parameters can be modulated. Just pass parameters as dict to
    constructor - a value in the dict may be a callable ugen.

    Example:

        from pyo import midiToHz, Sine, Server

        from bl.arp import OrderedArp, ArpMap
        from bl.orchestra.pyo import PyoPlayer

        serv = Server().boot().start()
        arp = OrderedArp([60,64,67,69,48,50,55,52])
        arp = ArpMap(midiToHz, arp)
        sine = Sine(midiToHz(60), mul=0.2)
        out = sine.out()
        player = PyoPlayer(out, interval=(1,8)).setArgs(freq=arp)
        player.resumePlaying()
    """

    def __init__(self, pyo, time=None, interval=(1, 8), clock=None, args=None):
        if args is None:
            args = {}
        self.pyo = pyo
        self._gatherMethods()
        self.clock = getClock(clock)
        self.time = timing(self.clock, time, interval)
        sched = schedule(self.time, self.modulate, args)
        self.args = args
        self.schedulePlayer = SchedulePlayer(sched, self.clock)

    def updateArgs(self, **args):
        self.args.update(args)
        return self

    def modulate(self, **args):
        for name in args:
            v = args[name]
            if type(v) is tuple:
                v = list(v)
            self._methods[name](v)

    def _gatherMethods(self):
        self._methods = {}
        for attr in dir(self.pyo):
            setter = getattr(self.pyo, 'set%s' % attr.capitalize())
            self._methods[attr] = setter
