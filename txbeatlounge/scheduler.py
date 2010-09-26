from functools import wraps

from zope.interface import implements

from twisted.internet.interfaces import IReactorTime
from twisted.internet.defer import Deferred, succeed
from twisted.internet.task import LoopingCall

from fluidsynth import Synth


class BeatReactor(object):
    audioDevice = 'coreaudio'
    synth = Synth()

    def __init__(self, reactor=None):
        if reactor is None:
            from twisted.internet import reactor
        self.reactor = reactor

    def run(self):
        self.synth.start(self.audioDevice)
        self.reactor.run()

    def __getattr__(self, attr):
        return getattr(self.reactor, attr)

class CountingProxy(object):

    count = 0
    max_count = -1
    scheduled_event = None

    def __init__(self, func):
        self.func = func
        self.threshold_reached = lambda se, c : None

    def on_count(self, scheduled_event, count):
        if count == self.max_count:
            self.threshold_reached(scheduled_event, count)

    def __call__(self, *args, **kwargs):
        rv = self.func(*args, **kwargs)
        self.count = self.count + 1
        self.on_count(self.scheduled_event, self.count)
        return rv

    def __repr__(self):
        return 'CountingProxy(%r)' % self.func

class ScheduledEvent(object):

    def __init__(self, task, clock, reactor=None):
        self.task = task
        self.clock = clock
        if reactor is None:
            from txbeatlounge.internet import reactor
        self.reactor = reactor

    def start(self, interval, now=True):
        def _start():
            self.task.start(interval, now)
        self.reactor.callWhenRunning(_start)
        return self
       
    def start_later(self, when, interval):
        def _start():
            self.clock.callLater(when, lambda : self.task.start(interval, True))
        self.reactor.callWhenRunning(_start)
        return self
 
    def stop_at_interval(self, interval):
        def _stop():
            self.clock.callLater(interval, self.task.stop)
        self.reactor.callWhenRunning(_stop)
        return self

    def stop_after_iterations(self, iterations):
        counting_proxy = self.task.f
        counting_proxy.max_count = iterations
        counting_proxy.threshold_reached = lambda se, c: self.task.stop()
        return self

    def set_threshold_reached(self, func):
        counting_proxy = self.task.f
        counting_proxy.threshold_reached = func
        return self

    def set_on_count(self, func):
        counting_proxy = self.task.f
        counting_proxy.on_count = func
        return self


class Scheduler(object):

    def __init__(self, clock=None, reactor=None):
        if clock is None:
            from twisted.internet import reactor as clock
        self.reactor = reactor
        self.clock = clock


    def schedule(self, func, *args, **kw):
        task = LoopingCall(CountingProxy(func), *args, **kw)
        task.clock = self.clock
        task.f.scheduled_event = scheduled = ScheduledEvent(task,
            self.clock, self.reactor)
        return scheduled
        

schedule = Scheduler().schedule


class BeatClock(object):
    implements(IReactorTime)

    def __init__(self, bpm=135, clock=None):
        if clock is None:
            from twisted.internet import reactor as clock
        self.clock = clock
        self.bpm = bpm
        self.reset()

    def reset(self):
        self.start_seconds = self.clock.seconds()

    def _get_bpm(self):
        return self._bpm
    
    def _set_bpm(self, bpm):
        self._bpm = bpm
        self._time_skew = 60. / float(self._bpm)

    bpm = property(_get_bpm, _set_bpm)

    def callLater(self, beats, f, *a, **k):
        return self.clock.callLater(beats * self._time_skew, f, *a, **k)


    def beats(self):
        return (self.clock.seconds() - self.start_seconds) / self._time_skew


    def cancelCallLater(self, callid):
        return self.clock.concelCallLater(callid)

    def getDelayedCalls(self):
        return self.clock.getDelayedCalls()

    def seconds(self):
        return self.clock.seconds()



class TimedGenerator(object):

    def __init__(self, gen, clock):
        self.gen = gen
        self.clock = clock

    def __call__(self):
        self.on_complete = Deferred()
        self._resume()
        return self.on_complete


    def _resume(self):
        try:
            wait = self.gen.next()
            self.clock.callLater(wait, self._resume)
        except StopIteration:
            self.on_complete.callback(None)

class Timely(object):

    def __init__(self, clock):
        self.clock = clock

    
    def __call__(self, f):
        @wraps(f)
        def wrapper(*a, **k):
            gen = f(*a, **k)
            return TimedGenerator(gen, self.clock)()
        return wrapper

