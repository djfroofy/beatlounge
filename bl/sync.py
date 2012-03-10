# Synchronization components which can be plugged into a BeatClock

import math
import time
import datetime

from zope.interface import Interface, implements


class ISyncClock(Interface):
    """
    Canonical source of tick/time information which can be plugged into a
    BeatClock.
    """

    def lastTick():
        """
        Return two-tuple consisting of last tick and timestamp according to the
        provider.
        """


class SystemClock:
    """
    Sync clock based on system time and the given startTime.

    If startTime is not given in constructor, this defaults to midnight of the
    current day.
    """
    implements(ISyncClock)

    def __init__(self, beatclock, startTime=None):
        self.beatclock = beatclock
        if not startTime:
            now = datetime.datetime.utcnow()
            sdt = datetime.datetime(now.year, now.month, now.day)
            startTime = time.mktime(sdt.utctimetuple())
        self._start = startTime

    def lastTick(self):
        delta = time.time() - self._start
        bps = self.beatclock.tempo.bpm / 60. * self.beatclock.tempo.tpb
        tick = math.floor(bps * delta)
        return int(tick), self._start + (tick / bps)
