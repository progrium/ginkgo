
_registry = {}

def load(context, basepath=''):
    for k in context:
        if isinstance(context[k], dict):
            load(context[k], '%s.' % k)
        else:
            _registry[''.join([basepath, k]).lower()] = context[k]

class Option(object):
    def __init__(self, path, default=None, doc=''):
        self.path = path.lower()
        self.default = default
        self.__doc__ = doc
    
    def __get__(self, instance, owner):
        return _registry.get(self.path, self.default)
        
    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")


if __name__ == '__main__':
    load(dict(
        FOO='bar',
        baz='qux',
        section1=dict(
            foo='bar'),
        section2=dict(
            foo='bar',
            SUBSECTION=dict(
                baz='qux'))
    ))
    
    class MyThing(object):
        my_config = Option('section1.foo')
    
    m = MyThing()
    assert m.my_config == 'bar'
    assert MyThing.my_config == 'bar'
    

