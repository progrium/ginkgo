from threading import Event

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
                    if 'pass_instance' in self.kwargs:
                        del self.kwargs['pass_instance']
                        self.args.insert(instance, 0)
                    newval = self.default_factory(*self.args, **self.kwargs)
                    instance.__dict__[key] =newval
                    return newval

class AbstractStateMachine(object):
    event_class = Event

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
