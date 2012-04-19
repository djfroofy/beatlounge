from functools import partial

from twisted.python import log

from bl.debug import DEBUG


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
                node = self.addressPattern % (self.page, j + 1, k + 1)
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

    def __init__(self, receiver, callback=lambda x, y: None, callbacks=None,
                 page=1):
        self.receiver = receiver
        self.callbacks = callbacks
        self.callback = callback
        self.page = page

    def attach(self):
        self._recv_callbacks = []
        if self.callbacks:
            for (idx, cb) in enumerate(self.callbacks):
                node = '/%d/xy%d' % (self.page, idx + 1)
                recvcb = partial(self._callback, cb, node)
                self._recv_callbacks.append((node, recvcb))
                self.receiver.addCallback(node, recvcb)
        else:
            node = '/%d/xy' % self.page
            recvcb = partial(self._callback, self.callback, node)
            self._recv_callbacks.append((node, recvcb))
            self.receiver.addCallback(node, recvcb)
        return self

    def _callback(self, cb, node, message, address):
        (x, y) = message.arguments
        x = float(x)
        y = float(y)
        if DEBUG:
            cn = self.__class__.__name__
            log.msg('[%s] %s %s %s' % (cn, node, x, y))
        cb(x, y)


class TouchOSCStepSequencer:

    ledAddressPattern = '/%d/led%d'

    def __init__(self, receiver, send, stepSequencer, page=1):
        self.stepSequencer = ss = stepSequencer
        self.receiver = receiver
        self.send = send
        self.page = page
        # Listeners for multifader and toggle widgets
        self._multifader = MultiFader(receiver,
            [partial(self.setVelocity, idx) for idx in range(ss.beats)],
            page)
        self._multitoggle = MultiToggle(receiver,
            [[partial(ss.setStep, c, r) for c in range(ss.beats)]
             for r in range(len(ss.notes))], page)

    def attach(self):
        ss = self.stepSequencer
        clock = ss.clock
        beats = ss.beats
        #players = self.players
        #self.step = 0
        ss.step = 0

        # Clear out the multifader and toggle widgets
        for beat in range(1, beats + 1):
            for index in range(1, len(ss.notes) + 1):
                self.send(MultiToggle.addressPattern % (
                          self.page, index, beat),
                          ss.on_off[beat - 1][index - 1])
        for beat in range(1, beats + 1):
            self.send(MultiFader.addressPattern % (self.page, beat),
                      ss.velocity[beat - 1] / 127.)

        self._multifader.attach()
        self._multitoggle.attach()

        self._led_schedule = clock.schedule(self.updateLEDs
                ).startLater(1, 1. / beats)
        self._refresh_col = 0
        self._refresh_ui_schedule = clock.schedule(self.refreshUI
                ).startLater(1, 0.0625)
        return self

    def detach(self):
        self._led_schedule.stopLater(0)
        self._refresh_ui_schedule.stopLater(0)
        self._multifader.detach()
        self._multitoggle.detach()

    def updateLEDs(self):
        ss = self.stepSequencer
        on = ss.step + 1
        off = on - 1
        off = off or ss.beats
        self.send(self.ledAddressPattern % (self.page, on), 1.0)
        self.send(self.ledAddressPattern % (self.page, off), 0.0)
        # really only want this for udp, but alas
        self.send(self.ledAddressPattern % (self.page, on), 1.0)
        self.send(self.ledAddressPattern % (self.page, off), 0.0)

    def setVelocity(self, idx, v):
        nv = int(v * 127)
        self.stepSequencer.setVelocity(idx, nv)

    def refreshUI(self):
        ss = self.stepSequencer
        col = ss.on_off[self._refresh_col]
        for (index, on_off) in enumerate(col):
            self.send(MultiToggle.addressPattern %
                      (self.page, index + 1, self._refresh_col + 1), on_off)
        for beat in range(ss.beats):
            self.send(MultiFader.addressPattern % (self.page, beat + 1),
                      ss.velocity[beat] / 127.)
        self._refresh_col = (self._refresh_col + 1) % ss.beats
