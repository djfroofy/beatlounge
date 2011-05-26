

from twisted.trial.unittest import TestCase

from bl.ue.web.util import decodeValues, _ALLOWED_NAMES
from bl.ue.web.exceptions import ApiError

class DecodeValues(TestCase):

    def test_decodeValues(self):
        a = [1, 2, 3, "R(1,2,2)"]
        ad = list(decodeValues(a))
        self.fail("weak")

    test_decodeValues.todo = ('Need some assertions here - but this '
                              'begs "units" module first')

    def test_allowedNamesForEval(self):
        def Nasty(*a):
            import sys
            sys.exit(1)
        a = ["Nasty(1,2,3)",1,2,"R(1,2)"]
        try:
            ad = list(decodeValues(a))
            self.fail("should have raised ApiError")
        except ApiError, e:
            message = str(e)
            self.assertEquals(message, "Unallowed names in values: Nasty. "
                                       "Allowed: %s" % (','.join(_ALLOWED_NAMES)))



