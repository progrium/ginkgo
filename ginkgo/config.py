import runpy
from peak.util.proxies import ObjectWrapper


class Config(object):
    """Represents a collection of settings

    Provides access to a collection of settings that can be loaded from a
    Python module or file, or a dictionary. It allows classic-style classes to
    be used to indicate namespaces or groups, which can be nested.
    """
    settings = {}

    def _normalize_path(self, path):
        return path.lower().lstrip(".")

    def get(self, path, default=None):
        return self.settings.get(self._normalize_path(path), default)

    def set(self, path, value):
        self.settings[self._normalize_path(path)] = value

    def group(self, path=''):
        return Group(self, path)

    def setting(self, path, default=None, doc=''):
        return Setting(self, path, default, doc)

    def load_module(self, module_path):
        return self.load(runpy.run_module(module_path))

    def load_file(self, file_path):
        return self.load(runpy.run_path(file_path))

    def load(self, config_dict):
        def _load(d, prefix=''):
            """
            Recursively loads configuration from a dictionary, putting
            configuration under classic-style classes in a namespace.
            """
            items = (i for i in d.iteritems() if not i[0].startswith("_"))
            for key, value in items:
                path = ".".join((prefix, key))
                if type(value).__name__ == 'classobj':
                    _load(value.__dict__, path)
                else:
                    self.set(path, value)
        _load(config_dict)
        return self.settings


class Group(object):
    """Provides read-only access to a group of config data

    These objects represent a 'view' into a particular scope of the entire
    config, whether the global group or a group created using classic-style
    classes in the config file. They're not created directly. Use the `group()`
    method on `Config`.

        c = Config()
        g1 = c.group() # global scope group
        g1.foo # gives you the setting named "foo"
        g2 = c.group("bar.baz") # bar.baz scoped group
        g2.qux # give you the setting named "bar.baz.qux"

    They are not intended to be the primary interface to settings. However, in
    some cases it is more convenient. You should usually use the `setting`
    function to embed config settings for particular values on relevant classes.
    """
    def __init__(self, config, name):
        self._config = config
        self._name = name

    def __getattr__(self, name):
        path = self._config._normalize_path(".".join((self._name, name)))
        try:
            return self._config.settings[path]
        except KeyError:
            group_path = path + "."
            keys = self._config.settings.keys()
            if any(1 for k in keys if k.startswith(group_path)):
                return Group(self._config, path)
            return None

    def __repr__(self):
        return 'Group[{}]'.format(self._name)


class Setting(object):
    """Setting descriptor for embedding in component classes.

    Do not use this object directly, instead use `Config.setting()`.

    This is a descriptor for your component classes to define what settings
    your application uses and provides a way to access that setting. By
    accessing with a descriptor, if the configuration changes you
    will always have the current value. Example:

        class MyService(Service):
            foo = config.setting('foo', default='bar',
                    doc="This lets us set foo for MyService")

            def do_start(self):
                print self.foo
    """
    _init = object()

    def __init__(self, config, path, default=None, doc=''):
        self._last_value = self._init
        self.config = config
        self.path = path
        self.default = default
        self.__doc__ = doc

    def __get__(self, instance, type):
        return SettingProxy(self.value, self)

    @property
    def value(self):
        return self.config.get(self.path, self.default)

    @property
    def changed(self):
        """ True if the value has changed since the last time accessing
            this property. False on first access.
        """
        old, self._last_value = self._last_value, self.value
        return self.value != old and old is not self._init


class SettingProxy(ObjectWrapper):
    """Wraps an object returned by a `Setting` descriptor

    Primarily it gives any object that comes from `Setting` a `changed`
    property that will determine if the value has been changed, such as when
    configuration is reloaded.
    """
    descriptor = None

    def __init__(self, obj, descriptor):
        ObjectWrapper.__init__(self, obj)
        self.descriptor = descriptor

    @property
    def changed(self):
        return self.descriptor.changed


if __name__ == '__main__':
    c = Config()
    c.load({
        "foo": "bar",
        "bar.foo": "qux",
        "bar.boo": "bar",
        "bar.baz.foo": "bar",
        "bar.baz.bar": "bar"})

    assert c.get("foo") == "bar"

    class MyClass(object):
        foo = c.setting("foo", doc="This is foo.")

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
    assert g.bar.__class__ == Group
    assert g.bar.boo == "bar"
    assert g.bar.tree == None
