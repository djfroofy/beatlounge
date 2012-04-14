from bl.utils import getClock, exhaustCall
from bl.debug import DEBUG


class SchedulePlayer(object):

    def __init__(self, schedule, clock=None):
        self.schedule = schedule
        self.clock = getClock(clock)
        self.last = 0
        self.paused = True
        self._paused_event = None

    def play(self):
        self.paused = False
        event = self._paused_event
        self._paused_event = None
        self._advance(self.last, self.schedule, event=event)

    def pause(self):
        self.paused = True

    def _advance(self, last, schedule, event=None):
        self.last = last
        if self.paused:
            self._paused_event = event
            return
        if event is not None:
            (func, args) = event

            # TODO exhaustCall is "BAD" b/c we might want to actually pass
            # functions! This should be replaced maybe by exhaustUgens which
            # has prequisite: unit generators (ugens). bl.player's ad-hoc ugens
            # should be put in bl.ugens (new module) and implement IUgen or
            # something

            exhausted_args = dict((k, exhaustCall(v))
                                  for (k,v) in args.iteritems())
            func(**exhausted_args)
        try:
            event = schedule.next()
        except StopIteration:
            return
        if event:
            when, event = exhaustCall(event[0]), event[1:]
            delta = when - last
            if DEBUG:
                log.msg('%r last=%s, when=%s; delta=%s' % (
                        self, last, when, delta))
            if delta < 0:
                log.err(
                    'scheduled value in past? relative last tick=%d, when=%d'
                    % (last, when))
            else:


                # TODO It would be nice to not do this instead override
                # callLater to ensure it really makes a call synchronously. (or
                # maybe that's a horrible idea since it could run into maximum
                # recursion).

                if not delta:
                    self._advance(when, schedule, event)
                else:
                    self.clock.callLater(
                        delta, self._advance, when, schedule, event)

    def startPlaying(self):
        self.clock.callAfterMeasures(0, self.play)

    def stopPlaying(self):
        self.clock.callAfterMeasures(0, self.stop)
