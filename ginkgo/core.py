from util import AbstractStateMachine
from util import defaultproperty

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

class BasicService(object):
    _statemachine_class = ServiceStateMachine
    _children = defaultproperty(list)

    start_timeout = defaultproperty(int, 2)
    state = defaultproperty(
            lambda i: i._statemachine_class(i), pass_instance=True)

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
        except RuntimeWarning:
            # If it can't start because it's
            # already started, just move on
            pass
        if ready_callback is not None:
            ready_callback()
        self.state.wait("stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()



