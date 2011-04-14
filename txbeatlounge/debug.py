
from twisted.python import log

class _Debug(object):
    debug = False

    def __nonzero__(self):
        return self.debug

    def __str__(self):
        return str(self.debug)

    __repr__ = __str__

DEBUG = _Debug()

def setDebug(debug):
    DEBUG.debug = bool(debug)


def debug(message):
    if DEBUG:
        log.msg(message)

