import random
from bl.ugen import N


__all__ = ['explode', 'cut']


def explode(notes, factor=2):
    notes2 = []
    f = factor - 1
    for note in notes:
        notes2.append(note)
        for i in range(f):
            notes2.append(N)
    return notes2


def cut(notes, aprob=0.25, bprob=0.25):
    size = len(notes)
    m = size / 2
    if random.random() <= bprob:
        if random.random() <= 0.5:  # half chop
            slice = _cut(notes[m:])
            notes = notes[:m] + slice
        else:  # quarter chop
            s = m + m / 2
            if random.random() <= bprob:
                slice = _cut(notes[s:])
                notes = notes[:s] + slice
            else:
                slice = _cut(notes[m:s])
                notes = notes[:m] + slice + notes[s:]

    if random.random() <= aprob:
        if random.random() <= 0.5:
            slice = _cut(notes[:m])
            notes = slice + notes[m:]
        else:
            s = m / 2
            if random.random() <= bprob:
                slice = _cut(notes[:s])
                notes = slice + notes[s:]
            else:
                slice = _cut(notes[s:m])
                notes = notes[:s] + slice + notes[m:]
    return notes


def _cut(notes):
    size = len(notes)
    if notes[0] == N:
        for (first, note) in enumerate(notes):
            if note != N:
                break
        repeat = size / (first + 1)
        notes = (notes[:first + 1] * repeat)[:size]
        notes.extend([N] * (size - len(notes)))
        return notes
    if size >= 8 and random.random() <= 0.10:
        rv = notes[:4] * (size / 4)
        return rv
    if size >= 4 and random.random() <= 0.75:
        rv = notes[:2] * (size / 2)
        return rv
    rv = [notes[0]] * size
    return rv
