import os
import random
import time
import json

from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet import reactor
from twisted.python.filepath import FilePath
from twisted.python.reflect import namedAny

from bl.scheduler import Tempo, Meter, BeatClock
from bl import scheduler
from bl.testlib import TestReactor, ClockRunner
from bl.instrument.fsynth import Instrument, Recorder


Instrument.recorder = Recorder()


here = FilePath(os.path.dirname(__file__))


class SongsAreOkTestCase(TestCase, ClockRunner):

    sleep = float(os.environ.get('BL_TESTSONGS_SLEEP', 0))

    def setUp(self):
        random.seed(0)
        testReactor = TestReactor()
        clockBefore = BeatClock.defaultClock
        self.clock = BeatClock(reactor=testReactor, default=True)
        self.patch(Instrument, 'recorder', Recorder(self.clock))
        def reset():
            BeatClock.defaultClock = clockBefore
            scheduler.clock = clockBefore
        self.addCleanup(reset)


    @inlineCallbacks
    def spin(self, amount):
        for i in xrange(amount):
            self.runTicks(1)
            d = Deferred()
            reactor.callLater(self.sleep, d.callback, None)
            yield d

    def assertEqualsLastRecording(self, basename):
        jsonPath = here.child('data').child(basename + '.json')
        recorded = Instrument.recorder.toDict()
        recorded = json.loads(json.dumps(recorded))
        if not jsonPath.exists():
            print 'Serializing recording to %s' % jsonPath.path
            fd = jsonPath.open('w')
            fd.write(json.dumps(recorded))
            fd.close()
        d = json.loads(jsonPath.open('r').read())
        self.assertEqual(recorded, d)


def method(basename):
    def test_song(self):
        mod = namedAny('tutor.%s' % basename)
        d = self.spin(96 * 8)
        def check(result):
            self.assertEqualsLastRecording(basename)
        return d.addCallback(check)
    return test_song


for child in here.parent().globChildren('song*'):
    basename, _ = os.path.splitext(child.basename())
    setattr(SongsAreOkTestCase, 'test_%s' % basename, method(basename))


