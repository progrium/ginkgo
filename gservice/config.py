
_registry = {}

class Namespace(dict): pass

def load(context, basepath=''):
    for k in context:
        if isinstance(context[k], Namespace):
            load(context[k], '%s.' % k)
        else:
            _registry[''.join([basepath, k]).lower()] = context[k]

def changed(obj, property):
    try:
        return obj.__dict__[property].changed
    except KeyError:
        return obj.__class__.__dict__[property].changed

class Setting(object):
    def __init__(self, path, default=None, doc=''):
        self.path = path.lower()
        self.default = default
        self.__doc__ = doc
        self._last_value = None
    
    def __get__(self, instance, type):
        return self.value
        
    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")
    
    @property
    def value(self):
        return _registry.get(self.path, self.default)
    
    @property
    def changed(self):
        has_changed = self._last_value != self.value
        if has_changed:
            self._last_value = self.value
        return has_changed

# Using Option is now deprecated. Use Setting instead
Option = Setting
