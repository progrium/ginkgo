"""Ginkgo utility functions and classes

This module contains functions and classes that are shared across modules or
are more general utilities that aren't specific to Ginkgo. This way we keep
Ginkgo modules very dense in readable domain specific code.
"""
import resource
import os
import errno
import tempfile


class defaultproperty(object):
    """
    Allow for default-valued properties to be added to classes.

    Example usage:

    class Foo(object):
        bar = defaultproperty(list)
    """
    def __init__(self, default_factory, *args, **kwargs):
        self.default_factory = default_factory
        self.args = args
        self.kwargs = kwargs

    def __get__(self, instance, owner):
        if instance is None:
            return None
        for kls in owner.__mro__:
            for key, value in kls.__dict__.iteritems():
                if value == self:
                    newval = self.default_factory(*self.args, **self.kwargs)
                    instance.__dict__[key] = newval
                    return newval


def daemonize(preserve_fds=None):
    """\
    Standard daemonization of a process.
    http://www.svbug.com/documentation/comp.unix.programmer-FAQ/faq_2.html#SEC16
    """
    def _maxfd(limit=1024):
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if maxfd == resource.RLIM_INFINITY:
            return limit
        else:
            return maxfd

    def _devnull(default="/dev/null"):
        if hasattr(os, "devnull"):
            return os.devnull
        else:
            return default

    def _close_fds(preserve=None):
        preserve = preserve or []
        for fd in xrange(0, _maxfd()):
            if fd not in preserve:
                try:
                    os.close(fd)
                except OSError: # fd wasn't open to begin with (ignored)
                    pass

    if os.fork():
        os._exit(0)
    os.setsid()

    if os.fork():
        os._exit(0)

    os.umask(0)
    _close_fds(preserve_fds)

    os.open(_devnull(), os.O_RDWR)
    os.dup2(0, 1)
    os.dup2(0, 2)

def prevent_core_dump():
    """ Prevent this process from generating a core dump.

        Sets the soft and hard limits for core dump size to zero. On
        Unix, this prevents the process from creating core dump
        altogether.

        """
    core_resource = resource.RLIMIT_CORE

    try:
        # Ensure the resource limit exists on this platform, by requesting
        # its current value
        core_limit_prev = resource.getrlimit(core_resource)
    except ValueError, e:
        raise RuntimeWarning(
            "System does not support RLIMIT_CORE resource limit ({})".format(e))

    # Set hard and soft limits to zero, i.e. no core dump at all
    resource.setrlimit(core_resource, (0, 0))

class PassthroughEvent(object):
    def wait(self, timeout=None): return
    def set(self): return
    def clear(self): return

class AbstractStateMachine(object):
    event_class = PassthroughEvent

    def __init__(self, subject):
        self._state = self.initial_state
        self._subject = subject
        self._waitables = {}
        if hasattr(self._subject, 'async'):
            self.event_class = self._subject.async.event
        for state in self.allow_wait:
            self._waitables[state] = self.event_class()

    @property
    def current(self):
        return self._state

    def wait(self, state, timeout=None):
        if state in self._waitables:
            self._waitables[state].wait(timeout)
        else:
            raise RuntimeWarning("Unable to wait for state '{}'".format(state))

    def __call__(self, event):
        from_states, to_state, callback = self._lookup_event(event)
        if self._state in from_states:
            self._callback(callback)
            self._transition(to_state)
        else:
            raise RuntimeWarning("""
                Unable to enter '{}' from state '{}'
                """.format(to_state, self.current).strip())

    def _lookup_event(self, event):
        event_definition = "event_{}".format(event)
        if hasattr(self, event_definition):
            return getattr(self, event_definition)
        else:
            raise AttributeError("No event '{}' on {}".format(event, self))

    def _callback(self, name):
        if name is not None and hasattr(self._subject, name):
            getattr(self._subject, name)()

    def _transition(self, new_state):
        for state in self._waitables:
            self._waitables[state].clear()
        self._state = new_state
        if new_state in self._waitables:
            self._waitables[new_state].set()


class GlobalContext(object):
    """Context manager mixin for stackable singletons

    Use this mixin when a class has a global singleton set somewhere that can
    be temporarily set while in the context of an instance of that class::

        class Foo(GlobalContext):
            instance = None  # where we'll keep the singleton
            singleton_attr = (Foo, 'instance')  # tell mixin where it is

        Foo.instance = Foo()  # set an initial Foo singleton
        temporary_foo = Foo()  # create another Foo
        # now use it as a context
        with temporary_foo:
            # the singleton will be set to this instance
            assert Foo.instance is temporary_foo
        # then set back when you exit the context
        assert Foo.instance is not temporary_foo

    You can also nest global contexts if necessary. The main API is just
    setting where the singleton is with `singleton_attr`, which is a tuple of
    (object, attribute name). If `singleton_attr` is not set, there is no
    effect when you use the context manager. You can define `singleton_attr`
    outside the class definition to decouple your class definition from your
    use of a singleton. For example::

        class Foo(GlobalContext):
            pass

        singleton = Foo()  # module level singleton
        Foo.singleton_attr = (sys.modules[__name__], 'singleton')

    """
    singleton_attr = None
    _singleton_stacks = {}

    @classmethod
    def _get_singleton(cls):
        if cls.singleton_attr:
            return getattr(*cls.singleton_attr)

    @classmethod
    def _set_singleton(cls, value):
        if cls.singleton_attr:
            setattr(*list(cls.singleton_attr)+[value])

    @classmethod
    def _push_context(cls, obj):
        if cls.singleton_attr:
            klass = cls.__name__
            if klass not in cls._singleton_stacks:
                cls._singleton_stacks[klass] = []
            cls._singleton_stacks[klass].append(cls._get_singleton())
            cls._set_singleton(obj)

    @classmethod
    def _pop_context(cls):
        if cls.singleton_attr:
            klass = cls.__name__
            cls._set_singleton(
                    cls._singleton_stacks.get(klass, []).pop())

    def __enter__(self):
        self.__class__._push_context(self)
        return self

    def __exit__(self, type, value, traceback):
        self.__class__._pop_context()


class Pidfile(object):
    """\
    Manage a PID file. If a specific name is provided
    it and '"%s.oldpid" % name' will be used. Otherwise
    we create a temp file using os.mkstemp.
    """

    def __init__(self, fname):
        self.fname = fname
        self.pid = None

    def create(self, pid):
        oldpid = self.validate()
        if oldpid:
            if oldpid == os.getpid():
                return
            raise RuntimeError("Already running on PID %s " \
                "(or pid file '%s' is stale)" % (os.getpid(), self.fname))

        self.pid = pid

        # Write pidfile
        fdir = os.path.dirname(self.fname)
        if fdir and not os.path.isdir(fdir):
            raise RuntimeError("%s doesn't exist. Can't create pidfile." % fdir)
        fd, fname = tempfile.mkstemp(dir=fdir)
        os.write(fd, "%s\n" % self.pid)
        if self.fname:
            os.rename(fname, self.fname)
        else:
            self.fname = fname
        os.close(fd)

        # set permissions to -rw-r--r-- 
        os.chmod(self.fname, 420)

    def rename(self, path):
        self.unlink()
        self.fname = path
        self.create(self.pid)

    def unlink(self):
        """ delete pidfile"""
        try:
            with open(self.fname, "r") as f:
                pid1 =  int(f.read() or 0)

            if pid1 == self.pid:
                os.unlink(self.fname)
        except:
            pass

    def validate(self):
        """ Validate pidfile and make it stale if needed"""
        if not self.fname:
            return
        try:
            with open(self.fname, "r") as f:
                wpid = int(f.read() or 0)

                if wpid <= 0:
                    return

                try:
                    os.kill(wpid, 0)
                    return wpid
                except OSError, e:
                    if e[0] == errno.ESRCH:
                        return
                    raise
        except IOError, e:
            if e[0] == errno.ENOENT:
                return
            raise

## The following is extracted from ProxyTypes 0.9 package, licensed under ZPL:
## http://pypi.python.org/pypi/ProxyTypes

class AbstractProxy(object):
    """Delegates all operations (except ``.__subject__``) to another object"""
    __slots__ = ()

    def __call__(self,*args,**kw):
        return self.__subject__(*args,**kw)

    def __getattribute__(self, attr, oga=object.__getattribute__):
        subject = oga(self,'__subject__')
        if attr=='__subject__':
            return subject
        return getattr(subject,attr)

    def __setattr__(self,attr,val, osa=object.__setattr__):
        if attr=='__subject__':
            osa(self,attr,val)
        else:
            setattr(self.__subject__,attr,val)

    def __delattr__(self,attr, oda=object.__delattr__):
        if attr=='__subject__':
            oda(self,attr)
        else:
            delattr(self.__subject__,attr)

    def __nonzero__(self):
        return bool(self.__subject__)

    def __getitem__(self,arg):
        return self.__subject__[arg]

    def __setitem__(self,arg,val):
        self.__subject__[arg] = val

    def __delitem__(self,arg):
        del self.__subject__[arg]

    def __getslice__(self,i,j):
        return self.__subject__[i:j]


    def __setslice__(self,i,j,val):
        self.__subject__[i:j] = val

    def __delslice__(self,i,j):
        del self.__subject__[i:j]

    def __contains__(self,ob):
        return ob in self.__subject__

    for name in 'repr str hash len abs complex int long float iter oct hex'.split():
        exec "def __%s__(self): return %s(self.__subject__)" % (name,name)

    for name in 'cmp', 'coerce', 'divmod':
        exec "def __%s__(self,ob): return %s(self.__subject__,ob)" % (name,name)

    for name,op in [
        ('lt','<'), ('gt','>'), ('le','<='), ('ge','>='),
        ('eq','=='), ('ne','!=')
    ]:
        exec "def __%s__(self,ob): return self.__subject__ %s ob" % (name,op)

    for name,op in [('neg','-'), ('pos','+'), ('invert','~')]:
        exec "def __%s__(self): return %s self.__subject__" % (name,op)

    for name, op in [
        ('or','|'),  ('and','&'), ('xor','^'), ('lshift','<<'), ('rshift','>>'),
        ('add','+'), ('sub','-'), ('mul','*'), ('div','/'), ('mod','%'),
        ('truediv','/'), ('floordiv','//')
    ]:
        exec (
            "def __%(name)s__(self,ob):\n"
            "    return self.__subject__ %(op)s ob\n"
            "\n"
            "def __r%(name)s__(self,ob):\n"
            "    return ob %(op)s self.__subject__\n"
            "\n"
            "def __i%(name)s__(self,ob):\n"
            "    self.__subject__ %(op)s=ob\n"
            "    return self\n"
        )  % locals()

    del name, op

    # Oddball signatures

    def __rdivmod__(self,ob):
        return divmod(ob, self.__subject__)

    def __pow__(self,*args):
        return pow(self.__subject__,*args)

    def __ipow__(self,ob):
        self.__subject__ **= ob
        return self

    def __rpow__(self,ob):
        return pow(ob, self.__subject__)

class ObjectProxy(AbstractProxy):
    """Proxy for a specific object"""

    __slots__ = "__subject__"

    def __init__(self,subject):
        self.__subject__ = subject

class AbstractWrapper(AbstractProxy):
    """Mixin to allow extra behaviors and attributes on proxy instance"""
    __slots__ = ()

    def __getattribute__(self, attr, oga=object.__getattribute__):
        if attr.startswith('__'):
            subject = oga(self,'__subject__')
            if attr=='__subject__':
                return subject
            return getattr(subject,attr)
        return oga(self,attr)

    def __getattr__(self,attr, oga=object.__getattribute__):
        return getattr(oga(self,'__subject__'), attr)

    def __setattr__(self,attr,val, osa=object.__setattr__):
        if (
            attr=='__subject__'
            or hasattr(type(self),attr) and not attr.startswith('__')
        ):
            osa(self,attr,val)
        else:
            setattr(self.__subject__,attr,val)

    def __delattr__(self,attr, oda=object.__delattr__):
        if (
            attr=='__subject__'
            or hasattr(type(self),attr) and not attr.startswith('__')
        ):
            oda(self,attr)
        else:
            delattr(self.__subject__,attr)

class ObjectWrapper(ObjectProxy, AbstractWrapper):      __slots__ = ()

