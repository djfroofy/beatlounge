
from zope.interface import implements, Interface


class IStore(Interface):
    """
    Basic interface for document stores.
    """

    def find(**search):
        """
        Find documents matching search.
        """

    def get(**search):
        """
        Get one document matching search.
        """

class IDocument(Interface):
    """
    A document has a simple dict-like interface.
    """

    def __getitem__(name):
        """
        Get value of attribute named `name`
        """

    def __setitem__(name, value):
        """
        Set value of attribute with name `name`
        """



