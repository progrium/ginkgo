import functools
import runpy

from util import AbstractStateMachine
from util import defaultproperty

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
 +--->|  start_services() |
 |    |-------------------|        +-------------------+
 |    | starting:services +---+--->|  stop_services()  |
 |    +-------------------+   |    |-------------------|
 |             |              |    | stopping:services +---+
 |             v              |    +-------------------+   |
 |    +-------------------+   |              |             |
 |    |      start()      |   |              v             |
 |    |-------------------|   |    +-------------------+   |
 |    |     starting      +---+    |      stop()       |   |
 |    +-------------------+   |    |-------------------|   |
 |             |              |    |     stopping      |   |
 |             v              |    +-------------------+   |
 |        +-----------+       |              |             |
 |        |  ready()  |       |              |             |
 |        |-----------|       |              v             |
 |        |   ready   +-------+       +-------------+      |
 |        +-----------+               |  stopped()  |<-----+
 |                                    |-------------|
 +------------------------------------+   stopped   |
                                      +-------------+

    http://www.asciiflow.com/#7278337222084818599/1920677602
    """
    initial_state = "init"
    allow_wait = ["ready", "stopped"]
    event_start_services = \
        ["init", "stopped"], "starting:services", "pre_start"
    event_start = \
        ["starting:services"], "starting", None
    event_ready = \
        ["starting"], "ready", "post_start"
    event_stop_services = \
        ["ready", "starting:services", "starting"], "stopping:services", "pre_stop"
    event_stop = \
        ["stopping:services"], "stopping", None
    event_stopped = \
        ["stopping", "stopping:services"], "stopped", "post_stop"

class ContainerStateMachine(ServiceStateMachine):
    allow_wait = ["ready", "stopped", "start"]
    event_start = \
        ["init", "stopped"], "starting", "pre_start"
    event_started = \
        ["starting"], "starting:services", None
    event_ready = \
        ["starting:services"], "ready", "post_start"

class BasicService(object):
    _statemachine_class = ServiceStateMachine
    _children = defaultproperty(list)

    start_timeout = defaultproperty(int, 2) 

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
        self.state("start_services")
        for child in self._children:
            if child.state.current not in ["ready", "starting", "starting:services"]:
                child.start(block_until_ready)
        self.state("start")
        ready = not self.do_start()
        if not ready and block_until_ready is True:
            self.state.wait("ready", self.start_timeout)
        elif ready:
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
        self.state("stop_services")
        for child in reversed(self._children):
            child.stop()
        if ready_before_stop:
            self.state("stop")
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
        for child in self._children:
            child.reload()
        self.do_reload()

    def do_reload(self):
        """Empty implementation of service reload. Implement me!"""
        pass

    def serve_forever(self, ready_callback=None):
        """Start the service if it hasn't been already started and wait until it's stopped."""
        try:
            self.start()
        except RuntimeWarning, e:
            # If it can't start because it's
            # already started, just move on
            pass
        if ready_callback is not None:
            ready_callback()

        # This is done to recursively get services to wait on stopped.
        # Services based on BasicService will not wait because they
        # have no async manager and assume no event loop or threads.
        for child in self._children:
            child.serve_forever()

        self.state.wait("stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()


class ContainerService(BasicService):
    _statemachine_class = ContainerStateMachine

    def start(self, block_until_ready=True):
        """Starts this service and then children. By default it blocks until ready."""
        self.state("start")
        started = not self.do_start()
        if not started and block_until_ready is True:
            self.state.wait("starting:services", self.start_timeout)
        elif started:
            self.state("started")
        for child in self._children:
            if child.state.current not in ["ready", "starting", "starting:services"]:
                child.start(block_until_ready)
        self.state("ready")


class Service(BasicService):
    async = 'ginkgo.async.gevent'

    def pre_init(self):
        try:
            mod = runpy.run_module(self.async)
            self.async = mod['AsyncManager']()
            self.add_service(self.async)
        except NotImplementedError: #(ImportError, KeyError):
            raise RuntimeError(
                "Unable to load async manager from {}".format(self.async))

    def spawn(self, *args, **kwargs):
        return self.async.spawn(*args, **kwargs)

    def spawn_later(self, *args, **kwargs):
        return self.async.spawn_later(*args, **kwargs)


