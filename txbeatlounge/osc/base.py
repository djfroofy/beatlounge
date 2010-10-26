from twisted.python import log

from txosc import osc
from txosc import dispatch

class AbstractDispatcher(object):
    
    address = None

    def __init__(self, address=None, transform=lambda v : v):
        self._listeners = []
        self.address = address or self.address
        self._transform = transform
    
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

    def __call__(self):
        return self

class TouchDispatcher(AbstractDispatcher):
    
    address = "touch"

    def handle(self, message, address):
        log.msg('[TouchDispatcher.handle] %s, %s, %s' % (message, message.arguments, address))
        try:
            x, y = message.arguments
            self.dispatch(self._transform(float(x)), self._transform(float(y)))
        except Exception, e:
            log.msg('[TouchDispatcher.handle] error', e)


class BoolDispatcher(AbstractDispatcher):
    def handle(self, message, address):
        self.dispatch(message.arguments[0].value)


class FloatDispatcher(AbstractDispatcher):

    def handle(self, message, address):
        try:
            (v,) = message.arguments
            self.dispatch(self._transform(float(v)))
        except Exception, e:
            log.msg('[FloatDispatcher.handle] error', e)


class Float2Dispatcher(AbstractDispatcher):

    def handle(self, message, address):
        try:
            (v1, v2) = message.arguments
            self.dispatch(self._transform(float(v1)), self._transform(float(v2)))
        except Exception, e:
            log.msg('[Float2Dispatcher.handle] error', e)
      
class Float3Dispatcher(AbstractDispatcher):

    def handle(self, message, address):
        try:
            (v1, v2, v3) = message.arguments
            self.dispatch(
                self._transform(float(v1)),
                self._transform(float(v2)),
                self._transform(sloat(v3)))
        except Exception, e:
            log.msg('[Float3Dispatcher.handle] error', e)
      
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

# Some generic device representations

class Device(object):
    pass

class Accelerometer(Device):

    pitch = 0
    roll = 0
    yaw = 0

    def on_pitch(self, v):
        self.pitch = v

    def on_roll(self, v):
        self.roll = v

    def on_yaw(self, v):
        self.yaw = v


class TouchPad(Device):

    max_x = 640
    max_y = 480
    
    x = 0
    y = 0
    
    def on_x(self, v):
        self.x = v

    def on_y(self, v):
        self.y = v




