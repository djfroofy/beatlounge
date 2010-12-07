from functools import partial

from twisted.python import log

from txosc import dispatch
from txosc.async import DatagramClientProtocol, ClientFactory

from txbeatlounge.debug import DEBUG
from txbeatlounge.osc.base import fallback #DispatcherHub, FloatDispatcher



class PageWidget(object):

    addressPattern = None

    def __init__(self, receiver, callbacks=[], page=1):
        self.receiver = receiver
        self.page = page
        self.callbacks = callbacks

    def _callback(self, cb, node, message, address):
        (v,) = message.arguments
        v = float(v)
        if DEBUG:
            cn = self.__class__.__name__
            log.msg('[%s] %s %s' % (cn, node, v))
        cb(v)

    def attach(self):
        self._recv_callbacks = []
        for (idx, cb) in enumerate(self.callbacks):
            node = self.addressPattern % (self.page, idx + 1)
            recvcb = partial(self._callback, cb, node)
            self._recv_callbacks.append((node, recvcb))
            self.receiver.addCallback(node, recvcb)
        return self

    def detach(self):
        for (node, recvcb) in self._recv_callbacks:
            self.receiver.removeCallback(node, recvcb)


class GridWidget(PageWidget):

    def attach(self):
        self._recv_callbacks = []
        for (j, row) in enumerate(self.callbacks):
            for (k, cb) in enumerate(row):
                node = self.addressPattern % (self.page, j+1, k+1)
                recvcb = partial(self._callback, cb, node)
                self._recv_callbacks.append((node, recvcb))
                self.receiver.addCallback(node, recvcb)
        return self
        


class Push(PageWidget): 
    addressPattern = '/%d/push%d'

class Fader(PageWidget):
    addressPattern = '/%d/fader%d'

class MultiFader(PageWidget):
    addressPattern = '/%d/multifader/%d'

class Rotary(PageWidget):
    addressPattern = '/%d/rotary%d'

class Toggle(PageWidget):
    addressPattern = '/%d/toggle%d'

class MultiToggle(GridWidget):
    addressPattern = '/%d/multitoggle/%d/%d'

class MultiFaderGrid(GridWidget):
    addressPattern = '/%d/multifader%d/%d'

class XY(object):

    def __init__(self, receiver, callback=lambda x,y: None, callbacks=None, page=1):
        self.receiver = receiver
        self.callbacks = callbacks
        self.callback = callback

    def attach(self):
        self._recv_callbacks = []
        if self.callbacks:
            for (idx, cb) in enumerate(callbacks):
                node = '/%d/xy%d' % (page, idx + 1)
                recvcb = partial(self._callback, cb, node)
                self._recv_callbacks.append((node, recvcb))
                self.receiver.addCallback(node, recvcb)
        else:
            node = '/%d/xy' % page
            recvcb = partial(self._callback, callback, node)
            self._recv_callbacks.append((node, recvcb))
            self.receiver.addCallback(node, recvcb)
        return self
    
    def _callback(self, cb, node, message, address):
        (x,y) = message.arguments
        x = float(x)
        y = float(y)
        if DEBUG:
            cn = self.__class__.__name__
            log.msg('[%s] %s %s %s' % (cn, node, x, y))
        cb(x, y)



class StepSequencer(object):

    ledAddressPattern = '/%d/led%d'

    def __init__(self, receiver, send, players, page=1, beats=16, clock=None):
        if clock is None:
            from txbeatlounge.scheduler import clock
        self.clock = clock
        self.receiver = receiver
        self.send = send
        self.players = players
        self.page = page
        instruments = len(players)
        self.velocity = [0] * beats
        self.on_off = []
        self.beats = beats
        self.step = 0
        for i in range(beats):
            self.on_off.append([0] * instruments)
        # Listeners for multifader and toggle widgets
        self._multifader = MultiFader(receiver,
            [ partial(self.setVolume, idx) for idx in range(beats) ], page) 
        self._multitoggle = MultiToggle(receiver,
            [ [ partial(self.setStep, c, r) for c in range(beats) ]
               for r in range(instruments) ], page)
        self._play_schedule = clock.schedule(self.play).startLater(1, 1. / beats)

    def attach(self):
        clock = self.clock
        beats = self.beats
        players = self.players
        self.step = 0

        # Clear out the multifader and toggle widgets
        for beat in range(beats):
            for instr in range(len(players)):
                self.send(MultiToggle.addressPattern % (
                          self.page, instr + 1, beat + 1),
                          self.on_off[beat][instr])
        for beat in range(beats):
            self.send(MultiFader.addressPattern % (self.page, beat + 1),
                      self.velocity[beat] / 127.)

        self._multifader.attach()
        self._multitoggle.attach()

        self._led_schedule = clock.schedule(self.updateLEDs).startLater(1, 1. / beats)
        self._refresh_col = 0
        self._refresh_ui_schedule = clock.schedule(self.refreshUI).startLater(1, 0.0625)
        return self

    def detach(self):
        self._led_schedule.stopLater(0)
        self._refresh_ui_schedule.stopLater(0)
        self._multifader.detach()
        self._multitoggle.detach()

    def updateLEDs(self):
        on = self.step + 1
        off = on - 1
        off = off or self.beats
        self.send(self.ledAddressPattern % (self.page, on), 1.0)
        self.send(self.ledAddressPattern % (self.page, off), 0.0)
        # really only want this for udp, but alas
        self.send(self.ledAddressPattern % (self.page, on), 1.0)
        self.send(self.ledAddressPattern % (self.page, off), 0.0)
            

    def setVolume(self, idx, v):
        nv = int(v * 127)
        if DEBUG:
            log.msg('[StepSequencer.setVolume] setting volume at beat=%d to %d' %
                    (idx, nv))
        self.velocity[idx] = nv

    def setStep(self, c, r, on_off):
        if DEBUG:
            log.msg('[StepSequencer.setStep] setting %dx%d=%d' % (c,r,on_off))
        self.on_off[c][r] = on_off    

    def refreshUI(self):
        col = self.on_off[self._refresh_col]
        for (instr, on_off) in enumerate(col):
            self.send(MultiToggle.addressPattern %
                      (self.page, instr + 1, self._refresh_col + 1), on_off)
        for beat in range(self.beats):
            self.send(MultiFader.addressPattern % (self.page, beat+1),
                      self.velocity[beat] / 127.)
        self._refresh_col = (self._refresh_col + 1) % self.beats 

    def play(self):
        v = self.velocity[self.step]
        for (idx, player) in enumerate(self.players):
            if self.on_off[self.step][idx]:
                player(v)
        self.step = (self.step + 1) % self.beats

