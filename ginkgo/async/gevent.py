from __future__ import absolute_import

import gevent
import gevent.event
import gevent.queue
import gevent.timeout
import gevent.pool

from ..core import BasicService

class AsyncManager(BasicService):
    """Starting with just gevent"""

    def __init__(self):
        self._greenlets = gevent.pool.Group()

    def do_stop(self):
        pass # TODO: Kill greenlets

    def spawn(self, func, *args, **kwargs):
        """Spawn a greenlet under this service"""
        return self._greenlets.spawn(func, *args, **kwargs)

    def spawn_later(self, seconds, func, *args, **kwargs):
        """Spawn a greenlet in the future under this service"""
        group = self._greenlets
        g = group.greenlet_class(func, *args, **kwargs)
        g.start_later(seconds)
        group.add(g)
        return g

    def sleep(self, seconds):
        return gevent.sleep(seconds)

    def queue(self, *args, **kwargs):
        return gevent.queue.Queue(*args, **kwargs)

    def event(self, *args, **kwargs):
        return gevent.event.Event(*args, **kwargs)

    def lock(self, *args, **kwargs):
        return gevent.coros.Semaphore(*args, **kwargs)
