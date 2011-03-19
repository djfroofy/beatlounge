"""
Some things to interconvert txbeatlounge.music.<notes|scales|chords>

Theoretically .. for now it's just stuff I didn't want crowding my namespaces.
"""



def notesStringsForList(li):
    """
    Pass in a list and get out the str() letters that are in there.
    """

    retD = {}
    for note in li:
        if note in C:
            retD['C'] = True
        elif note in Df:
            retD['Df'] = True
        elif note in D:
            retD['D'] = True
        elif note in Ef:
            retD['Ef'] = True
        elif note in E:
            retD['E'] = True
        elif note in F:
            retD['F'] = True
        elif note in Gf:
            retD['Gf'] = True
        elif note in G:
            retD['G'] = True
        elif note in Af:
            retD['Af'] = True
        elif note in A:
            retD['A'] = True
        elif note in Bf:
            retD['Bf'] = True
        elif note in B:
            retD['B'] = True

    return set(retD.keys())

def flattenLists(li):
    """
    Takes a list of lists and returns a flat list of the submembers
    """
    ret = []
    for l in li:
        ret.extend(l)
    return ret


_midi = lambda v : (v > 127) and (v - 12) or v

def invertChord(chord, inversion=1):
    if inversion < 0 or inversion > 4:
        raise ValueError('inversion argument must be one of: 0, 1, 2, 3, 4')
    if not inversion:
        return chord
    first = _midi(chord[0] + 12)
    second = chord[1]
    third = chord[2]
    if inversion >= 2:
        second = _midi(chord[1] + 12)
    if inversion >= 3:
        third = _midi(chord[2] + 12)
    if len(chord) >= 4:
        fourth = chord[3]
        if inversion >= 4:
            fourth = _midi(chord[3] + 12)
    if len(chord) == 3:
        return [ first, second, third ]
    return [ first, second, third, fourth ] + chord[4:]



