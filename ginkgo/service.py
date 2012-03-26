import functools

from util import defaultproperty

from core import BasicService
from core import ServiceStateMachine

from async import AsyncManager

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

class ContainerStateMachine(ServiceStateMachine):
    allow_wait = ["ready", "stopped", "start"]
    event_start = \
        ["init", "stopped"], "starting", "pre_start"
    event_started = \
        ["starting"], "starting:services", None
    event_ready = \
        ["starting:services"], "ready", "post_start"

class Container(BasicService):
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
    _async_class = AsyncManager

    def pre_init(self):
        self.async = self._async_class()
        self.add_service(self.async)

    def spawn(self, *args, **kwargs):
        return self.async.spawn(*args, **kwargs)

    def spawn_later(self, *args, **kwargs):
        return self.async.spawn_later(*args, **kwargs)

