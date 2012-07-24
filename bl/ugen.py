import math
import random
from itertools import cycle

from bl.utils import getClock, exhaustCall


__all__ = [
    'N', 'Cycle', 'C', 'Random', 'R', 'RandomPhrase', 'RP', 'RandomWalk', 'RW',
    'W', 'Weight', 'Oscillate', 'O', 'LinearOsc', 'LSystem'
]


class _Nothing(object):

    def __str__(self):
        return 'N'

    def __repr__(self):
        return 'N'

    def __call__(self):
        return None

    def __nonzero__(self):
        return False


N = _Nothing()


class _CyclicSampler(object):

    _cycle = None

    def __call__(self, c):
        if self._cycle is None:
            self._cycle = cycle(c)
        return self._cycle.next()


def _sample(sample=None, c=()):
    if sample is None:
        sample = _CyclicSampler()
    return lambda: sample(c)


def Cycle(*c):
    return _sample(c=c)


C = Cycle


def Oscillate(*c):
    c = list(c) + list(reversed(c[1:-1]))
    return _sample(c=c)


O = Oscillate


def Random(*c):
    return _sample(random.choice, c)


R = Random


def _randomPhraseGen(phrases):
    while 1:
        phrase = random.choice(phrases)
        for next in phrase:
            yield next


def RandomPhrase(phrases=(), length=None):
    if length is not None:
        for phrase in phrases:
            if len(phrase) != length:
                raise ValueError('Phrase %s is not of specified length: %s' %
                                (phrase, length))
    return _randomPhraseGen(phrases).next


RP = RandomPhrase


def _randomWalk(sounds, startIndex=None):
    ct = len(sounds)
    if startIndex is None:
        index = random.randint(0, ct - 1)
    else:
        index = startIndex
    direction = 1
    while 1:
        yield sounds[index]
        if index == 0:
            direction = 1
        elif index == ct - 1:
            direction = -1
        else:
            if random.randint(0, 1):
                direction *= -1
        index += direction


def RandomWalk(sounds, startIndex=None):
    return _randomWalk(sounds, startIndex).next


RW = RandomWalk


def _weighted(*notes):
    ws = []
    for (note, weight) in notes:
        ws.extend([note for w in range(weight)])
    random.shuffle(ws)
    return ws


def Weight(*weights):
    ws = _weighted(*weights)
    return R(*ws)


W = Weight


def _intceil(n):
    return int(math.ceil(n))


class LinearOsc(object):

    def __init__(self, points, duration=(1, 1), clock=None, meter=None,
                 transform=_intceil):
        self.clock = getClock(clock)
        if meter is None:
            meter = self.clock.meter
        self.meter = meter
        self.duration = self.clock.meter.divisionToTicks(*duration)
        self._buildTable(points, transform)

    def _buildTable(self, points, transform):
        lastTime, lastValue = (0, 0)
        self._table = []
        startValue = points[0][1]
        for (interval, value) in points:
            interval = self.meter.divisionToTicks(*interval)
            offset = lastTime + interval
            steps = offset - lastTime
            if not steps:
                lastValue = value
                continue
            slope = (value - lastValue) / float(steps)
            for i in range(steps):
                self._table.append(transform(lastValue + i * slope))
            lastTime, lastValue = offset, value
        steps = self.duration - lastTime
        if steps:
            slope = (startValue - lastValue) / float(steps)
            for i in range(steps):
                self._table.append(transform(lastValue + i * slope))

    def __call__(self):
        return self._table[self.clock.ticks % self.duration]


class LSystem(object):

    maxSize = 4092
    _halted = False

    def __init__(self, rules, axiom, iterations=None):
        self.rules = rules
        self._validateRules()
        self._current = [exhaustCall(axiom)]
        self._gen = self._systemGenerator()
        if iterations is not None:
            self.pregenerate(iterations)

    def __call__(self):
        return self._gen.next()

    def _validateRules(self):
        for axiom, production in self.rules.iteritems():
            for element in production:
                assert element in self.rules, (
                       'No axiom found for element %s in production %s->%s' %
                       (element, axiom, production))

    def _systemGenerator(self):
        while True:
            if self._halted:
                for node in cycle(self._current):
                    yield node
            played = []
            for node in self._current:
                production = self.rules[node]
                for element in production:
                    yield element
                played.extend(production)
            if len(played) >= self.maxSize:
                self._halted = True
            self._current = list(played)

    def pregenerate(self, iterations):
        """
        Pregenerate L-System productions for given number of iterations.
        """
        played = []
        for i in xrange(iterations):
            played = []
            for node in self._current:
                production = self.rules[node]
                played.extend([e for e in production])
            self._current = list(played)
        self._halted = True
