def psuedo_code_example():
    """Compare to the current implementation of start()"""
    class Service:
        def start(self, block_until_ready=True):
            self.state("start_services")
            for child in self._children:
                child.start(block_until_ready)
            self.state("services_started")
            ready = not self.do_start()
            if not ready and block_until_ready:
                self.state.wait("ready", self.ready_timeout)
            elif ready:
                self.state("ready")
            # if not ready, but block_until_ready is false,
            # your service code will just call self.state("ready")
            # when ready. this replaces self.set_ready()

class AbstractStateMachine(object):
    event_class = Event()

    def __init__(self, subject):
        self._state = self.initial_state
        self._subject = subject
        self._waitables = {}
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
            raise RuntimeWarning(
                "Unable to enter '{}' in current state".format(state))

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
 |    | services_started()|   |              v             |
 |    |-------------------|   |    +-------------------+   |
 |    |     starting      +---+    | services_stopped()|   |
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
    event_services_started = \
        ["starting:services"], "starting", None
    event_ready = \
        ["starting"], "ready", "post_start"
    event_stop_services = \
        ["ready", "starting:services", "starting"], "stopping:services", "pre_stop"
    event_services_stopped = \
        ["stopping:services"], "stopping", None
    event_stopped = \
        ["stopping", "stopping:services"], "stopped", "post_stop"

