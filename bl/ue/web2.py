import random
import os
import sys
from pprint import pformat

from twisted.python import log
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.client import Response

from bl.utils import getClock
from bl.player import SchedulePlayer



class Home(Resource):
    isLeaf = True

    def render_GET(self, request):
        # hehe - reloading template support
        return open(html_path).read() #% _authors


class Parent(Resource):
    allowed = ("GET",)

    def __init__(self, arps=[]):
        Resource.__init__(self)
        self.arps = arps
        self.notes = []

    def getChild(self, path, request):
        log.msg('path: %s' % path)

        if not path or path == '/':
            return Home()

        if path == 'favicon.ico':
            return Response('')

        return ArpEvent(path, self)


class PosterChild(Resource):
    allowed = ("POST",)
    isLeaf = True

    def __init__(self, path, parent):
        Resource.__init__(self)
        self.path = path
        self.parent = parent


class ArpEvent(PosterChild):

    def __init__(self, path, parent):
        PosterChild.__init__(self, path, parent)

    def render_POST(self, request):
        arps = self.parent.arps

        if request.args.get('on'):
            self.parent.notes.append(int(request.args['on'][0]))

        else:
            self.parent.notes.remove(int(request.args['off'][0]))

        for a in arps:
            a.reset(self.parent.notes)

        # TODO: push this back to the browser(s)
        print self.parent.notes
        return 'ok'



HERE = os.path.dirname(__file__)
_authors = ['Drew Smathers', 'Skylar Saveland']
random.shuffle(_authors)
html_path = os.path.join(HERE, 'web2.html')


def start():
    from twisted.internet import reactor
    clock = getClock()
    resource = Parent()
    factory = Site(resource)
    reactor.listenTCP(9090, factory)
    return resource


