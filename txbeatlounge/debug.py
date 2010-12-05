
class _Debug(object):
    debug = False

    def __nonzero__(self):
        return self.debug

DEBUG = _Debug()

def setDebug(debug):
    DEBUG.debug = debug

