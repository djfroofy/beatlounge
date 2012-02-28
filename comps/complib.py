import os.path

from bl.scheduler import clock
from bl.instrument.fsynth import Instrument, MultiInstrument

def sf2(sf2name):
    here = os.path.dirname(__file__)
    path = os.path.join(os.path.dirname(here), 'comps/sf2', sf2name)
    return path

kit_f = lambda connection='mono': Instrument(sf2('kit.sf2'), connection=connection)
bass_f = lambda connection='mono': Instrument(sf2('bass.sf2'), connection=connection)
piano_f = lambda connection='mono': Instrument(sf2('piano.sf2'), connection=connection)
# other_f = lambda connection='mono': Instrument(sf2('me/other.sf2'), connection=connection)


