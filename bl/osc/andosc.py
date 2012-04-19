from functools import partial


class OSCCallbackBase(object):

    def __init__(self, receiver, callback=lambda x, y: None, callbacks=None):
        self.receiver = receiver
        self.callbacks = callbacks
        self.callback = callback

    def attach(self):
        self._recv_callbacks = []
        if self.callbacks:
            for (idx, cb) in enumerate(self.callbacks):
                recvcb = partial(self._callback, cb, self.address)
                self._recv_callbacks.append((self.address, recvcb))
                self.receiver.addCallback(self.address, recvcb)
        else:
            recvcb = partial(self._callback, self.callback, self.address)
            self._recv_callbacks.append((self.address, recvcb))
            self.receiver.addCallback(self.address, recvcb)
        return self


class Touch(OSCCallbackBase):
    address = "/touch"

    def _callback(self, cb, node, message, address):
        pass


class Acc(OSCCallbackBase):
    address = "/acc"

    def _callback(self, cb, node, message, address):
        compass, pitch, roll = message.arguments
        compass = float(compass) / 360.
        pitch = (float(pitch) + 180) / 360.
        roll = (float(roll) + 90) / 180.
        cb(compass, pitch, roll)


class Ori(OSCCallbackBase):
    address = "/ori"

    def _callback(self, cb, node, message, address):
        compass, pitch, roll = message.arguments
        compass = int(compass) / 360.
        pitch = (int(pitch) + 180) / 360.
        roll = (int(roll) + 90) / 180.
        cb(compass, pitch, roll)


def main():
    from pyo import Sine
    from bl.dsp import startPYO
    s = startPYO()

    from twisted.internet import reactor
    from txosc.dispatch import Receiver
    from txosc.async import DatagramServerProtocol

    receiver = Receiver()
    reactor.listenUDP(17779, DatagramServerProtocol(receiver),
                      interface='0.0.0.0')

    sineMulMul = Sine(1)
    sineMul = Sine(1, mul=sineMulMul)
    sine = Sine([110, 110 + (55 / 32.)], mul=sineMul)

    def cb(x, y, z):
        sine.freq = [x * 220, x * 220 + (55 / 32.)]
        sine.mul.freq = y * 55
        sine.mul.mul.freq = z * 55

    ori = Ori(receiver, cb)
    acc = Acc(receiver, cb)
    return s, ori, acc, sine
