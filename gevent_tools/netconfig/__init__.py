from gevent_tools import service

_backends = {}
_instances = {}

def get(backend, *args, **kwargs):
    __import__('gevent_tools.netconfig.%s' % backend)
    if backend not in _backends:
        raise NotImplementedError("This backend is not found")
    if backend not in _instances:
        _instances[backend] = _backends[backend](*args, **kwargs)
    return _instances[backend]

def register(backend_class):
    _backends[backend_class.name] = backend_class

class ConfigStoreService(service.Service):
    name = None
    
    def get(self, path):
        raise NotImplementedError()
    
    def set(self, path, value):
        raise NotImplementedError()
    
    def list(self, path):
        raise NotImplementedError()
    
    def delete(self, path):
        raise NotImplementedError()