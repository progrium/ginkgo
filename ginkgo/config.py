import runpy
from peak.util.proxies import ObjectWrapper

class Namespace(object):
    def __init__(self, config, name):
        self._config = config
        self._name = name

    def __getattr__(self, name):
        setting_name = "{}.{}".format(self._name, name).lstrip('.')
        if setting_name in self._config.settings:
            return self._config.get(setting_name)
        else:
            namespace_name = "{}.".format(setting_name)
            for key in self._config.settings.keys():
                if key.startswith(namespace_name):
                    return Namespace(self._config, setting_name)
            return None

    def __repr__(self):
        return 'Namespace[{}]'.format(self._name)

class Configuration(object):
    setting_defs = []
    settings = {}

    def register_def(self, setting_def):
        if setting_def not in self.setting_defs:
            self.setting_defs.append(setting_def)

    def get(self, path, default=None):
        return self.settings.get(path.lower(), default)

    def set(self, path, value):
        self.settings[path.lower()] = value
        for setting_def in self.setting_defs:
            if setting_def.path == path.lower():
                setting_def._initial_changed = False

    def namespace(self, path=''):
        return Namespace(self, path)

    def load_module(self, module_path):
        return self.load(runpy.run_module(module_path))

    def load_file(self, file_path):
        return self.load(runpy.run_path(file_path))

    def load(self, config_dict):
        def _load(d, prefix=''):
            settings = [(k,d[k]) for k in d if not k.startswith('_')]
            for key, value in settings:
                if type(value).__name__ == 'classobj':
                    _load(value.__dict__, '{}.{}'.format(
                        prefix, key).lstrip('.'))
                else:
                    self.set('{}.{}'.format(
                        prefix, key).lstrip('.'), value)
        _load(config_dict)
        return self.settings

_default_config = Configuration()

class SettingProxy(ObjectWrapper):
    descriptor = None

    def __init__(self, obj, descriptor):
        ObjectWrapper.__init__(self, obj)
        self.descriptor = descriptor

    @property
    def changed(self):
        return self.descriptor._changed


class Setting(object):
    def __init__(self, path, default=None, doc='', _config=None):
        self.config = _config or _default_config
        self.config.register_def(self)
        self.path = path.lower()
        self.default = default
        self.__doc__ = doc
        self._last_value = None
        self._initial_changed = True

    def __get__(self, instance, type):
        return SettingProxy(self.value, self)

    @property
    def value(self):
        return self.config.get(self.path)

    @property
    def _changed(self):
        if self._initial_changed is True:
            self._last_value = self.value
            self._initial_changed = False
            return False
        has_changed = self._last_value != self.value
        if has_changed:
            self._last_value = self.value
        return has_changed

    @staticmethod
    def get(path, default=None, _config=None):
        config = _config or _default_config
        return config.get(path, default)

    @staticmethod
    def set(path, value, _config=None):
        config = _config or _default_config
        config.set(path, value)

    @staticmethod
    def namespace(path='', _config=None):
        config = _config or _default_config
        return config.namespace(path)


if __name__ == '__main__':
    _default_config.load({
        "foo": "bar",
        "bar.foo": "bar",
        "bar.boo": "bar",
        "bar.baz.foo": "bar",
        "bar.baz.bar": "bar"})
    assert Setting.get("foo") == "bar"

    class MyClass(object):
        foo = Setting("foo", doc="This is foo.")

        def override(self):
            self.foo = "qux"

    o = MyClass()
    assert o.foo == "bar"
    assert o.foo.changed == False
    assert o.foo.changed == False
    Setting.set("foo", "BAZ")
    assert o.foo.changed == True
    assert o.foo.changed == False
    assert MyClass.foo == "BAZ"

    o.override()
    assert MyClass.foo == "BAZ"
    assert o.foo == "qux"

    ns = Setting.namespace()
    assert ns.foo == "BAZ"
    assert ns.bar.__class__ == Namespace
    assert ns.bar.boo == "bar"
    assert ns.bar.tree == None
