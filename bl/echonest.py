from bl.utils import getClock


def playSegments(segments, instr, clock=None):
    clock = getClock(clock)
    _resumeSegments(clock, instr, segments, 0)


_notes = [60, 61, 62, 63, 64, 67, 68, 69, 70, 71]

def _f(v):
    if v > 126:
        return int(v)
    return 0

def _resumeSegments(clock, instr, segments, index):
    instr.stopall()
    segment = segments[index]
    index += 1
    velocities = [_f(127 * p) for p in segment['pitches']]
    for (note, velocity) in zip(_notes, velocities):
        instr.playnote(note, velocity)
    if index == len(segments):
        return
    clock.callLater(segment['duration'], _resumeSegments,
                    clock, instr, segments, index)

