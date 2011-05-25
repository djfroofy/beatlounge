
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
            ('sfdir', 's', 'journey/sf2', 'Directory containing sound fonts')]

    def makeService(self, options):
        ms = MultiService()
        site = apiSite(options['sfdir'])
        strports.service('tcp:%s:interface=%s' % (options['port'], options['interface']),
                         site).setServiceParent(ms)
        return ms


serviceMaker = BLRestPlugin()

