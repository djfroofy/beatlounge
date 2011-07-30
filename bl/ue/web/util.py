import os
from functools import wraps

from bl.player import R, W, N
from bl.ue.web.exceptions import ApiError
from bl.ue.web import base32


__all__ = ('checkClassAvailable', 'encodeKwargs', 'decodeValues', 'newTuple',
           'generateBlid')

def checkClassAvailable(klassName, klass):
    def decorator(f):
        @wraps(f)
        def wrapper(*a, **k):
            if not klass:
                raise ApiError('%r is not available' % klassName)
            return f(*a, **k)
        return wrapper
    return decorator

def encodeKwargs(kw):
    return dict((str(k), v) for (k,v) in kw.items())



_EVAL_NS = {
    'R':R,
    'W':W,
    'N':N }
_ALLOWED_NAMES = set(_EVAL_NS.keys())

_s = lambda seq : ','.join(seq)

def decodeValues(values):
    """
    A client can send us some values as JSON deserializes:

        [1, 2, 3, "R(2,3,3,4)", 5]

    We want to decode this into something we can understand:

        [1, 2, 3, R(2,3,3,4), 5]

    So decodeValues(decoded_json_array) is how we partay.

    Note, string expressions in a list are eval'ed only if they
    use these names: R, W, N.

    Otherwise, we raise an ApiError on you.
    """
    for value in values:
        if type(value) in (int, float):
            yield value
        else:
            c = compile(value, '<string>', 'eval')
            names = set(c.co_names)
            if not names.issubset(_ALLOWED_NAMES):
                raise ApiError('Unallowed names in values: %s. Allowed: %s' %
                               (_s(names - _ALLOWED_NAMES), _s(_ALLOWED_NAMES)))
            value = eval(value, _EVAL_NS, _EVAL_NS)
            yield value


def newTuple(tup, add=(), remove=()):
    return tuple((set(tup) - set(remove)).union(set(add)))


def generateBlid(bits=256):
    """
    Make a scure BLID which is a Swiss Number of bits.
    """
    swnum = os.urandom(bits/8)
    return base32.encode(swnum)


