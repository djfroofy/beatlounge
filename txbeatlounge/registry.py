
from contextlib import contextmanager

from zope.interface import Interface, implements, Attribute


class IRegistry(Interface):
    """
    A Registry with contexts that can be pushed and popped. Pushing
    a context allows us to "hide" objects in any parent context. Popping
    "unhides" those objects in the parent context.
    """

    currentContext = Attribute("""
        The name of the current context""")


    def contexts(directChildrenOnly=False):
        """
        Return list of context names of the current and all descendants unless
        directChildrenOnly is True in which case only the immediate children
        will be returned.
        """

    def push(name):
        """
        Add a new context to the registry or switch to context `name` is if
        it already exists and is an immediate child, Until pop() is called only
        objects in this context and children can be added or removed.
        Other methods such as len() only reflect the number of object
        in current and child contexts.

        Note that from the root context, only names not equals to __root_
        may be pushed. From other descendant context of root, anyname may
        be pushed and will be namespaced on the parent context as:

            <parent-name>:<pushed-name>

        raise: RegistryError if (1) the name of the context to be pushed contains
            a ':' which is reserved for name-spacing, or (2) the name is __root__
            and the current context is __root__.
        """


    def pop():
        """
        Pop the last context pushed. Popping does not unregister objects
        in the popped context but restores our ability to query and remove
        objects in the parent context. Objects in all descendant contexts
        will still be queryable and removable.

        raise: RegistryError if the current context is __root__
        """

    def add(obj):
        """
        Add an object to the current context.

        raise: RegistryError if obj has already been added to a descendant
               or parent context.
        """

    def remove(obj):
        """
        Remove and object from the current context.

        raise: RegistryError if obj is not in current context of any descendant
               context.
        """

    def get(index):
        """
        Get object at index within current and descendant contexts
        """

    def __len__():
        """
        The number of objects in the current and descendant contexts.
        """

    def __iter__():
        """
        Iterate objects in the current and descendant contexts.
        """

    def __enter__():
        """
        Do nothing.
        """

    def __exit__(type, value, traceback):
        """
        Call pop() and re-raise any exception passed.
        """


class RegistryError(Exception):
    pass


class Registry(object):

    implements(IRegistry)

    currentContext = '__root__'

    def __init__(self):
        self._contexts = ( self.currentContext, [] )
        self._stack = [ self._contexts ]
        self._names = [ self.currentContext ] 

    def contexts(self, directChildrenOnly=Fasle):
        if not directChildrenOnly:
            return self._names
        current = self._stack[-1]
        return  [ entry[0] for entry in current ]

    def push(self, name):
        if self.currentContext == '__root__' and name == '__root__':
            raise RegistryError('Invalid name from root context: __root__!')
        current = self._stack[-1]
        for entry in current:
            if entry[0] == name:
                self._stack.append(entry)

    def pop(self):
        pass

    def add(self, obj):
        pass

    def remove(self, obj):
        pass

    def get(self, index):
        pass

    def __len__(self):
        return 0

    def __iter__(self):
        return iter([])

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass






