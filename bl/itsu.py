"""
Playing with the concept of a non-isochronous, but strongly timed clock.
"""
import sys

from twisted.python import log
from twisted.python.components import proxyForInterface
from twisted.internet.interfaces import IReactorTime
from twisted.internet.base import DelayedCall


class NonIsochronousClock(proxyForInterface(IReactorTime,
                                            originalAttribute='reactor')):

    singleton = None

    def __init__(self, reactor=None):
        if reactor is None:
            from twisted.internet import reactor
        self.reactor = reactor
        self.parent = None
        self._seconds = reactor.seconds()
        self.children = []
        if NonIsochronousClock.singleton is None:
            NonIsochronousClock.singleton = self

    def registerChild(self, clock):
        clock.parent = self
        self.children.append(clock)

    def seconds(self):
        return self._seconds

    def callLater(self, _seconds, _f, *args, **kw):
        assert callable(_f), "%s is not callable" % _f
        assert sys.maxint >= _seconds >= 0, \
               "%s is not greater than or equal to 0 seconds" % (_seconds,)
        tple = DelayedCall(self.seconds() + _seconds, _f, args, kw,
                           self.reactor._cancelCallLater,
                           self.reactor._moveCallLaterSooner,
                           seconds=self.reactor.seconds)
        self.reactor._newTimedCalls.append(tple)
        return tple


    def runUntilCurrent(self):
        if self.parent is None:
            self.reactor.runUntilCurrent()
            self._seconds = self.reactor.seconds()
            for clock in self.children:
                clock.runUntilCurrent()
        else:
            self._seconds = self.parent.seconds()


    def run(self, installSignalHandlers=True):
        self.reactor.startRunning(installSignalHandlers=installSignalHandlers)
        self.mainLoop()


    @property
    def running(self):
        return self.reactor.running

    def mainLoop(self):
        while self.reactor._started:
            try:
                while self.reactor._started:
                    # Advance simulation time in delayed event
                    # processors.
                    self.runUntilCurrent()
                    t2 = self.reactor.timeout()
                    t = self.reactor.running and t2
                    self.reactor.doIteration(t)
            except:
                log.msg("Unexpected error in main loop.")
                log.err()
            else:
                log.msg('Main loop terminated.')

