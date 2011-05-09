import random
import os
import sys
from pprint import pformat

from twisted.python import log
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.client import Response
from twisted.web.server import NOT_DONE_YET
from twisted.web.template import Element, renderer, XMLFile, flattenString

from bl.utils import getClock
from bl.player import SchedulePlayer

_here = os.path.dirname(__file__)
_authors = ['Drew Smathers', 'Skylar Saveland']

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

    def noteoff(self, when, note):
        self.grid[when][note] = 0


class RootElement(Element):
    loader = XMLFile(os.path.join(_here, 'stepseq.html'))

    @renderer
    def title(self, request, tag):
        random.shuffle(_authors)
        tag.fillSlots(authors=', '.join(_authors))
        return tag

    @renderer
    def form(self, request, tag):
        tag.fillSlots(sid=str(request.sid))
        return tag


class StepSequencerPage(Resource):
    allowed = ("GET",)
    addSlash = True

    def __init__(self, instrFactory):
        Resource.__init__(self)
        self.instrFactory = instrFactory
        self.sessions = []

    def render_GET(self, request):
        clock = getClock()
        stepSequencer = StepSequencer()
        instr = self.instrFactory()
        player = SchedulePlayer(instr, stepSequencer)
        session = {
            'sequencer': stepSequencer,
            'player': player,
        }
        clock.callAfterMeasures(1, player.play)
        request.sid = len(self.sessions)
        self.sessions.append(session)
        request.write('<!DOCTYPE html>\n')
        flattenString(request, RootElement()).addCallback(self._templateRendered, request)
        return NOT_DONE_YET

    def _templateRendered(self, html, request):
        request.write(html)
        request.finish()


class NoteEventHandler(Resource):
    allowed = ("POST",)
    isLeaf = True
    parent = None

    def _parse_request(self, request):
        node = request.path.split('/')[-1]
        id, command, when, note = node.split('-')
        return int(id), command, int(when), int(note)

    def render_POST(self, request):
        id, command, when, note = self._parse_request(request)
        session = self.parent.sessions[id]
        stepSequencer = session['sequencer']
        if command == 'on':
            stepSequencer.noteon(when, note)
        else:
            stepSequencer.noteoff(when, note)
        return 'ok'



def start(instrFactory):
    from twisted.internet import reactor
    root = Resource()
    seqPage = StepSequencerPage(instrFactory)
    root.putChild('stepseq', seqPage)
    noteEventHandler = NoteEventHandler()
    noteEventHandler.parent = seqPage
    seqPage.putChild('notes', noteEventHandler)
    factory = Site(root)
    reactor.listenTCP(9090, factory)
    return root, seqPage




