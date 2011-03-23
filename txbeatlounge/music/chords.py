from twisted.python import log

from txbeatlounge.utils import flattenLists
from txbeatlounge.music import notes, constants


flavs = {
    "maj": [0,4,7,12],
    "min": [0,3,7,12],
    "aug": [0,4,8,12],
    "dim": [0,3,6,12],
    "dim7": [0,3,6,9,12],
    "m7f5": [0,3,6,10,12],
    "min7": [0,3,7,10,12],
    "mM7": [0,3,7,11,12],
    "dom7": [0,4,7,10,12],
    "maj7": [0,4,7,11,12],
    "aug7": [0,4,8,10,12],
    "M7s5": [0,4,8,11,12],
    "9": [0,4,7,10,12,14],
    "11": [0,4,7,10,12,14,17],
    "13": [0,4,7,10,12,14,17,21],
    "maj9": [0,4,7,11,12,14],
    "maj11": [0,4,7,11,12,14,17],
    "maj13": [0,4,7,11,12,14,17,21],
    "min9": [0,3,7,10,12,14],
    "min11": [0,3,7,10,12,14,17],
    "min13": [0,3,7,10,12,14,17,21],
    "sus2": [0,2,7,12],
    "sus4": [0,5,7,12],
}

class RootedChord(object):

    def __init__(self, root=57, flav="maj"):
        if root > 115 or root < 0:
            log.msg(root)
            raise ValueError("root must be between 0 and 115 (maybe less)")
        self.root = root
        self.flav = flav
        #log.msg(flav)
        self.proto = flavs[flav]
        self.list = [notes.MidiNote(root+n) for n in self.proto if 0 <= (root+n) < 128]

    def __repr__(self):
        return repr(self.list)

    def __iter__(self):
        for i in self.list:
            yield i

    def __len__(self):
        return len(self.list)

    def __getitem__(self, i):
        return self.list[i]

    def __add__(self, other):
        return list(self) + list(other)

    def __radd__(self, other):
        return self + other

    def transpose(self, i):
        return [n+i for n in self]

    def freqs(self, intone=None):
        """
        Without intone, we return the equally tempered value.
        Intone may == 'py', in which case, we return the pythagorean tuning.
        Otherwise, we use the just temperament.
        """

        if not intone:
            return [constants.twelve_tone_equal_440[int(n)] for n in self]

        if intone == 'py':
            return [constants.twelve_tone_equal_440[int(n)] * notes.offsets[int(n)-self.root][1] for n in self]

        return [constants.twelve_tone_equal_440[int(n)] * notes.offsets[int(n)-self.root][0] for n in self]


class NamedChord(object):

    def __init__(self, key="C", flav="maj"):
        self.key = key
        self.flav = flav
        #log.msg(key)
        self.root = notes.keys[key] # 0,1,2 ..

    def __repr__(self):
        return "NamedChord(key=%s, flav=%s)" % (self.key, self.flav)

    def __iter__(self):
        for i in self.lists:
            yield i

    def __len__(self):
        return len(self.lists)

    def __getitem__(self, i):
        return self.lists[i]

    def __contains__(self, prospect):
        """
        WARNING: This method is inconsistent with __iter__/__getitem__.
        It's a convenience to be able to say ``9 in chords.Amaj``.

        "for x in y: ..." and "x in y" are supposed to talk about the same elements x.
        """
        return prospect in self.flat

    def transpose(self, i):
        return [n.transpose(i) for n in self]

    @property
    def lists(self):
        ret = []
        root = self.root

        while root < 115:
            chord = RootedChord(root=root, flav=self.flav)
            if all([c < 127 for c in chord]):
                ret.append(chord)
                root += 12
            else:
                break
        return ret

    @property
    def flat(self):
        """return self.lists as a flat list"""
        return list(set(flattenLists(self)))

    @property
    def letters(self):
        ret = []
        for n in self[0]:
            ret.append(notes.keys_rev[int(n)])
        return set(ret)

    def len_intersect(self, other):
        return len(self.intersect(other))

    def intersect(self, other):
        return self.letters.intersection(other.letters)


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


# Major
Cmaj = NamedChord("C", "maj")
Csmaj = Dfmaj = NamedChord("Cs", "maj") #Cmaj.transpose(1) .. would like to preserve type .. 
Dmaj = NamedChord("D", "maj")
Dsmaj = Efmaj = NamedChord("Ds", "maj")
Emaj = NamedChord("E", "maj")
Fmaj = NamedChord("F", "maj")
Fsmaj = Gfmaj =  NamedChord("Fs", "maj")
Gmaj = NamedChord("G", "maj")
Gsmaj = Afmaj = NamedChord("Gs", "maj")
Amaj = NamedChord("A", "maj")
Asmaj = Bfmaj = NamedChord("As", "maj")
Bmaj = NamedChord("B", "maj")


# Minor
Cmin = NamedChord("C", "min")
Csmin = Dfmin = NamedChord("Cs", "min")
Dmin = NamedChord("D", "min")
Dsmin = Efmin = NamedChord("Ds", "min")
Emin = NamedChord("E", "min")
Fmin = NamedChord("F", "min")
Fsmin = Gfmin =  NamedChord("Fs", "min")
Gmin = NamedChord("G", "min")
Gsmin = Afmin = NamedChord("Gs", "min")
Amin = NamedChord("A", "min")
Asmin = Bfmin = NamedChord("As", "min")
Bmin = NamedChord("B", "min")


# Augmented
Caug = NamedChord("C", "aug")
Csaug = Dfaug = NamedChord("Cs", "aug")
Daug = NamedChord("D", "aug")
Dsaug = Efaug = NamedChord("Ds", "aug")
Eaug = NamedChord("E", "aug")
Faug = NamedChord("F", "aug")
Fsaug = Gfaug =  NamedChord("Fs", "aug")
Gaug = NamedChord("G", "aug")
Gsaug = Afaug = NamedChord("Gs", "aug")
Aaug = NamedChord("A", "aug")
Asaug = Bfaug = NamedChord("As", "aug")
Baug = NamedChord("B", "aug")


# Diminished
Cdim = NamedChord("C", "dim")
Csdim = Dfdim = NamedChord("Cs", "dim")
Ddim = NamedChord("D", "dim")
Dsdim = Efdim = NamedChord("Ds", "dim")
Edim = NamedChord("E", "dim")
Fdim = NamedChord("F", "dim")
Fsdim = Gfdim =  NamedChord("Fs", "dim")
Gdim = NamedChord("G", "dim")
Gsdim = Afdim = NamedChord("Gs", "dim")
Adim = NamedChord("A", "dim")
Asdim = Bfdim = NamedChord("As", "dim")
Bdim = NamedChord("B", "dim")


# Diminished seventh
Cdim7 = NamedChord("C", "dim7")
Csdim7 = Dfdim7 = NamedChord("Cs", "dim7")
Ddim7 = NamedChord("D", "dim7")
Dsdim7 = Efdim7 = NamedChord("Ds", "dim7")
Edim7 = NamedChord("E", "dim7")
Fdim7 = NamedChord("F", "dim7")
Fsdim7 = Gfdim7 =  NamedChord("Fs", "dim7")
Gdim7 = NamedChord("G", "dim7")
Gsdim7 = Afdim7 = NamedChord("Gs", "dim7")
Adim7 = NamedChord("A", "dim7")
Asdim7 = Bfdim7 = NamedChord("As", "dim7")
Bdim7 = NamedChord("B", "dim7")


Caug7 = NamedChord("C", "aug7")
Csaug7 = Dfaug7 = NamedChord("Cs", "aug7")
Daug7 = NamedChord("D", "aug7")
Dsaug7 = Efaug7 = NamedChord("Ds", "aug7")
Eaug7 = NamedChord("E", "aug7")
Faug7 = NamedChord("F", "aug7")
Fsaug7 = Gfaug7 =  NamedChord("Fs", "aug7")
Gaug7 = NamedChord("G", "aug7")
Gsaug7 = Afaug7 = NamedChord("Gs", "aug7")
Aaug7 = NamedChord("A", "aug7")
Asaug7 = Bfaug7 = NamedChord("As", "aug7")
Baug7 = NamedChord("B", "aug7")


# Minor 7, flat 5
Cm7f5 = NamedChord("C", "m7f5")
Csm7f5 = Dfm7f5 = NamedChord("Cs", "m7f5")
Dm7f5 = NamedChord("D", "m7f5")
Dsm7f5 = Efm7f5 = NamedChord("Ds", "m7f5")
Em7f5 = NamedChord("E", "m7f5")
Fm7f5 = NamedChord("F", "m7f5")
Fsm7f5 = Gfm7f5 =  NamedChord("Fs", "m7f5")
Gm7f5 = NamedChord("G", "m7f5")
Gsm7f5 = Afm7f5 = NamedChord("Gs", "m7f5")
Am7f5 = NamedChord("A", "m7f5")
Asm7f5 = Bfm7f5 = NamedChord("As", "m7f5")
Bm7f5 = NamedChord("B", "m7f5")


# Minor 7th
Cmin7 = NamedChord("C", "min7")
Csmin7 = Dfmin7 = NamedChord("Cs", "min7")
Dmin7 = NamedChord("D", "min7")
Dsmin7 = Efmin7 = NamedChord("Ds", "min7")
Emin7 = NamedChord("E", "min7")
Fmin7 = NamedChord("F", "min7")
Fsmin7 = Gfmin7 =  NamedChord("Fs", "min7")
Gmin7 = NamedChord("G", "min7")
Gsmin7 = Afmin7 = NamedChord("Gs", "min7")
Amin7 = NamedChord("A", "min7")
Asmin7 = Bfmin7 = NamedChord("As", "min7")
Bmin7 = NamedChord("B", "min7")


CmM7 = NamedChord("C", "mM7")
CsmM7 = DfmM7 = NamedChord("Cs", "mM7")
DmM7 = NamedChord("D", "mM7")
DsmM7 = EfmM7 = NamedChord("Ds", "mM7")
EmM7 = NamedChord("E", "mM7")
FmM7 = NamedChord("F", "mM7")
FsmM7 = GfmM7 =  NamedChord("Fs", "mM7")
GmM7 = NamedChord("G", "mM7")
GsmM7 = AfmM7 = NamedChord("Gs", "mM7")
AmM7 = NamedChord("A", "mM7")
AsmM7 = BfmM7 = NamedChord("As", "mM7")
BmM7 = NamedChord("B", "mM7")


Cdom7 = NamedChord("C", "dom7")
Csdom7 = Dfdom7 = NamedChord("Cs", "dom7")
Ddom7 = NamedChord("D", "dom7")
Dsdom7 = Efdom7 = NamedChord("Ds", "dom7")
Edom7 = NamedChord("E", "dom7")
Fdom7 = NamedChord("F", "dom7")
Fsdom7 = Gfdom7 =  NamedChord("Fs", "dom7")
Gdom7 = NamedChord("G", "dom7")
Gsdom7 = Afdom7 = NamedChord("Gs", "dom7")
Adom7 = NamedChord("A", "dom7")
Asdom7 = Bfdom7 = NamedChord("As", "dom7")
Bdom7 = NamedChord("B", "dom7")


Cmaj7 = NamedChord("C", "maj7")
Csmaj7 = Dfmaj7 = NamedChord("Cs", "maj7")
Dmaj7 = NamedChord("D", "maj7")
Dsmaj7 = Efmaj7 = NamedChord("Ds", "maj7")
Emaj7 = NamedChord("E", "maj7")
Fmaj7 = NamedChord("F", "maj7")
Fsmaj7 = Gfmaj7 =  NamedChord("Fs", "maj7")
Gmaj7 = NamedChord("G", "maj7")
Gsmaj7 = Afmaj7 = NamedChord("Gs", "maj7")
Amaj7 = NamedChord("A", "maj7")
Asmaj7 = Bfmaj7 = NamedChord("As", "maj7")
Bmaj7 = NamedChord("B", "maj7")


CM7s5 = NamedChord("C", "M7s5")
CsM7s5 = DfM7s5 = NamedChord("Cs", "M7s5")
DM7s5 = NamedChord("D", "M7s5")
DsM7s5 = EfM7s5 = NamedChord("Ds", "M7s5")
EM7s5 = NamedChord("E", "M7s5")
FM7s5 = NamedChord("F", "M7s5")
FsM7s5 = GfM7s5 =  NamedChord("Fs", "M7s5")
GM7s5 = NamedChord("G", "M7s5")
GsM7s5 = AfM7s5 = NamedChord("Gs", "M7s5")
AM7s5 = NamedChord("A", "M7s5")
AsM7s5 = BfM7s5 = NamedChord("As", "M7s5")
BM7s5 = NamedChord("B", "M7s5")


C9 = NamedChord("C", "9")
Cs9 = Df9 = NamedChord("Cs", "9")
D9 = NamedChord("D", "9")
Ds9 = Ef9 = NamedChord("Ds", "9")
E9 = NamedChord("E", "9")
F9 = NamedChord("F", "9")
Fs9 = Gf9 =  NamedChord("Fs", "9")
G9 = NamedChord("G", "9")
Gs9 = Af9 = NamedChord("Gs", "9")
A9 = NamedChord("A", "9")
As9 = Bf9 = NamedChord("As", "9")
B9 = NamedChord("B", "9")


C11 = NamedChord("C", "11")
Cs11 = Df11 = NamedChord("Cs", "11")
D11 = NamedChord("D", "11")
Ds11 = Ef11 = NamedChord("Ds", "11")
E11 = NamedChord("E", "11")
F11 = NamedChord("F", "11")
Fs11 = Gf11 =  NamedChord("Fs", "11")
G11 = NamedChord("G", "11")
Gs11 = Af11 = NamedChord("Gs", "11")
A11 = NamedChord("A", "11")
As11 = Bf11 = NamedChord("As", "11")
B11 = NamedChord("B", "11")


C13 = NamedChord("C", "13")
Cs13 = Df13 = NamedChord("Cs", "13")
D13 = NamedChord("D", "13")
Ds13 = Ef13 = NamedChord("Ds", "13")
E13 = NamedChord("E", "13")
F13 = NamedChord("F", "13")
Fs13 = Gf13 =  NamedChord("Fs", "13")
G13 = NamedChord("G", "13")
Gs13 = Af13 = NamedChord("Gs", "13")
A13 = NamedChord("A", "13")
As13 = Bf13 = NamedChord("As", "13")
B13 = NamedChord("B", "13")


Cmaj9 = NamedChord("C", "maj9")
Csmaj9 = Dfmaj9 = NamedChord("Cs", "maj9")
Dmaj9 = NamedChord("D", "maj9")
Dsmaj9 = Efmaj9 = NamedChord("Ds", "maj9")
Emaj9 = NamedChord("E", "maj9")
Fmaj9 = NamedChord("F", "maj9")
Fsmaj9 = Gfmaj9 =  NamedChord("Fs", "maj9")
Gmaj9 = NamedChord("G", "maj9")
Gsmaj9 = Afmaj9 = NamedChord("Gs", "maj9")
Amaj9 = NamedChord("A", "maj9")
Asmaj9 = Bfmaj9 = NamedChord("As", "maj9")
Bmaj9 = NamedChord("B", "maj9")


Cmaj11 = NamedChord("C", "maj11")
Csmaj11 = Dfmaj11 = NamedChord("Cs", "maj11")
Dmaj11 = NamedChord("D", "maj11")
Dsmaj11 = Efmaj11 = NamedChord("Ds", "maj11")
Emaj11 = NamedChord("E", "maj11")
Fmaj11 = NamedChord("F", "maj11")
Fsmaj11 = Gfmaj11 =  NamedChord("Fs", "maj11")
Gmaj11 = NamedChord("G", "maj11")
Gsmaj11 = Afmaj11 = NamedChord("Gs", "maj11")
Amaj11 = NamedChord("A", "maj11")
Asmaj11 = Bfmaj11 = NamedChord("As", "maj11")
Bmaj11 = NamedChord("B", "maj11")


Cmaj13 = NamedChord("C", "maj13")
Csmaj13 = Dfmaj13 = NamedChord("Cs", "maj13")
Dmaj13 = NamedChord("D", "maj13")
Dsmaj13 = Efmaj13 = NamedChord("Ds", "maj13")
Emaj13 = NamedChord("E", "maj13")
Fmaj13 = NamedChord("F", "maj13")
Fsmaj13 = Gfmaj13 =  NamedChord("Fs", "maj13")
Gmaj13 = NamedChord("G", "maj13")
Gsmaj13 = Afmaj13 = NamedChord("Gs", "maj13")
Amaj13 = NamedChord("A", "maj13")
Asmaj13 = Bfmaj13 = NamedChord("As", "maj13")
Bmaj13 = NamedChord("B", "maj13")


Cmin9 = NamedChord("C", "min9")
Csmin9 = Dfmin9 = NamedChord("Cs", "min9")
Dmin9 = NamedChord("D", "min9")
Dsmin9 = Efmin9 = NamedChord("Ds", "min9")
Emin9 = NamedChord("E", "min9")
Fmin9 = NamedChord("F", "min9")
Fsmin9 = Gfmin9 =  NamedChord("Fs", "min9")
Gmin9 = NamedChord("G", "min9")
Gsmin9 = Afmin9 = NamedChord("Gs", "min9")
Amin9 = NamedChord("A", "min9")
Asmin9 = Bfmin9 = NamedChord("As", "min9")
Bmin9 = NamedChord("B", "min9")


Cmin11 = NamedChord("C", "min11")
Csmin11 = Dfmin11 = NamedChord("Cs", "min11")
Dmin11 = NamedChord("D", "min11")
Dsmin11 = Efmin11 = NamedChord("Ds", "min11")
Emin11 = NamedChord("E", "min11")
Fmin11 = NamedChord("F", "min11")
Fsmin11 = Gfmin11 =  NamedChord("Fs", "min11")
Gmin11 = NamedChord("G", "min11")
Gsmin11 = Afmin11 = NamedChord("Gs", "min11")
Amin11 = NamedChord("A", "min11")
Asmin11 = Bfmin11 = NamedChord("As", "min11")
Bmin11 = NamedChord("B", "min11")


Cmin13 = NamedChord("C", "min13")
Csmin13 = Dfmin13 = NamedChord("Cs", "min13")
Dmin13 = NamedChord("D", "min13")
Dsmin13 = Efmin13 = NamedChord("Ds", "min13")
Emin13 = NamedChord("E", "min13")
Fmin13 = NamedChord("F", "min13")
Fsmin13 = Gfmin13 =  NamedChord("Fs", "min13")
Gmin13 = NamedChord("G", "min13")
Gsmin13 = Afmin13 = NamedChord("Gs", "min13")
Amin13 = NamedChord("A", "min13")
Asmin13 = Bfmin13 = NamedChord("As", "min13")
Bmin13 = NamedChord("B", "min13")


Csus4 = NamedChord("C", "sus4")
Cssus4 = Dfsus4 = NamedChord("Cs", "sus4")
Dsus4 = NamedChord("D", "sus4")
Dssus4 = Efsus4 = NamedChord("Ds", "sus4")
Esus4 = NamedChord("E", "sus4")
Fsus4 = NamedChord("F", "sus4")
Fssus4 = Gfsus4 =  NamedChord("Fs", "sus4")
Gsus4 = NamedChord("G", "sus4")
Gssus4 = Afsus4 = NamedChord("Gs", "sus4")
Asus4 = NamedChord("A", "sus4")
Assus4 = Bfsus4 = NamedChord("As", "sus4")
Bsus4 = NamedChord("B", "sus4")


Csus2 = NamedChord("C", "sus2")
Cssus2 = Dfsus2 = NamedChord("Cs", "sus2")
Dsus2 = NamedChord("D", "sus2")
Dssus2 = Efsus2 = NamedChord("Ds", "sus2")
Esus2 = NamedChord("E", "sus2")
Fsus2 = NamedChord("F", "sus2")
Fssus2 = Gfsus2 =  NamedChord("Fs", "sus2")
Gsus2 = NamedChord("G", "sus2")
Gssus2 = Afsus2 = NamedChord("Gs", "sus2")
Asus2 = NamedChord("A", "sus2")
Assus2 = Bfsus2 = NamedChord("As", "sus2")
Bsus2 = NamedChord("B", "sus2")


CHORDS = chord_choices = [
    A11, A13, A9, AM7s5, Aaug, Aaug7, Adim, Adim7, Adom7, Af11, Af13, Af9, AfM7s5, Afaug, Afaug7,
    Afdim, Afdim7, Afdom7, Afm7f5, AfmM7, Afmaj, Afmaj11, Afmaj13, Afmaj7, Afmaj9, Afmin, Afmin11, Afmin13,
    Afmin7, Afmin9, Afsus2, Afsus4, Am7f5, AmM7, Amaj, Amaj11, Amaj13, Amaj7, Amaj9, Amin, Amin11, Amin13,
    Amin7, Amin9, As11, As13, As9, AsM7s5, Asaug, Asaug7, Asdim, Asdim7, Asdom7, Asm7f5, AsmM7, Asmaj,
    Asmaj11, Asmaj13, Asmaj7, Asmaj9, Asmin, Asmin11, Asmin13, Asmin7, Asmin9, Assus2, Assus4, Asus2, Asus4,
    B11, B13, B9, BM7s5, Baug, Baug7, Bdim, Bdim7, Bdom7, Bf11, Bf13, Bf9, BfM7s5, Bfaug, Bfaug7, Bfdim, Bfdim7,
    Bfdom7, Bfm7f5, BfmM7, Bfmaj, Bfmaj11, Bfmaj13, Bfmaj7, Bfmaj9, Bfmin, Bfmin11, Bfmin13, Bfmin7, Bfmin9,
    Bfsus2, Bfsus4, Bm7f5, BmM7, Bmaj, Bmaj11, Bmaj13, Bmaj7, Bmaj9, Bmin, Bmin11, Bmin13, Bmin7, Bmin9, Bsus2,
    Bsus4, C11, C13, C9, CM7s5, Caug, Caug7, Cdim, Cdim7, Cdom7, Cm7f5, CmM7, Cmaj, Cmaj11, Cmaj13, Cmaj7, Cmaj9,
    Cmin, Cmin11, Cmin13, Cmin7, Cmin9, Cs11, Cs13, Cs9, CsM7s5, Csaug, Csaug7, Csdim, Csdim7, Csdom7, Csm7f5,
    CsmM7, Csmaj, Csmaj11, Csmaj13, Csmaj7, Csmaj9, Csmin, Csmin11, Csmin13, Csmin7, Csmin9, Cssus2, Cssus4,
    Csus2, Csus4, D11, D13, D9, DM7s5, Daug, Daug7, Ddim, Ddim7, Ddom7, Df11, Df13, Df9, DfM7s5, Dfaug,
    Dfaug7, Dfdim, Dfdim7, Dfdom7, Dfm7f5, DfmM7, Dfmaj, Dfmaj11, Dfmaj13, Dfmaj7, Dfmaj9, Dfmin, Dfmin11, Dfmin13,
    Dfmin7, Dfmin9, Dfsus2, Dfsus4, Dm7f5, DmM7, Dmaj, Dmaj11, Dmaj13, Dmaj7, Dmaj9, Dmin, Dmin11, Dmin13, Dmin7,
    Dmin9, Ds11, Ds13, Ds9, DsM7s5, Dsaug, Dsaug7, Dsdim, Dsdim7, Dsdom7, Dsm7f5, DsmM7, Dsmaj, Dsmaj11,
    Dsmaj13, Dsmaj7, Dsmaj9, Dsmin, Dsmin11, Dsmin13, Dsmin7, Dsmin9, Dssus2, Dssus4, Dsus2, Dsus4,
    E11, E13, E9, EM7s5, Eaug, Eaug7, Edim, Edim7, Edom7, Ef11, Ef13, Ef9, EfM7s5, Efaug, Efaug7, Efdim,
    Efdim7, Efdom7, Efm7f5, EfmM7, Efmaj, Efmaj11, Efmaj13, Efmaj7, Efmaj9, Efmin, Efmin11, Efmin13, Efmin7,
    Efmin9, Efsus2, Efsus4, Em7f5, EmM7, Emaj, Emaj11, Emaj13, Emaj7, Emaj9, Emin, Emin11, Emin13, Emin7, Emin9,
    Esus2, Esus4, F11, F13, F9, FM7s5, Faug, Faug7, Fdim, Fdim7, Fdom7, Fm7f5, FmM7, Fmaj, Fmaj11, Fmaj13,
    Fmaj7, Fmaj9, Fmin, Fmin11, Fmin13, Fmin7, Fmin9, Fs11, Fs13, Fs9, FsM7s5, Fsaug, Fsaug7, Fsdim, Fsdim7,
    Fsdom7, Fsm7f5, FsmM7, Fsmaj, Fsmaj11, Fsmaj13, Fsmaj7, Fsmaj9, Fsmin, Fsmin11, Fsmin13, Fsmin7, Fsmin9,
    Fssus2, Fssus4, Fsus2, Fsus4, G11, G13, G9, GM7s5, Gaug, Gaug7, Gdim, Gdim7, Gdom7, Gf11, Gf13, Gf9,
    GfM7s5, Gfaug, Gfaug7, Gfdim, Gfdim7, Gfdom7, Gfm7f5, GfmM7, Gfmaj, Gfmaj11, Gfmaj13, Gfmaj7, Gfmaj9, Gfmin,
    Gfmin11, Gfmin13, Gfmin7, Gfmin9, Gfsus2, Gfsus4, Gm7f5, GmM7, Gmaj, Gmaj11, Gmaj13, Gmaj7, Gmaj9, Gmin,
    Gmin11, Gmin13, Gmin7, Gmin9, Gs11, Gs13, Gs9, GsM7s5, Gsaug, Gsaug7, Gsdim, Gsdim7, Gsdom7, Gsm7f5,
    GsmM7, Gsmaj, Gsmaj11, Gsmaj13, Gsmaj7, Gsmaj9, Gsmin, Gsmin11, Gsmin13, Gsmin7, Gsmin9, Gssus2, Gssus4,
    Gsus2, Gsus4
]


