from nose.tools import with_setup, raises

from gevent_tools import util
from unittest import TestCase

class TestUtil(TestCase):
    def setUp(self):
        class Foo(object):
            bar = util.defaultproperty(set)
            
            def baz(self):
                ret = []
                for item in self.bar:
                    ret.append(item)
                return ret
                
        self.foo = Foo()
        self.fuz = Foo()

    def test_defaultproperty(self):
        assert self.foo.bar == set(), "foo.bar is a set"
        assert isinstance(self.foo.bar, set), "foo.bar is a set"

    def test_default_property_mutable(self):
        s = self.foo.bar
        s2 = self.fuz.bar

        s.add(3)
        s2.add(5)

        assert self.foo.bar == set([3]), "can mutate reference"
        assert self.fuz.bar == set([5]), "but not all references"

    def test_default_is_iterable(self):
        assert self.foo.baz() == [], "can iterate over self reference"

    def test_add_ass_first_dereference_works(self):
        self.foo.bar.add(3)
        assert self.foo.bar == set([3]), "previous line throws exceptino on fail"
