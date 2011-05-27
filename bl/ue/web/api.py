import os

from twisted.python import log
from twisted.python.components import registerAdapter
from twisted.web.resource import IResource, Resource
from twisted.web.server import Site

from txyoga import Collection, Element

from bl.debug import setDebug
from bl.scheduler import BeatClock, Meter
from bl import arp
from bl import player
from bl.ue.web.util import encodeKwargs, decodeValues, newTuple
from bl.ue.web.exceptions import ApiError
from bl.ue.web.loaders import loaders, FluidSynthInstrumentLoader
from bl.ue.web.storage import IStore

I_WANT_TO_EVAL_SHIT_FROM_ARBITRARY_SOURCE_AND_PRETEND_ITS_SAFE = True

if not I_WANT_TO_EVAL_SHIT_FROM_ARBITRARY_SOURCE_AND_PRETEND_ITS_SAFE:
    def decodeValues(values):
        for value in values:
            yield value

class PersistentElement(Element):
    _id = None
    persistentAttributes = 'name', '_id'
    persisted = False
    collectionName = ''

    def save(self):
        self.saving = True
        store = IStore(self)
        return store.collection(self.collectionName).addCallbacks(
            self._collection_cb, log.err)

    def powerUp(self, update=False):
        pass

    def update(self, state):
        Element.update(self, state)
        # TODO
        # Part of me thinks we should save and then power up so
        # our elements aren't in a powered-up state that doesn't
        # reflect what has been persisted; Another side of me
        # like not to wait for the latency before an object is
        # powered up.
        self.powerUp(update=True)
        self.save()

    def _collection_cb(self, collection):
        log.msg('got collection: %s' % collection)
        document = dict((name, getattr(self, name)) for name in self.persistentAttributes
                        if not (name == '_id' and self._id is None))
        d = collection.save(document)
        d.addCallbacks(self._saved_cb, log.err)
        return d

    def _saved_cb(self, _id):
        self._id = _id
        log.msg('Saved: %s' % _id)
        self.saving = False
        self.persisted = True


class BeatClockElement(PersistentElement):
    exposedAttributes = 'name', 'tempo', 'meter', 'is_default', 'saving', 'persisted'
    persistentAttributes = newTuple(exposedAttributes,
                                    add=('_id',), remove=('saving', 'persisted'))
    collectionName = 'clocks'

    def __init__(self, name='default', tempo=132, meter='4/4', is_default=False):
        self.name = name
        self.tempo = tempo
        self.meter = meter
        self.is_default = is_default
        self.powerUp()
        self.save()

    def powerUp(self, update=False):
        if update:
            return
        n, d = self.meter.split('/')
        self.clock = BeatClock(self.tempo, [ Meter(int(n), int(d)) ],
                                default=self.is_default)
        self.clock.run(False)
        log.msg('%r powered up with clock: %s' % (self, self.clock))


class BeatClocks(Collection):
    defaultElementClass = BeatClockElement
    exposedElementAttributes = 'name', 'tempo', 'meter', 'is_default', 'saving', 'persisted'

class InstrumentElement(PersistentElement):
    exposedAttributes = 'name', 'type', 'load_args', 'cc',
    persistentAttributes = newTuple(exposedAttributes,
                                    add=('_id',), remove=('saving', 'persisted'))
    updatableAttributes = 'cc',
    loaders = {}
    collectionName = 'instruments'

    def __init__(self, name=None, type=None, load_args=None, cc=None):
        self.name = name
        self.type = type
        self.cc = cc or {}
        load_args = load_args or {}
        self.load_args = dict((str(k),v) for (k,v) in load_args.items())
        self.powerUp()
        self.save()

    def powerUp(self, update=False):
        if update:
            self.instrument.controlChange(**encodeKwargs(self.cc))
            log.msg('%r adjusting cc on instrument: %s' % (self, self.cc))
            return
        loader = loaders[self.type]
        self.instrument = loader.load(**self.load_args)
        log.msg('%r powered up with instrument: %s' % (self, self.instrument))


class Instruments(Collection):
    defaultElementClass = InstrumentElement
    exposedElementAttributes = 'name', 'type'

class ArpElement(PersistentElement):
    exposedAttributes = 'name', 'type', 'values', 'saving', 'persisted'
    updatableAttributes = 'values',
    persistentAttributes = newTuple(exposedAttributes,
                                    add=('_id',), remove=('saving', 'persisted'))
    collectionName = 'arps'

    def __init__(self, name=None, type=None, values=None):
        self.name = name
        self.type = type
        self.values = values
        self.powerUp()
        self.save()

    def powerUp(self, state=None, update=False):
        if update:
            self.arp.reset(list(decodeValues(self.values)))
            log.msg('%s reset arp with values: %s' % (self, self.values))
            return
        self.arp = self.noteFactory = getattr(arp, self.type)(self.values)


class Arps(Collection):
    defaultElementClass = ArpElement
    exposedElementAttributes = 'name', 'type', 'values', 'saving', 'persisted'

class SwitcherElement(PersistentElement):
    updatableAttributes = 'switchee_uri', 'values', 'amount', 'octaves', 'oscillate'
    exposedAttributes = 'name', 'type', 'switchee_uri', 'values', 'amount', 'octaves', 'oscillate'
    persistentAttributes = newTuple(exposedAttributes,
                                    add=('_id',), remove=('saving', 'persisted'))
    collectionName = 'switchers'
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
        self.powerUp()
        self.save()

    def powerUp(self, state=None, update=False):
        c, name = self.switchee_uri.split('/')
        collection = getattr(self, c)
        switchee = collection[name].noteFactory
        if not update:
            switcherClass = getattr(arp, self.type)
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



class Switchers(Collection):
    defaultElementClass = SwitcherElement
    exposedElementAttributes = 'name', 'type', 'switchee_uri'

class PlayerElement(PersistentElement):
    exposedAttributes = ('name', 'type', 'instrument_name', 'note_factory_uri', 'clock_name', 'velocity_arp_name',
                         'sustain', 'interval', 'playing', 'saving', 'persisted')
    updatableAttributes = ('interval', 'playing', 'instrument_name', 'note_factory_uri', 'velocity_arp_name',
                          'sustain')
    persistentAttributes = newTuple(exposedAttributes,
                                    add=('_id',), remove=('saving', 'persisted'))
    collectionName = 'players'
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
        self.powerUp()
        self.save()

    def powerUp(self, state=None, update=False):
        if update:
            return self._update(state)
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
        if self.playing:
            log.msg('%r starting to play' % self)
            self.player.startPlaying()

    def _update(self, state):
        if 'instrument_name' in state:
            instrument = self.instruments[self.instrument_name].instrument
            self.player.instr = instrument
        if 'note_factory_uri' in state:
            note_arp = self.arps[self.note_factory_uri].arp
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

    # Let's embark on this magical journey that is persistence with mongodo
    from bl.ue.web.storage import thing2MongoStore
    from txyoga.interface import ICollection, IElement
    registerAdapter(thing2MongoStore, ICollection, IStore)
    registerAdapter(thing2MongoStore, IElement, IStore)

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

