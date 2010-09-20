
from twisted.internet.defer import Deferred, succeed
from twisted.internet.task import LoopingCall


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
        self.func(*args, **kwargs)
        self.count = self.count + 1
        self.on_count(self.scheduled_event, self.count)


    def __repr__(self):
        return 'CountingProxy(%r)' % self.func

class ScheduledEvent(object):

    def __init__(self, task, clock):
        self.task = task
        self.clock = clock

    def start(self, interval, now=True):
        self.task.start(interval, now)
        return self
       
    def start_later(self, when, interval):
        self.clock.callLater(when, lambda : self.task.start(interval, True))
        return self
 
    def stop_at_interval(self, interval):
        self.clock.callLater(interval, self.task.stop)
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

    def __init__(self, clock=None):
        if clock is None:
            from twisted.internet import reactor as clock
        self.clock = clock


    def schedule(self, func, *args, **kw):
        task = LoopingCall(CountingProxy(func), *args, **kw)
        task.clock = self.clock
        task.f.scheduled_event = scheduled = ScheduledEvent(task, self.clock)
        return scheduled
        

schedule = Scheduler().schedule

