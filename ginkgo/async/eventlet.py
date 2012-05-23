from __future__ import absolute_import

import eventlet
import eventlet.greenpool
import eventlet.greenthread
import eventlet.event
import eventlet.queue
import eventlet.timeout
import eventlet.semaphore

from ..core import BasicService, Service
from ..util import defaultproperty

class AsyncManager(BasicService):
    """Async primitives from eventlet"""
    stop_timeout = defaultproperty(int, 1)

    def __init__(self):
        self._greenlets = eventlet.greenpool.GreenPool()

    def do_stop(self):
        if eventlet.greenthread.getcurrent() in self._greenlets.coroutines_running:
            return eventlet.spawn(self.do_stop).join()
        if self._greenlets.running():
            with eventlet.timeout.Timeout(self.stop_timeout, False):
                self._greenlets.waitall() # put in timeout for stop_timeout
            for g in list(self._greenlets.coroutines_running):
                with eventlet.timeout.Timeout(1, False):
                    g.kill() # timeout of 1 sec?

    def spawn(self, func, *args, **kwargs):
        """Spawn a greenlet under this service"""
        return self._greenlets.spawn(func, *args, **kwargs)

    def spawn_later(self, seconds, func, *args, **kwargs):
        """Spawn a greenlet in the future under this service"""
        def spawner():
            self.spawn(func, *args, **kwargs)
        return eventlet.spawn_after(seconds, spawner)

    def sleep(self, seconds):
        return eventlet.sleep(seconds)

    def queue(self, *args, **kwargs):
        return eventlet.queue.Queue(*args, **kwargs)

    def event(self, *args, **kwargs):
        return Event(*args, **kwargs)

    def lock(self, *args, **kwargs):
        return eventlet.semaphore.Semaphore(*args, **kwargs)

class Event(eventlet.event.Event):
    def clear(self):
        if not self.ready():
            return
        self.reset()

    def set(self):
        self.send()

    def wait(self, timeout=None):
        if timeout:
            with eventlet.timeout.Timeout(timeout, False):
                super(Event, self).wait()
        else:
            super(Event, self).wait()
