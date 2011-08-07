from nose.tools import with_setup, raises

from gevent_tools import config

def setup(): pass

def teardown():
    config._registry = {}

@with_setup(setup, teardown)
def test_basic_load_and_read_from_option():
    class Foo(object):
        bar = config.Option('bar')
    config.load(dict(bar='foo'))
    assert Foo.bar == 'foo', "Option value not set properly"

@with_setup(setup, teardown)
def test_configuration_namespaces():
    class Foo(object):
        bar = config.Option('foo.bar')
    config.load(dict(
        foo = config.Namespace(
            bar = 'foo')
    ))
    assert Foo.bar == 'foo', "Namespaced value not accessible"

@with_setup(setup, teardown)
def test_value_changed():
    class Foo(object):
        bar = config.Option('bar')
    config.load(dict(bar='bar'))
    assert config.changed(Foo, 'bar'), "Value should have changed after initial load"
    assert not config.changed(Foo, 'bar'), "Value should not have changed after initial check"
    config.load(dict(bar='foo'))
    assert config.changed(Foo, 'bar'), "Value should have changed after setting"
    assert not config.changed(Foo, 'bar'), "Value should not have changed after previous check"

@raises(AttributeError)
@with_setup(setup, teardown)
def test_cannot_set_option():
    class Foo(object):
        bar = config.Option('bar')
    #config.load(dict(bar='bar'))
    #Foo.bar = 'woefijwefo'
    #print Foo.bar
    #assert Foo.bar == 'bar', "Class option value was set"
    f = Foo()
    f.bar = 'kjiufuff'
    assert Foo.bar is None, "Instance option value was set"
