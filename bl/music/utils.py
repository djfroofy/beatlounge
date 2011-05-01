"""
Some things to interconvert bl.music.<notes|scales|chords>

Theoretically .. for now it's just stuff I didn't want crowding my namespaces.
"""





from bl.notes import C, Df, D, Ef, E, F, Gf, F, Af, A, Bf, B


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




