import os

from twisted.python import log
from twisted.web.resource import IResource, Resource
from twisted.web.server import Site

from txyoga import Collection, Element

from bl.scheduler import BeatClock, Meter
from bl.ue.web.loaders import loaders, FluidSynthInstrumentLoader


class BeatClockElement(Element):
    exposedAttributes = 'name', 'tempo', 'meter', 'is_default'

    def __init__(self, name='default', tempo=132, meter='4/4', is_default=False):
        self.name = name
        self.tempo = tempo
        self.meter = meter
        self.is_default = is_default
        self.powerup()

    def powerup(self):
        n, d = self.meter.split('/')
        self.clock = BeatClock(self.tempo, Meter(int(n), int(d)),
                                default=self.is_default)
        self.clock.run(False)
        log.msg('%r powered up with clock: %s' % (self, self.clock))


class BeatClocks(Collection):
    defaultElementClass = BeatClockElement
    exposedElementAttributes = 'name', 'tempo', 'meter', 'is_default'


class InstrumentElement(Element):
    exposedAttributes = 'name', 'type', 'load_args'
    loaders = {}

    def __init__(self, name=None, type=None, load_args=None):
        self.name = name
        self.type = type
        load_args = load_args or {}
        self.load_args = dict((str(k),v) for (k,v) in load_args.items())
        self.powerup()

    def powerup(self):
        loader = loaders[self.type]
        self.instrument = loader.load(**self.load_args)
        log.msg('%r powered up with instrument:' % self)


class Instruments(Collection):
    defaultElementClass = InstrumentElement
    exposedElementAttributes = 'name', 'type'


def apiSite(sfdir):
    loaders['fluidsynth'] = FluidSynthInstrumentLoader(sfdir)
    clocks = BeatClocks()
    clockResource = IResource(clocks)

    instruments = Instruments()
    instrumentResource = IResource(instruments)

    root = Resource()
    root.putChild('clocks', clockResource)
    root.putChild('instruments', instrumentResource)

    site = Site(root)
    return site

