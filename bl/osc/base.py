from functools import partial
from warnings import warn

from twisted.python import log
from twisted.python.failure import Failure

from txosc import async
from txosc import osc
from txosc import dispatch

from bl.player import Player, snd


def fallback(message, address):
    log.msg('[fallback] %s %s' % (message, address))


class MessageSender(object):
    """
    Example Usage:

        client = txosc.async.DatagramClientProtocol()
        clientPort = reactor.listenUDP(0, client)
        sender = MessageSender(client, '127.0.0.1', 17779)
        sender.send('/foo', 10000)
    """

    def __init__(self, client, host='127.0.0.1', port=17779):
        self.client = client
        self.host = host
        self.port = port
        if isinstance(client, async.ClientFactory):
            self._send = self._tcp_send
        if isinstance(client, async.DatagramClientProtocol):
            self._send = self._udp_send

    def send(self, address, *args):
        message = osc.Message(address, *args)
        self._send(message)

    def _udp_send(self, element):
        self.client.send(element, (self.host, self.port))

    def _tcp_send(self, element):
        self.client.send(element)


class Play(object):

    def __init__(self, instr, notes, velocity, stop=lambda: None, clock=None):
        self.notes = notes
        self.player = Player(instr, snd(self._iternotes()), velocity=velocity,
            stop=stop, clock=clock)

    def _iternotes(self):
        while 1:
            yield self.notes[self.index]

    def play(self, index, on_off):
        if on_off:
            self.index = index
            self.player.play()

    def callbacks(self):
        cbs = []
        for index in range(len(self.notes)):
            cbs.append(partial(self.play, index))
        return cbs


###########################################
# NOTE
# Everything under this note is deprecated.

class AbstractDispatcher(object):

    address = None

    def __init__(self, address=None, transform=lambda v: v):
        warn('AbstractDispatcher is deprecated for rilz')
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
                f = Failure(e)
                f.printTraceback()
                log.err(e)

    def __call__(self):
        return self


class TouchDispatcher(AbstractDispatcher):

    address = "touch"

    def handle(self, message, address):
        log.msg('[TouchDispatcher.handle] %s, %s, %s' % (
                message, message.arguments, address))
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
            f = Failure(e)
            f.printTraceback()
            log.msg('[FloatDispatcher.handle] error', e)


class Float2Dispatcher(AbstractDispatcher):

    def handle(self, message, address):
        try:
            (v1, v2) = message.arguments
            self.dispatch(self._transform(float(v1)),
                          self._transform(float(v2)))
        except Exception, e:
            log.msg('[Float2Dispatcher.handle] error', e)


class Float3Dispatcher(AbstractDispatcher):

    def handle(self, message, address):
        try:
            (v1, v2, v3) = message.arguments
            self.dispatch(
                self._transform(float(v1)),
                self._transform(float(v2)),
                self._transform(float(v3)))
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
            raise ValueError('Dispatcher with address %s already added' %
                             dispatcher.address)
        self._addresses[dispatcher.address] = dispatcher
        prefix = ''
        if dispatcher.address[0] != '/':
            prefix = '/'
        self.receiver.addCallback(prefix + dispatcher.address,
                                  dispatcher.handle)

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
