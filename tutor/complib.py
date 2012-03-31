import os.path

from bl.scheduler import clock
from bl.instrument.fsynth import Instrument, MultiInstrument

_HERE = os.path.dirname(__file__)

def sf2(sf2name):
    path = os.path.join(_HERE, 'sf2', sf2name)
    return path

def kitFactory(kit_name):
    def f(connection='mono'):
        return Instrument(sf2(kit_name), connection=connection)
    return f

drums_f = kit_f = kitFactory('kit.sf2')
bass_f = kitFactory('bass.sf2')
piano_f = kitFactory('piano.sf2')



