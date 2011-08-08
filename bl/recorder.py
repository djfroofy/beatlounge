from twisted.python import log


from bl.utils import getClock


class LoopRecorder(object):
    """
    A LoopRecorder is a simple object for recording arbitrary events as a loop
    over the a duration given in measures. Up to 10 recorded loops can be fetched
    from a FIFO buffer. When a new loop is recorded it is added to the buffer and
    the oldest is removed if capacity exceeds 10.
    """

    def __init__(self, measures=1, clock=None, meter=None):
        self.clock = getClock(clock)
        if meter is None:
            meter = self.clock.meters[0]
        self.meter = meter
        self.period = self.meter.ticksPerMeasure * measures
        self._loops = []
        self._buffer = []
        self._last_ticks = self.clock.ticks

    def record(self, event):
        """
        Record an event. If this the end of the loop duration, and the recorded events
        create a loop different from the past loop, add to recorded stack.
        """
        ticks = self.clock.ticks
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
        elapsed = ticks - self._last_ticks
        self._buffer.append((event, elapsed))

    def latch(self, index=0):
        """
        Return a completed loop. By default, this will return the last complete recorded
        loop, otherwise you can return a past loop (up to 10) with index. For example,
        index=1 will return the loop before the last, ..., index=9, the 10th loop in the past.
        """
        if not self._loops:
            return
        backindex = -(index + 1)
        return self._loops[backindex]


