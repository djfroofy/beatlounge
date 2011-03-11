from twisted.python import log


from txbeatlounge.utils import getClock
from txbeatlounge.scheduler import measuresToTicks


class LoopRecorder(object):

    def __init__(self, measures=1, clock=None, meter=None):
        self.clock = getClock(clock)
        if meter is None:
            meter = self.clock.meters[0]
        self.meter = meter
        self.period = measuresToTicks(measures)
        self._loops = []
        self._buffer = []
        self._last_ticks = self.clock.ticks

    def record(self, event):
        ticks = self.clock.ticks
        revent = (event, self.meter.ticks(self.clock.ticks))
        if (ticks - self._last_ticks) >= self.period and self._buffer:
            if not self._loops:
                self._loops.append(self._buffer)
            else:
                last = self._loops[-1]
                if last != self._buffer:
                    self._loops.append(self._buffer)
                    self._loops = self._loops[-10:]
            self._buffer = []
            self._last_ticks = self.meter.ticksPerMeasure * self.meter.measure(ticks)
        if not self._buffer:
            self._last_ticks = self.meter.ticksPerMeasure * self.meter.measure(ticks)
        self._buffer.append(revent)
        
    def latch(self, index=0):
        backindex = -(index + 1)
        return self._loops[backindex]


