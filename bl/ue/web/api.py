import os
from functools import wraps

from twisted.python import log
from twisted.web.resource import IResource, Resource
from twisted.web.server import Site

from txyoga import Collection, Element

try:
    from bl.instrument.fsynth import Instrument as FluidSynthInstrument
except ImportError:
    FluidSynthInstrument = None



class ApiError(Exception):
    pass


class Clocks(Collection):
    exposedElementAttributes = ('tempo', 'meter')


class BeatClock(Element):
    exposedAttributes = ('tempo', 'meter')

    def __init__(self, clock, key=''):
        self.clock = clock
        self.key = key

    @property
    def tempo(self):
        return self.clock.tempo

    @property
    def meter(self):
        meter = self.clock.meters[0]
        return '%s/%s' % (meter.length, meter.division)


def checkClass(klassName, klass):
    def decorator(f):
        @wraps(f)
        def wrapper(*a, **k):
            if not klass:
                raise ApiError('%r is not available' % klassName)
            return f(*a, **kw)
        return wrapper
    return decorator


class FluidSynthLoader:
    def __init__(self, baseDirectory):
        self.baseDirectory = baseDirectory

    @checkClass('FluidSynthInstrument', FluidSynthInstrument)
    def load(self, uri, connection='mono'):
        if not FluidSynthInstrument:
            raise ApiError('fluidsynth is not avaiable')
        path = os.path.join(self.baseDirectory, uri)
        return Instrument(path, connection=connection)


class Instruments(Collection):
    exposedElementAttributes = ('type', 'uri', 'key')


class Instrument(Element):
    loaders = {}

    def __init__(self, type, uri, connection, key=''):
        self.type = type
        self.uri = uri
        self.connection = connection
        self.key = key
        self._load()

    def _load(self):
        loader = self.loaders[self.type]
        self._instrument = loader.load(self.uri, self.connection)
        log.msg('Loaded instrument')


def apiSite(clock, sf2dir='journey/sf2'):
    Instrument.loaders['fluidsynth'] = FluidSynthLoader(sf2dir)

    clocks = Clocks()
    clocks.add(BeatClock(clock, 'default'))
    clockResource = IResource(clocks)

    instruments = Instruments()
    instrumentResource = IResource(instruments)

    root = Resource()
    root.putChild('clocks', clockResource)
    root.putChild('instruments', instrumentResource)

    site = Site(root)
    return site

