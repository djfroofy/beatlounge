from zope.interface import Interface, implements

from twisted.python import log
from twisted.python.components import proxyForInterface
from twisted.internet.defer import Deferred, succeed, fail

from epsilon.modal import mode, Modal

try:
    from txmongo import MongoConnection
except:
    def MongoConnection(*a, **k):
        raise RuntimeError('txmongo required')

from bl.ue.web.exceptions import StorageError


class IStore(Interface):

    def collection(name):
        """
        Get a collection (IPersistentCollection) provider by name.
        Returns a deferred that while fire when the collection is accessible
        or errback if it could not be found.
        """

class IPersistentCollection(Interface):

    # TODO
    # The following iface methods were lifted from txmongo sources.
    # Whether or not all of these stay, more need to be added is up in the
    # air now so consider this iface unstable.

    def find(spec=None, skip=0, limit=0, fields=None, filter=None):
        pass

    def find_one(spec=None, fields=None):
        pass

    def count(spec=None, fields=None):
        pass

    def group(keys, initial, reduce, condition=None, finalize=None):
        pass

    def filemd5(spec):
        pass

    def insert(docs, safe=False):
        pass

    def update(spec, document, upsert=False, multi=False, safe=False):
        pass

    def save(doc, safe=False):
        pass

    def remove(spec, safe=False):
        pass

    # And I stopped here ... maybe we need more ... maybe less



class MongoStore(Modal):
    implements(IStore)

    modeAttribute = 'mode'
    initialMode = 'quiescent'

    host = 'localhost'
    port = 27017
    reconnect = True
    mongo = None
    _pending = ()

    class quiescent(mode):
        """
        collection method for "quiescent" mode
        """
        def collection(self, name):
            log.msg('collection called in quiescent mode')
            self._pending = []
            self.mode = 'connecting'
            MongoConnection(self.host, self.port, self.reconnect
                           ).addCallbacks(self._connect_cb, self._connect_cb)
            return self.collection(name)

    class connecting(mode):
        """
        collection method for "connecting" mode
        """
        def collection(self, name):
            log.msg('collection called in connecting mode')
            d = Deferred()
            self._pending.append((d, name))
            return d

    class connected(mode):
        """
        collection method for "connected" mode
        """
        def collection(self, name):
            log.msg('collection called in connected mode: %s' % name)
            coll = self.db[name]
            return succeed(MongoCollection(coll))

    def _connect_cb(self, mongo):
        self.mongo = mongo
        self.db = self.mongo.bl
        self.mode = 'connected'
        for (d, name) in self._pending:
            d.callback(self.collection(name))
        self._pending = ()

    def _connect_eb(self, why):
        for (d, name) in self._pending:
            d.errback(StorageError(str(why), why.value))
        self._pending = ()
        self.mode = 'quiescent'

_mongoStore = MongoStore()

# Make a proxy obeying the IPersistentCollection iface for mongo
# so it's hard to accidentally use methods outside what we might want to support
# for swappable storage backends

class MongoCollection(proxyForInterface(IPersistentCollection, originalAttribute='_collection')):
    implements(IPersistentCollection)
    def __init__(self, collection):
        self._collection = collection

# TODO make some in-memory implementations for testing/fallback


def thing2MongoStore(thing):
    return _mongoStore

