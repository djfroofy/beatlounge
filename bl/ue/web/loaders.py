import os

from zope.interface import Interface, implements, Attribute

from bl.ue.web.exceptions import ApiError
from bl.ue.web.util import checkClassAvailable

try:
    from bl.instrument.fsynth import Instrument as FluidSynthInstrument
except ImportError:
    FluidSynthInstrument = None


loaders = {}

class ILoader(Interface):

    loaderType = Attribute("""The type of loader (a string)""")

    def load(**args):
        """
        Load an sound object with the given arguments.
        """


class FluidSynthInstrumentLoader:
    implements(ILoader)

    loaderType = 'fluidsynth'

    def __init__(self, baseDirectory):
        self.baseDirectory = baseDirectory

    @checkClassAvailable('FluidSynthInstrument', FluidSynthInstrument)
    def load(self, uri, connection='mono'):
        if not FluidSynthInstrument:
            raise ApiError('fluidsynth is not avaiable')
        path = os.path.join(self.baseDirectory, uri)
        return FluidSynthInstrument(path, connection=connection)


#loaders[FluidSynthInstrumentLoader.loaderType] = FluidSynthInstrumentLoader



