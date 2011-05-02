import random
import os
import sys
from pprint import pformat

from twisted.python import log
from twisted.web.resource import Resource
from twisted.web.server import Site

from bl.utils import getClock
from bl.player import SchedulePlayer


class StepSequencer:

    def __init__(self, duration=16*4, octaves=2, offset=48):
        self.duration = duration
        self.grid = [[0 for i in range(octaves * 12)] for j in range(duration)]
        self.offset = offset

    def __iter__(self):
        index = 0
        start = 0
        while 1:
            col = self.grid[index]
            if any(col):
                for (note, on) in enumerate(col):
                    if on:
                        next = (start + index * (96/16), self.offset + note, 120, 24)
                        print 'next:', next
                        yield next
            index += 1
            index %= self.duration
            if not index:
                start += 96 * 4
                yield (start, None, 0, 0)

    def __call__(self):
        return iter(self)

    def noteon(self, when, note):
        self.grid[when][note] = 1
        print 'NOTEON grid:\n', pformat(self.grid)

    def noteoff(self, when, note):
        self.grid[when][note] = 0
        print 'NOTEOFF grid:\n', pformat(self.grid)


class TheStuff(Resource):
    isLeaf = True

    def render_GET(self, request):
        # hehe - reloading template support
        return open(html_path).read() #% _authors

class HaveYouSomeHTMLAndJavascript(Resource):
    allowed = ("GET",)

    def __init__(self, stepSequencer):
        Resource.__init__(self)
        self.stepSequencer = stepSequencer

    def getChild(self, path, request):
        log.msg('path: %s' % path)
        if not path or path == '/':
            return TheStuff()
        if path == 'favicon.ico':
            return Response('')
        return NoteEvent(path, self)


class NoteEvent(Resource):
    allowed = ("POST",)
    isLeaf = True

    def __init__(self, path, parent):
        Resource.__init__(self)
        command, when, note = path.split('-')
        self.command = command
        self.when = int(when)
        self.note = int(note)
        self.parent = parent

    def render_POST(self, request):
        stepSequencer = self.parent.stepSequencer
        if self.command == 'on':
            stepSequencer.noteon(self.when, self.note)
        else:
            stepSequencer.noteoff(self.when, self.note)
        return 'ok'


HERE = os.path.dirname(__file__)
_authors = ['Drew Smathers', 'Skylar Saveland']
random.shuffle(_authors)
html_path = os.path.join(HERE, 'html_web.html')


def start(instr):
    from twisted.internet import reactor
    clock = getClock()
    stepper = StepSequencer()
    resource = HaveYouSomeHTMLAndJavascript(stepper)
    player = SchedulePlayer(instr, stepper)
    clock.callAfterMeasures(1, player.play)
    factory = Site(resource)
    reactor.listenTCP(9090, factory)
    return resource


