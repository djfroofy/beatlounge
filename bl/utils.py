from twisted.python import reflect


def getClock(clock=None):
    if clock is None:
        from bl.itsu import NonIsochronousClock
        return NonIsochronousClock.singleton
    return clock


def buildNamespace(*modules):
    d = {}
    for module in modules:
        if isinstance(module, basestring):
            try:
                module = reflect.namedModule(module)
            except ImportError:
                continue
        if hasattr(module, '__all__'):
            names = module.__all__
        else:
            names = [name for name in  dir(module) if name[0] != '_']
        for name in names:
            if not hasattr(module, name):
                continue
            d[name] = getattr(module, name)
    return d


def exhaustCall(v):
    """
    Get an uncallable value at the end of a call chain or `v` itself
    if `v` is not callable.
    """
    while callable(v):
        v = v()
    return v
