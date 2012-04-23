import os.path
import peak.util.proxies
import re
import runpy

class Config(object):
    """Represents a collection of settings

    Provides access to a collection of settings that can be loaded from a
    Python module or file, or a dictionary. It allows classic-style classes to
    be used to indicate namespaces or groups, which can be nested.
    """
    _settings = {}
    _descriptors = []
    _last_file = None

    def _normalize_path(self, path):
        return path.lower().lstrip(".")

    def get(self, path, default=None):
        """gets the current value of a setting"""
        return self._settings.get(self._normalize_path(path), default)

    def set(self, path, value):
        """sets the value of a setting"""
        self._settings[self._normalize_path(path)] = value

    def group(self, path=''):
        """returns a Group object for the given path"""
        return Group(self, path)

    def setting(self, *args, **kwargs):
        """returns a _Setting descriptor attached to this configuration"""
        descriptor = _Setting(self, *args, **kwargs)
        self._descriptors.append(descriptor)
        return descriptor

    def load_module(self, module_path):
        """loads a module as configuration given a module path"""
        return self.load(runpy.run_module(module_path))

    def load_file(self, file_path):
        """loads a module as configuration given a file path"""
        file_path = os.path.abspath(os.path.expanduser(file_path))
        config_dict = runpy.run_path(file_path)
        self._last_file = file_path
        return self.load(config_dict)

    def reload_file(self):
        """reloads the last loaded configuration from load_file"""
        return self.load_file(self._last_file)

    def load(self, config_dict):
        """loads a dictionary into settings"""
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
        return self._settings

    def print_help(self, only_default=False):
        print "config settings:"
        for d in sorted(self._descriptors, key=lambda d: d.path):
            if d.help:
                value = d.default if only_default else self.get(d.path,
                                                                d.default)
                print "  %- 14s %s [%s]" % (
                    d.path, d.help.replace('\n', '\n'+' '*18), value)


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
            return self._config._settings[path]
        except KeyError:
            group_path = path + "."
            keys = self._config._settings.keys()
            if any(1 for k in keys if k.startswith(group_path)):
                return Group(self._config, path)
            return None

    def __repr__(self):
        return 'Group[{}]'.format(self._name)


class _Setting(object):
    """Setting descriptor for embedding in component classes.

    Do not use this object directly, instead use `Config.setting()`.

    This is a descriptor for your component classes to define what settings
    your application uses and provides a way to access that setting. By
    accessing with a descriptor, if the configuration changes you
    will always have the current value. Example:

        class MyService(Service):
            foo = config.setting('foo', default='bar',
                    help="This lets us set foo for MyService")

            def do_start(self):
                print self.foo
    """
    _init = object()

    def __init__(self, config, path, default=None, monitored=False, help=''):
        self._last_value = self._init
        self.config = config
        self.path = path
        self.default = default
        self.monitored = monitored
        self.help = self.__doc__ = re.sub(r'\n\s+', '\n', help.strip())

    def __get__(self, instance, type):
        if self.monitored:
            return SettingProxy(self.value, self)
        else:
            return self.value

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


class SettingProxy(peak.util.proxies.ObjectWrapper):
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

    @property
    def value(self):
        return self.__subject__


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
