import os

from twisted.python import log
from twisted.web.resource import IResource, Resource
from twisted.web.server import Site

from txyoga import Collection, Element

from bl.debug import setDebug
from bl.scheduler import BeatClock, Meter
from bl import arp
from bl import player
from bl.ue.web.util import encodeKwargs
from bl.ue.web.exceptions import ApiError
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
        self.clock = BeatClock(self.tempo, [ Meter(int(n), int(d)) ],
                                default=self.is_default)
        self.clock.run(False)
        log.msg('%r powered up with clock: %s' % (self, self.clock))


class BeatClocks(Collection):
    defaultElementClass = BeatClockElement
    exposedElementAttributes = 'name', 'tempo', 'meter', 'is_default'


class InstrumentElement(Element):
    exposedAttributes = 'name', 'type', 'load_args', 'cc',
    updatableAttributes = 'cc',
    loaders = {}

    def __init__(self, name=None, type=None, load_args=None, cc=None):
        self.name = name
        self.type = type
        self.cc = cc or {}
        load_args = load_args or {}
        self.load_args = dict((str(k),v) for (k,v) in load_args.items())
        self.powerup()

    def powerup(self):
        loader = loaders[self.type]
        self.instrument = loader.load(**self.load_args)
        log.msg('%r powered up with instrument: %s' % (self, self.instrument))

    def update(self, state):
        cc = self.cc
        Element.update(self, state)
        if cc != self.cc:
            self.instrument.controlChange(**encodeKwargs(self.cc))
            log.msg('%r adjusting cc on instrument: %s' % (self, self.cc))


class Instruments(Collection):
    defaultElementClass = InstrumentElement
    exposedElementAttributes = 'name', 'type'


class ArpElement(Element):
    exposedAttributes = 'name', 'type', 'values'
    updatableAttributes = 'values',

    def __init__(self, name=None, type=None, values=None):
        self.name = name
        self.type = type
        self.values = values
        self.powerup()

    def powerup(self):
        self.arp = getattr(arp, self.type)(self.values)

    def update(self, state):
        Element.update(self, state)
        self.arp.reset(self.values)
        log.msg('%s reset arp with values: %s' % (self, self.values))

class Arps(Collection):
    defaultElementClass = ArpElement
    exposedElementAttributes = 'name', 'type'


class PlayerElement(Element):
    exposedAttributes = ('name', 'type', 'instrument_name', 'note_arp_name', 'clock_name', 'velocity_arp_name',
                         'sustain', 'interval', 'playing')
    updatableAttributes = ('interval', 'playing', 'instrument_name', 'note_arp_name', 'velocity_arp_name',
                          'sustain')
    allowedInstrumenTypes = 'NotePlayer',


    arps = None
    instruments = None
    clocks = None

    def __init__(self, name=None, type='NotePlayer', instrument_name=None, note_arp_name=None,
                 velocity_arp_name=None, clock_name='default', sustain=None,
                 interval=None, playing=False):
        self.name = name
        self.type = type
        self.instrument_name = instrument_name
        self.note_arp_name = note_arp_name
        self.velocity_arp_name = velocity_arp_name
        self.clock_name = clock_name
        self.interval = interval
        self.sustain = sustain
        self.playing = playing
        self.powerup()

    def powerup(self):
        instrument = self.instruments[self.instrument_name].instrument
        note_arp = self.arps[self.note_arp_name].arp
        velocity_arp = self.arps[self.velocity_arp_name].arp
        clock = self.clocks[self.clock_name].clock
        if self.type not in self.allowedInstrumenTypes:
            raise ApiError('Invalid player types: %s. Allowed: %s' % (self.type, self.allowedInstrumenTypes))
        cls = getattr(player, self.type)
        self.player = cls(instrument, note_arp, velocity_arp, clock=clock, interval=self.interval,
                          stop = lambda : self.sustain)
        log.msg('%r powered up with player: %r' % (self, self.player))
        if self.playing:
            log.msg('%r starting to play' % self)
            self.player.startPlaying()

    def update(self, state):
        Element.update(self, state)
        if 'instrument_name' in state:
            instrument = self.instruments[self.instrument_name].instrument
            self.player.instr = instrument
        if 'note_arp_name' in state:
            note_arp = self.arps[self.note_arp_name].arp
            self.player.noteFactory = note_arp
        if 'velocity_arp_name' in state:
            velocity_arp = self.arps[self.velocity_arp_name].arp
            self.player.velocity = velocity_arp
        if 'interval' in state:
            if self.playing:
                raise ApiError('Cannot change interval on running player')
            self.player.interval = self.interval
        if 'sustain' in state:
            self.player.stop = lambda : self.sustain
        if 'playing' in state:
            if state['playing']:
                self.player.startPlaying()
                log.msg('%r started player' % self)
            else:
                self.player.stopPlaying()


class Players(Collection):
    defaultElementClass = PlayerElement
    exposedElementAttributes = 'name', 'type'


def apiSite(sfdir):
    #setDebug(True)

    loaders['fluidsynth'] = FluidSynthInstrumentLoader(sfdir)
    clocks = BeatClocks()
    clocks.add(BeatClockElement(is_default=True))
    clockResource = IResource(clocks)

    instruments = Instruments()
    instrumentResource = IResource(instruments)

    arps = Arps()
    arpResource = IResource(arps)

    players = Players()
    playerResource = IResource(players)

    PlayerElement.arps = arps
    PlayerElement.instruments = instruments
    PlayerElement.clocks = clocks

    root = Resource()
    root.putChild('clocks', clockResource)
    root.putChild('instruments', instrumentResource)
    root.putChild('arps', arpResource)
    root.putChild('players', playerResource)

    site = Site(root)
    return site

