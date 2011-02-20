
# Synchronization componetns which can be plugged into a BeatClock

import math
import time
import datetime


class SystemClock:

    def __init__(self, beatclock, startTime = None):
        self.beatclock = beatclock
        if not startTime:
            now = datetime.datetime.utcnow()
            sdt = datetime.datetime(now.year, now.month, now.day)
            startTime = time.mktime(sdt.utctimetuple())
        self._start = startTime

    def lastTick(self):
        delta = time.time() - self._start
        bps = self.beatclock.tempo / 60. * 24
        tick = math.floor(bps * delta)
        return int(tick), self._start + (tick / bps)


