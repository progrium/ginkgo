try:
    import ctypes
except MemoryError:
    # selinux execmem denial
    # https://bugzilla.redhat.com/show_bug.cgi?id=488396
    ctypes = None
except ImportError:
    # Python on Solaris compiled with Sun Studio doesn't have ctypes
    ctypes = None

import resource
import os
import errno
import tempfile

MAXFD = 1024
if (hasattr(os, "devnull")):
   DEVNULL = os.devnull
else:
   DEVNULL = "/dev/null"

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

def get_maxfd():
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
        maxfd = MAXFD
    return maxfd

try:
    from os import closerange
except ImportError:
    def closerange(fd_low, fd_high):
        # Iterate through and close all file descriptors.
        for fd in xrange(fd_low, fd_high):
            try:
                os.close(fd)
            except OSError:	# ERROR, fd wasn't open to begin with (ignored)
                pass

def daemonize():
    """\
    Standard daemonization of a process.
    http://www.svbug.com/documentation/comp.unix.programmer-FAQ/faq_2.html#SEC16
    """
    if os.fork():
        os._exit(0)
    os.setsid()

    if os.fork():
        os._exit(0)

    os.umask(0)
    maxfd = get_maxfd()
    closerange(0, maxfd)

    os.open(DEVNULL, os.O_RDWR)
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

