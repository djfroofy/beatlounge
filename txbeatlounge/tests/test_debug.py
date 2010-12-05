from twisted.trial.unittest import TestCase

from txbeatlounge.debug import DEBUG, setDebug

class DebugTests(TestCase):

    def setUp(self):
        self._debug = DEBUG.debug

    def tearDown(self):
        DEBUG.debug = self._debug

    def test_setDebug(self):
        setDebug(False)
        self.failIf(DEBUG)
        setDebug(True)
        self.assert_(DEBUG)
