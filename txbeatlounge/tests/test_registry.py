from zope.interface.verify import verifyClass, verifyObject
from twisted.trial.unittest import TestCase

from txbeatlounge.registry import IRegistry, Registry, RegistryError


class TestRegistryObject(object):
    pass


class RegistryTestCase(TestCase):

    def setUp(self):
        self.registry = Registry()
        self.object1 = TestRegistryObject()
        self.object2 = TestRegistryObject()
        self.object3 = TestRegistryObject()

    def test_registry_interface(self):
        verifyClass(IRegistry, Registry)
        verifyObject(IRegistry, self.registry)

    def test_push_pop(self):
        self.assertEquals(self.registry.contexts(), ['__root__'])
        self.push('foo@localhost')
        self.assertEquals(self.re)
        self.assertEquals(self.registry.contexts(), ['foo@localhost'])
        self.pop()
        self.assertEquals(self.registry.contexts(), ['__root__', 'foo@localhost'])

    def test_default_namespace(self):
        self.registry.add(self.object1)
        self.assertEquals(len(self.registry), 1)
        self.assertIn(self.object1, self.registry)
        self.assertNotIn(self.object2, self.registry)
        self.assertEquals(self.registry.contexts(), ['__root__'])


    def test_registry_context(self):
        self.registry.add(self.object1)
        with self.registry.push('foo@localhost'):
            self.assertEquals(self.registry.contexts(), ['foo@localhost'])
            self.registry.add(self.object2)
            self.assertEquals(len(self.registry), 1)
            self.assertIn(self.object2, self.registry)
        self.assertEquals(len(self.registry), 2)
        self.assertIn(self.object1, self.registry)
        self.assertIn(self.object2, self.registry)
        self.assertEquals(self.registry.contexts(), ['__root__', 'foo@localhost'])

    def test_registry_context_purging(self):
        self.registry.add(self.object1)
        with self.registry.push('foo@localhost'):
            self.registry.add(self.object2)
        self.assertEquals(self.registry.contexts, ['__root__', 'foo@localhost'])
        self.purge('foo@localhost')
        self.assertEquals(self.registry.contexts(), ['__root__'])
        self.assertEquals(len(self.registry), 1)


    def test_registry_context_is_kind_of_isolated(self):
        """
        This isn't java so references can be leaked, but at least in terms of the
        public api we cannot remove some object that belongs in parent context
        from the registry.
        """
        self.registry.add(self.object1)
        with self.registry.push('foo@localhost'):
            self.assertRaises(RegistryError, self.registry.remove, self.object1)
        self.assertIn(self.object1, self.registry)


    def test_registry_context_iteration(self):
        self.registry.add(self.object1)
        with self.registry.push('foo@localhost'):
            self.registry.add(self.object2)
            self.registry.add(self.object3)
            expected = [ self.object2, self.object3 ]
            actual = []
            for obj in self.registry:
                actual.append(obj)
            self.assertEquals(expected, actual)
        expected = [ self.object1, self.object2, self.object3 ]
        actual = []
        for obj in self.registry:
            actual.append(obj)
        self.assertEquals(expected, actual)


    def test_cannot_push_context_with_same_name_as_root(self):
        self.assertRaises(RegistryError, self.registry.push, 'foo@localhost')

    def test_pushing_registry_context_names_after_root_creates_namespaces(self):
        """
        After pushing additional contexts after root, namespacing occurs based on
        the second to root context.
        """
        with self.registry.push('foo@localhost'):
            self.assertEquals(self.registry.contexts(), ['foo@localhost'])
            with self.registry.push('bar'):
                self.assertEquals(self.registry.contexts(), ['foo@localhost:bar'])
                with self.registry.push('baz'):
                    self.assertEquals(self.registry.contexts(), ['foo@localhost:bar:baz'])
                self.assertEquals(self.registry.contexts(), ['foo@localhost:bar',
                                                             'foo@localhost:bar:baz'])
            self.assertEquals(self.registry.contexts(), ['foo@localhost', 'foo@localhost:bar',
                                                         'foo@localhost:bar:baz'])
        self.assertEquals(self.registry.contexts(),
                ['__root__', 'foo@localhost',
                 'foo@localhost:bar', 'foo@localhost:bar:baz'])

    def test_contexts_direct_children_only(self):
        with self.registry.push('foo@localhost'):
            with self.registry.push('raz'):
                pass
        with self.registry.push('bar@localhost'):
            with self.references.push('taz'):
                pass
        self.assertEquals(self.registry.contexts(1),
            ['foo@locahost', 'bar@localhost'])


    def test_get(self):
        self.registry.add(self.object1)
        with self.registry.push('foo@localhost'):
            self.registry.add(self.object2)
            self.assertEquals(self.registry.get(0), self.object2)
            with self.registry.push('bar'):
                self.registry.add(self.object3)
                self.assertEquals(self.registry.get(0), self.object3)
            self.assertEquals(self.registry.get(0), self.object2)
            self.assertEquals(self.registry.get(1), self.object3)
        self.assertEquals(self.registry.get(0), self.object1)
        self.assertEquals(self.registry.get(1), self.object2)
        self.assertEquals(self.registry.get(2), self.object3)

    def test_pop_from_root(self):
        self.assertRaises(RegistryError, self.registry.pop)

