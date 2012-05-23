from __future__ import absolute_import

import threading
import Queue
import time

from ..util import defaultproperty
from ..async import AbstractAsyncManager

class Event(threading._Event):
    def wait(self, timeout=None):
        # Use a spin-loop type of wait so that signals can get through
        elapsed = 0
        while True:
            if super(Event, self).wait(1):
                return True
            elapsed += 1
            if timeout is not None and elapsed >= timeout:
                return False

class AsyncManager(AbstractAsyncManager):
    """Async manager for threads"""
    stop_timeout = defaultproperty(int, 1)

    def __init__(self):
        # XXX: modify spawn/spawn_later to put threads in here,
        # need some way to clean them up though (wrapper func?)
        self._threads = []

    def do_stop(self):
        """
        print "stopping aysnc service"
        if threading.current_thread() in self._threads:
            threading.Thread(target=self.do_stop).start()

        for t in self._threads:
            t.join(self.stop_timeout)
            # XXX: no api to kill OS threads
        print "aysnc service stopped"
        """

    def spawn(self, func, *args, **kwargs):
        """Spawn a greenlet under this service"""
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.daemon=True
        t.start()
        return t

    def spawn_later(self, seconds, func, *args, **kwargs):
        """Spawn a greenlet in the future under this service"""
        t = threading.Timer(target=func, args=args, kwargs=kwargs)
        t.daemon=True
        t.start()
        return t

    def sleep(self, seconds):
        return time.sleep(seconds)

    def queue(self, *args, **kwargs):
        return Queue.Queue(*args, **kwargs)

    def event(self, *args, **kwargs):
        return Event(*args, **kwargs)

    def lock(self, *args, **kwargs):
        return threading.Lock(*args, **kwargs)
