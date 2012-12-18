from ginkgo import config

def test_config():
    c = config.Config()
    c.load({
        "foo": "bar",
        "bar.foo": "qux",
        "bar.boo": "bar",
        "bar.baz.foo": "bar",
        "bar.baz.bar": "bar"})

    assert c.get("foo") == "bar"

    class MyClass(object):
        foo = c.setting("foo", help="This is foo.", monitored=True)

        def override(self):
            self.foo = "qux"

    o = MyClass()
    assert o.foo == "bar"
    assert o.foo.changed == False
    assert o.foo.changed == False
    c.set("foo", "BAZ")
    assert o.foo.changed == True
    assert o.foo.changed == False
    assert MyClass.foo == "BAZ"

    o.override()
    assert MyClass.foo == "BAZ"
    assert o.foo == "qux"

    g = c.group()
    assert g.foo == "BAZ"
    assert g.bar.__class__ == config.Group
    assert g.bar.boo == "bar"
    assert g.bar.tree == None
