from __future__ import absolute_import

import threading
import Queue
import time

from ..util import defaultproperty
from ..async import AbstractAsyncManager

def _spin_wait(fn, timeout):
    """ Spin-wait blocking only 1 second at a time so we don't miss signals """
    elapsed = 0
    while True:
        if fn(timeout=1):
            return True
        elapsed += 1
        if timeout is not None and elapsed >= timeout:
            return False


class Event(threading._Event):
    def wait(self, timeout=None):
        return _spin_wait(super(Event, self).wait, timeout)


class Thread(threading.Thread):
    def join(self, timeout=None):
        return _spin_wait(super(Thread, self).join, timeout)


class Timer(threading._Timer):
    def join(self, timeout=None):
        return _spin_wait(super(Timer, self).join, timeout)


class AsyncManager(AbstractAsyncManager):
    """Async manager for threads"""
    stop_timeout = defaultproperty(int, 1)

    def __init__(self):
        # _lock protects the _threads structure
        print ("The ginkgo.async.threading manager should not be used in "
               "production environments due to the known limitations of the GIL")
        self._lock = threading.Lock()
        self._threads = []

    def do_stop(self):
        """
            Beware! This function has different behavior than the gevent
            async manager in the following respects:
                - The stop timeout is used for joining each thread instead of
                  for all of the threads collectively.
                - If the threads do not successfully join within their timeout,
                  they will not be killed since there is no safe way to do this.
        """
        with self._lock:
            reentrant_stop = threading.current_thread() in self._threads

        if reentrant_stop:
            t = Thread(target=self.do_stop)
            t.daemon=True
            t.start()
            return t.join()

        with self._lock:
            for t in self._threads:
                t.join(self.stop_timeout)

    def spawn(self, func, *args, **kwargs):
        """Spawn a greenlet under this service"""
        t = Thread(target=func, args=args, kwargs=kwargs)
        with self._lock:
            self._threads.append(t)
        t.daemon=True
        t.start()
        return t

    def spawn_later(self, seconds, func, *args, **kwargs):
        """Spawn a greenlet in the future under this service"""
        t = Timer(group=self, target=func, args=args, kwargs=kwargs)
        with self._lock:
            self._threads.append(t)
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
