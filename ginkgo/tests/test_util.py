from nose.tools import with_setup, raises

def _make_class(super):
    # don't use type(), it's hard to read
    from ginkgo.util import defaultproperty
    class Foo(super):
        bar = defaultproperty(set)
        
    return Foo

def test_defaultproperty():
    Foo = _make_class(object)
    foo = Foo()
    assert isinstance(foo.bar, set), "foo.bar is a set"

def test_default_property_mutable():
    Foo = _make_class(object)
    foo = Foo()
    fuz = Foo()
    s = foo.bar
    s2 = fuz.bar

    s.add(3)
    s2.add(5)

    assert foo.bar == set([3]), "can mutate reference"
    assert fuz.bar == set([5]), "but not all references"

def test_default_is_iterable():
    Foo = _make_class(object)
    foo = Foo()
    assert [x for x in foo.bar] == [], "can iterate over iterable default"

def test_add_as_first_dereference_works():
    Foo = _make_class(object)
    foo = Foo()
    foo.bar.add(3)
    assert foo.bar == set([3]), "previous line throws exceptino on fail"

def test_default_subclasses_work():
    Foo = _make_class(object)
    class Bar(Foo):
        pass
    bar = Bar()
    bar.bar.add(5)

    assert bar.bar == set([5]), "defaultproperties can find parent classes."
