

class ApiError(Exception):
    pass


class StorageError(ApiError):
    def __init__(self, message, rootCause=None):
        ApiError.__init__(self, message)
        self.rootCause = rootCause

