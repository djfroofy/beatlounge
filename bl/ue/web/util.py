from functools import wraps

from bl.ue.web.exceptions import ApiError

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

