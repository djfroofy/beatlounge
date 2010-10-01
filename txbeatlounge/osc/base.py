from twisted.python import log

from txosc import osc
from txosc import dispatch

class AbstractDispatcher(object):
    
    address = None

    def __init__(self, address=None):
        self._listeners = []
        self.address = address or self.address
    
    def listen(self, handler):
        self._listeners.append(handler)

    def unlisten(self, handler):
        while handler in self._listeners:
            self._listeners.remove(handler)

    def dispatch(self, *a, **k):
        for handler in self._listeners:
            try:
                handler(*a, **k)
            except Exception, e:
                log.err('[%r.dispatch] error' % self.__class__, e)

class TouchDispatcher(AbstractDispatcher):
    
    address = "touch"

    def handle(self, message, address):
        log.msg('[TouchDispatcher.handle] %s, %s, %s' % (message, message.arguments, address))
        try:
            x, y = message.arguments
            self.dispatch(float(x), float(y))
        except Exception, e:
            log.msg('[TouchDispatcher.handle] error', e)

class FloatDispatcher(AbstractDispatcher):

    def handle(self, message, address):
        try:
            (v,) = message.arguments
            self.dispatch(float(v))
        except Exception, e:
            log.msg('[FloatDispatcher.handle] error', e)

      
class DispatcherHub(object):

    def __init__(self, *dispatchers, **kw):
        self.receiver = kw.get('receiver', None) or dispatch.Receiver()
        self.receiver.fallback = self.fallback
        self._addresses = {}
        for d in dispatchers:
            self.addDispatcher(d)

    def addDispatcher(self, dispatcher):
        if dispatcher.address in self._addresses:
            raise ValueError('Dispatcher with address %s already added' % dispatcher.address)
        self._addresses[dispatcher.address] = dispatcher
        self.receiver.addCallback('/' + dispatcher.address, dispatcher.handle)  

    def fallback(self, message, address):
        log.msg('[fallback] %s %s' % (message, address))

    def __getitem__(self, address):
        return self._addresses[address]
 


