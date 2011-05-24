
from zope.interface import implements

from twisted.python.usage import Options
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker, IService, MultiService
from twisted.application import strports

from bl.ue.web.api import apiSite
from bl.scheduler import BeatClock

class BLRestPlugin(object):
    implements(IPlugin, IServiceMaker)

    tapname = 'blrest'
    description = 'BL Rest Services'


    class options(Options):
        optParameters = [
            ('port', 'p', 8347, 'Port for REST services to listen on', int),
            ('interface', 'i', '0.0.0.0', 'Interface to listen on (default: 0.0.0.0)'),
            ('tempo', 't', 132, 'Tempo in beats per minute (default: 132)', int) ]

    def makeService(self, options):
        ms = MultiService()
        clock = BeatClock()
        clock.setTempo(options['tempo'])
        site = apiSite(clock)
        strports.service('tcp:%s:interface=%s' % (options['port'], options['interface']),
                         site).setServiceParent(ms)
        clock.run(False)
        return ms


serviceMaker = BLRestPlugin()

