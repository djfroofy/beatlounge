from twisted.trial.unittest import TestCase

import bl.debug
from bl.debug import DEBUG, setDebug, debug


class DebugTests(TestCase):

    def setUp(self):
        self._debug = DEBUG.debug
        self.messages = []

        class Log:

            @classmethod
            def msg(cls, message):
                self.messages.append(message)

        self.patch(bl.debug, 'log', Log)

    def tearDown(self):
        DEBUG.debug = self._debug

    def test_setDebug(self):
        setDebug(False)
        self.failIf(DEBUG)
        setDebug(True)
        self.assert_(DEBUG)

    def test_debug(self):
        setDebug(False)
        debug('a')
        self.failIf(self.messages)
        setDebug(True)
        debug('b')
        debug('c')
        self.assertEquals(self.messages, ['b', 'c'])
        setDebug(False)
        debug('e')
        self.assertEquals(self.messages, ['b', 'c'])
