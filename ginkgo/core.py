"""Ginkgo service core

This module implements the core service model and several convenience
decorators to use with your services. The primary export of this module is
`Service`, but much of the implementation is in `BasicService`. `BasicService`
uses a simple state machine defined by `ServiceStateMachine` and implements the
core service interface.

`BasicService` assumes no async model, whereas `Service` creates an
`AsyncManager` from a driver in the `async` module. It's assumed the common
case is to create async applications, but there are cases when you need a
`Service` with no async. For example, `AsyncManager` classes inherit from
`BasicService`, otherwise there would be a circular dependency.

"""
import functools
import runpy

from .util import AbstractStateMachine
from .util import defaultproperty
from . import Setting

def require_ready(func):
    """ Decorator that blocks the call until the service is ready """
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        try:
            self.state.wait("ready", self.ready_timeout)
        except Exception, e:
            pass
        if not self.ready:
            raise RuntimeWarning("Service must be ready to call this method.")
        return func(self, *args, **kwargs)
    return wrapped

def autospawn(func):
    """ Decorator that will spawn the call in a local greenlet """
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        self.spawn(func, self, *args, **kwargs)
    return wrapped

class ServiceStateMachine(AbstractStateMachine):
    """     +------+
            | init |
            +--+---+
               |
               v
      +-------------------+
 +--->|      start()      |
 |    |-------------------|        +-------------------+
 |    |     starting      +---+--->|      stop()       |
 |    +-------------------+   |    |-------------------|
 |             |              |    |     stopping      |
 |             v              |    +-------------------+
 |        +-----------+       |              |
 |        |  ready()  |       |              |
 |        |-----------|       |              v
 |        |   ready   +-------+       +-------------+
 |        +-----------+               |  stopped()  |
 |                                    |-------------|
 +------------------------------------+   stopped   |
                                      +-------------+

    http://www.asciiflow.com/#7278337222084818599/1920677602
    """
    initial_state = "init"
    allow_wait = ["ready", "stopped"]
    event_start = \
        ["init", "stopped"], "starting", "pre_start"
    event_ready = \
        ["starting"], "ready", "post_start"
    event_stop = \
        ["ready", "starting"], "stopping", "pre_stop"
    event_stopped = \
        ["stopping"], "stopped", "post_stop"

class BasicService(object):
    _statemachine_class = ServiceStateMachine
    _children = defaultproperty(list)

    start_timeout = defaultproperty(int, 2)
    start_before = defaultproperty(bool, False)

    def pre_init(self):
        pass

    def __new__(cls, *args, **kwargs):
        s = super(BasicService, cls).__new__(cls, *args, **kwargs)
        s.pre_init()
        s.state = cls._statemachine_class(s)
        return s

    @property
    def service_name(self):
        return self.__class__.__name__

    @property
    def ready(self):
        return self.state.current == 'ready'

    def add_service(self, service):
        """Add a child service to this service

        The service added will be started when this service starts, before
        its :meth:`_start` method is called. It will also be stopped when this
        service stops, before its :meth:`_stop` method is called.

        """
        self._children.append(service)

    def remove_service(self, service):
        """Remove a child service from this service"""
        self._children.remove(service)

    def start(self, block_until_ready=True):
        """Starts children and then this service. By default it blocks until ready."""
        self.state("start")
        if self.start_before:
            self.do_start()
        for child in self._children:
            if child.state.current not in ["ready", "starting"]:
                child.start(block_until_ready)
        if not self.start_before:
            ready = not self.do_start()
            if not ready and block_until_ready is True:
                self.state.wait("ready", self.start_timeout)
            elif ready:
                self.state("ready")
        else:
            self.state("ready")

    def pre_start(self):
        pass

    def do_start(self):
        """Empty implementation of service start. Implement me!

        Return `service.NOT_READY` to block until :meth:`set_ready` is
        called (or `ready_timeout` is reached).

        """
        return

    def post_start(self):
        pass

    def stop(self):
        """Stop child services in reverse order and then this service"""
        if self.state.current in ["init", "stopped"]:
            return
        ready_before_stop = self.ready
        self.state("stop")
        for child in reversed(self._children):
            child.stop()
        if ready_before_stop:
            self.do_stop()
        self.state("stopped")

    def pre_stop(self):
        pass

    def post_stop(self):
        pass

    def do_stop(self):
        """Empty implementation of service stop. Implement me!"""
        return

    def reload(self):
        def _reload_children():
            for child in self._children:
                child.reload()

        if self.start_before:
            self.do_reload()
            _reload_children()
        else:
            _reload_children()
            self.do_reload()

    def do_reload(self):
        """Empty implementation of service reload. Implement me!"""
        pass

    def serve_forever(self):
        """Start the service if it hasn't been already started and wait until it's stopped."""
        try:
            self.start()
        except RuntimeWarning, e:
            # If it can't start because it's
            # already started, just move on
            pass

        self.state.wait("stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()


class Service(BasicService):
    async_available = ["ginkgo.async." + m for m in ("gevent", "threading",
                                                     "eventlet")]
    async = Setting("async", default="ginkgo.async.threading", help="""\
        The async reactor to use. Available choices:
            ginkgo.async.gevent
            ginkgo.async.threading
            ginkgo.async.eventlet
        """)

    def pre_init(self):
        try:
            mod = runpy.run_module(self.async)
            self.async = mod['AsyncManager']()
            self.add_service(self.async)
        except (NotImplementedError, ImportError) as e:
            if self.async not in self.async_available:
                helptext = ("Please select a valid async module: \n\t"
                            + "\n\t".join(self.async_available))

            elif self.async.endswith("gevent"):
                helptext = ("Please make sure gevent is installed or use "
                            "a different async manager.")
            else:
                helptext = ""

            raise RuntimeError(
                "Unable to load async manager from {}.\n{}".format(self.async,
                                                                  helptext))

    def spawn(self, *args, **kwargs):
        return self.async.spawn(*args, **kwargs)

    def spawn_later(self, *args, **kwargs):
        return self.async.spawn_later(*args, **kwargs)


