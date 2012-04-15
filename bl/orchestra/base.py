from bl.utils import getClock, exhaustCall


class SchedulePlayer(object):
    """
    A schedule player plays a "schedule" where a schedule is a generator (has
    next()) that yields 3-tuples of the form:

        (relative_ticks:int, func:function, args:dict)

    C{relative_ticks} is the number of ticks after "resuming" the scheduler
    from its last ticks value (attribue C{last}) (which begins at 0 unless
    customized).  The function C{func} will be scheduled to be called with args
    as keyword arguments, thus your callables should have well-defined
    signature (even after any decoration).
    """

    def __init__(self, schedule, clock=None):
        self.schedule = schedule
        self.clock = getClock(clock)
        self.last = 0
        self.paused = True
        self._paused_event = None
        self._scheduleChildren = []

    def play(self):
        """
        Immediately start playing our schedule. (Generally you should not use
        this method but resumePlaying() instead).
        """
        self.paused = False
        event = self._paused_event
        self._paused_event = None
        self._advance(self.last, self.schedule, event=event)

    def pause(self):
        """
        Immediately pause playing our schedule. (Generally you should not use
        this method but pausePlaying() instead).
        """
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

            exhaustedArgs = dict((k, exhaustCall(v))
                                  for (k,v) in args.iteritems())
            func(**exhaustedArgs)
            stoppedChildren = []
            for child in self._scheduleChildren:
                try:
                    (func, args) = child.next()
                except StopIteration:
                    stoppedChildren.append(child)
                    continue
                exhaustedArgs = dict((k, exhaustCall(v))
                                      for (k,v) in args.iteritems())
                func(**exhaustedArgs)
            for child in stoppedChildren:
                while child in self._scheduleChildren:
                    self._scheduleChildren.remove(child)
        try:
            event = schedule.next()
        except StopIteration:
            return
        if event:
            when, event = exhaustCall(event[0]), event[1:]
            delta = when - last
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

    def addChild(self, schedule):
        """
        A child schedule generator to this SchedulePlayer. A child generator
        cannot generate time but rather functions and arguments to be played in
        tandem with parent schedule:

            (func:function, args:dict)

        This is useful for modulating a set of parameters mapped to multiple
        functions (instruments as an example).
        """
        self._scheduleChildren.append(schedule)

    def resumePlaying(self):
        """
        Resume (or start) playing schedule on the next measure. If paused,
        schedule will resume from where we left off.
        """
        clock = self.clock
        mod = (self.last % clock.meter.ticksPerMeasure)
        delta = clock.untilNextMeasure()
        if mod:
            delta += mod
        self.clock.callLater(delta, self.play)

    def pausePlaying(self):
        """
        Pause playing our schedule on the next measure. To resume playing after
        pausing, call resumePlaying().
        """
        # FIXME Perhaps pause-playing should actually use value 1 here?
        self.clock.callAfterMeasures(0, self.pause)


