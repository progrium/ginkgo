"""Ginkgo config

This module provides the class for a `Config` object, which represents an
application configuration, often loaded by a configuration file. This is used
by the runner module's `Process` object, but can be used completely
independently.

Configuration is described and accessed by Setting descriptors in your
application. Configuration values can then be set by Python configuration
files. However, using configuration files is completely optional. You can
expose configuration to the end-user via command-line arguments, then load them
into the `Config` object via `load()`.

By default, Ginkgo creates a `Config` object singleton to use in your
applications that you can import with `from ginkgo import settings`. You should
only have to create a `Config` object in testing scenarios. Ginkgo also
provides a shortcut for creating Setting descriptors associated with this
singleton that you can import with `from ginkgo import Setting`. Often, this is
the only API you need to use Ginkgo config.

"""
import collections
import os.path
import re
import runpy

import util

class Config(util.GlobalContext):
    """Represents a collection of settings

    Provides access to a collection of settings that can be loaded from a
    Python module or file, or a dictionary. It allows classic-style classes to
    be used to indicate namespaces or groups, which can be nested.

    As a `GlobalContext`, you can specify the location of a singleton by setting
    `Config.singleton_attr` to a tuple of (object, attribute_name). Then any
    `Config` instance will be a context manager that will temporarily set that
    singleton to that instance.
    """
    _settings = {}
    _descriptors = []
    _forced_settings = set()
    _last_file = None

    def _normalize_path(self, path):
        return path.lower().lstrip(".")

    def get(self, path, default=None):
        """gets the current value of a setting"""
        return self._settings.get(self._normalize_path(path), default)

    def set(self, path, value, force=False):
        """sets the value of a setting"""
        path = self._normalize_path(path)
        if force or path not in self._forced_settings:
            self._settings[self._normalize_path(path)] = value
            if force:
                self._forced_settings.add(path)


    def group(self, path=''):
        """returns a Group object for the given path if exists"""
        if path not in self._settings:
            return Group(self, path)

    def setting(self, *args, **kwargs):
        """returns a _Setting descriptor attached to this configuration"""
        descriptor = _Setting(self, *args, **kwargs)
        self._descriptors.append(descriptor)
        return descriptor

    def load_module(self, module_path):
        """loads a module as configuration given a module path"""
        try:
            return self.load(runpy.run_module(module_path))
        except Exception, e:
            raise RuntimeError("Config error: {}".format(e))

    def load_file(self, file_path):
        """loads a module as configuration given a file path"""
        file_path = os.path.abspath(os.path.expanduser(file_path))
        try:
            config_dict = runpy.run_path(file_path)
        except Exception, e:
            raise RuntimeError("Config error: {}".format(e))
        self._last_file = file_path
        return self.load(config_dict)

    def reload_file(self):
        """reloads the last loaded configuration from load_file"""
        if self._last_file:
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


class Group(collections.Mapping):
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
    def __init__(self, config, name=''):
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
        return 'Group[{}:{}]'.format(self._name, self._dict())

    def _dict(self):
        d = dict()
        group_path = self._name + "."
        for key in self._config._settings.keys():
            if not self._name or key.startswith(group_path):
                if self._name:
                    key = key.split(group_path, 1)[-1]
                name = key.split('.', 1)[0]
                if name not in d:
                    d[name] = getattr(self, name)
        return d

    # Mapping protocol

    def __contains__(self, item):
        return item in self._dict()

    def __iter__(self):
        return self._dict().__iter__()

    def __len__(self):
        return self._dict().__len__()

    def __getitem__(self, key):
        return getattr(self, key)



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


class SettingProxy(util.ObjectWrapper):
    """Wraps an object returned by a `Setting` descriptor

    Primarily it gives any object that comes from `Setting` a `changed`
    property that will determine if the value has been changed, such as when
    configuration is reloaded.
    """
    descriptor = None

    def __init__(self, obj, descriptor):
        super(SettingProxy, self).__init__(obj)
        self.descriptor = descriptor

    @property
    def changed(self):
        return self.descriptor.changed

    @property
    def value(self):
        return self.__subject__


