import random
from itertools import cycle


__all__ = ['N', 'Cycle', 'C', 'Random', 'R', 'RandomPhrase', 'RP',
           'RandomWalk', 'RW', 'W', 'Weight', 'Oscillate', 'O']


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
