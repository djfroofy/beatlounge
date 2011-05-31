import os

from twisted.python import log
from twisted.web.resource import IResource, Resource
from twisted.web.server import Site

from txyoga import Collection, Element

from bl.debug import setDebug
from bl.scheduler import BeatClock, Meter
from bl import arp
from bl import player
from bl.ue.web.util import encodeKwargs, decodeValues
from bl.ue.web.exceptions import ApiError
from bl.ue.web.loaders import loaders, FluidSynthInstrumentLoader


I_WANT_TO_EVAL_SHIT_FROM_ARBITRARY_SOURCE_AND_PRETEND_ITS_SAFE = True

if not I_WANT_TO_EVAL_SHIT_FROM_ARBITRARY_SOURCE_AND_PRETEND_ITS_SAFE:
    def decodeValues(values):
        for value in values:
            yield value


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

    pageSize = 200
    maxPageSize = 1000



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

    pageSize = 200
    maxPageSize = 1000

class ArpElement(Element):
    exposedAttributes = 'name', 'type', 'values'
    updatableAttributes = 'values',

    def __init__(self, name=None, type=None, values=None):
        self.name = name
        self.type = type
        self.values = values
        self.powerup()

    def powerup(self):
        self.arp = self.noteFactory = getattr(arp, self.type)(self.values)

    def update(self, state):
        Element.update(self, state)
        self.arp.reset(list(decodeValues(self.values)))
        log.msg('%s reset arp with values: %s' % (self, self.values))


class Arps(Collection):
    defaultElementClass = ArpElement
    exposedElementAttributes = 'name', 'type', 'values'

    pageSize = 200
    maxPageSize = 1000

class SwitcherElement(Element):
    updatableAttributes = 'switchee_uri', 'values', 'amount', 'octaves', 'oscillate'
    exposedAttributes = 'name', 'type', 'switchee_uri', 'values', 'amount', 'octaves', 'oscillate'
    switcherClasses = 'OctaveArp', 'Adder',
    switchers = None
    arps = None

    def __init__(self, name=None, type=None, switchee_uri=None, values=(),
                 amount=0, octaves=2, oscillate=False):
        self.name = name
        self.type = type
        self.switchee_uri = switchee_uri
        self.values = values
        self.amount = amount
        self.octaves = octaves
        self.oscillate = oscillate
        self.powerup()

    def powerup(self, update=False):
        c, name = self.switchee_uri.split('/')
        collection = getattr(self, c)
        switchee = collection[name].noteFactory
        if not update:
            switcherClass = getattr(arp, self.type)
            print switcherClass, switchee, self.values
            self.switcher = self.noteFactory = switcherClass(switchee, self.values)
        else:
            if self.values != self.switcher.values:
                self.switcher.reset(list(decodeValues(self.values)))
            if switchee != self.switcher.arp:
                self.switcher.switch(switchee)
        if hasattr(self.switcher, 'amount') and self.amount != self.switcher.amount:
            self.switcher.amount = self.amount
        if hasattr(self.switcher, 'octaves') and self.octaves != self.switcher.octaves:
            self.switcher.octaves = self.octaves
        if hasattr(self.switcher, 'oscillate') and self.oscillate != self.switcher.oscillate:
            self.switcher.oscillate = self.oscillate

    def update(self, state):
        Element.update(self, state)
        self.powerup(True)


class Switchers(Collection):
    defaultElementClass = SwitcherElement
    exposedElementAttributes = 'name', 'type', 'switchee_uri', 'values'

    pageSize = 200
    maxPageSize = 1000

class PlayerElement(Element):
    exposedAttributes = ('name', 'type', 'instrument_name', 'note_factory_uri', 'clock_name', 'velocity_arp_name',
                         'sustain', 'interval', 'playing')
    updatableAttributes = ('interval', 'playing', 'instrument_name', 'note_factory_uri', 'velocity_arp_name',
                          'sustain')
    allowedInstrumenTypes = 'NotePlayer',

    arps = None
    switchers = None
    instruments = None
    clocks = None

    def __init__(self, name=None, type='NotePlayer', instrument_name=None, note_factory_uri=None,
                 velocity_arp_name=None, clock_name='default', sustain=None,
                 interval=None, playing=False):
        self.name = name
        self.type = type
        self.instrument_name = instrument_name
        self.note_factory_uri = note_factory_uri
        self.velocity_arp_name = velocity_arp_name
        self.clock_name = clock_name
        self.interval = interval
        self.sustain = sustain
        self.playing = playing
        self.powerup()

    def powerup(self):
        instrument = self.instruments[self.instrument_name].instrument
        c, name = self.note_factory_uri.split('/')
        coll = getattr(self, c)
        note_arp = coll[name].noteFactory
        velocity_arp = self.arps[self.velocity_arp_name].arp
        clock = self.clocks[self.clock_name].clock
        if self.type not in self.allowedInstrumenTypes:
            raise ApiError('Invalid player types: %s. Allowed: %s' % (self.type, self.allowedInstrumenTypes))
        cls = getattr(player, self.type)
        self.player = cls(instrument, note_arp, velocity_arp, clock=clock, interval=self.interval,
                          stop = lambda : self.sustain)
        log.msg('%r powered up with player: %r' % (self, self.player))
        log.msg(instrument, note_arp, velocity_arp, clock, self.interval, self.sustain)

        log.msg(dir(note_arp), dir(velocity_arp))
        log.msg(note_arp.values)
        log.msg(velocity_arp.values)

        if self.playing:
            log.msg('%r starting to play' % self)
            self.player.startPlaying()

    def update(self, state):
        Element.update(self, state)
        log.msg(state)
        if 'instrument_name' in state:
            self.player.instr.stopall()
            instrument = self.instruments[self.instrument_name].instrument
            self.player.instr = instrument


        if 'playing' in state:
            # TODO, this is not working ... ?
            log.msg(self.playing)
            if state['playing']:
                if not self.playing:
                    self.playing = True
                    self.player.startPlaying()
                    log.msg('%r started player' % self)
            else:
                log.msg('%r stopped player' % self)
                self.player.stopPlaying()
                self.playing = False


        if 'note_factory_uri' in state:
            log.msg('self.arps', self.arps)
            """
            TODO: key error?
            note_arp = self.arps[self.note_factory_uri].arp
            self.player.noteFactory = note_arp
            """
        if 'velocity_arp_name' in state:
            velocity_arp = self.arps[self.velocity_arp_name].arp
            self.player.velocity = velocity_arp

        if not self.playing:
            if 'interval' in state:
                if self.playing:
                    raise ApiError('Cannot change interval on running player')
                self.player.interval = self.interval
        if 'sustain' in state:
            self.player.stop = lambda : self.sustain


class Players(Collection):
    defaultElementClass = PlayerElement
    exposedElementAttributes = (
        'name',
        'type',
        'instrument_name',
        'note_factory_uri',
        'velocity_arp_name',
        'clock_name',
        'sustain',
        'interval',
        'playing'
    )

    pageSize = 200
    maxPageSize = 1000


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

    switchers = Switchers()
    switcherResource = IResource(switchers)

    PlayerElement.arps = arps
    PlayerElement.switchers = switchers
    PlayerElement.instruments = instruments
    PlayerElement.clocks = clocks

    SwitcherElement.arps = arps
    SwitcherElement.switchers = switchers

    root = Resource()
    root.putChild('clocks', clockResource)
    root.putChild('instruments', instrumentResource)
    root.putChild('arps', arpResource)
    root.putChild('switchers', switcherResource)
    root.putChild('players', playerResource)

    site = Site(root)
    return site

