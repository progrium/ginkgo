"""Async driver modules

This module provides the base class for `AsyncManager` classes for different
async drivers. This provides a unified interface to async primitives,
regardless of whether you're using gevent, eventlet, threading, or
multiprocessing. The `AsyncManager` also manages a pool of async workers, whatever
they are. Since each `Service` has an `AsyncManager`, all `Service` objects
also have their own pool of async workers.

By default, all services use `ginkgo.async.gevent` to find their
`AsyncManager`. But you can change this by setting `async` in your service
class definition::

    class NonGeventService(Service):
        async = "path.to.different.module"

"""
import signal
from ..core import BasicService

class AbstractAsyncManager(BasicService):
    def spawn(self, func, *args, **kwargs):
        raise NotImplementedError()

    def spawn_later(self, seconds, func, *args, **kwargs):
        raise NotImplementedError()

    def sleep(self, seconds):
        raise NotImplementedError()

    def queue(self, *args, **kwargs):
        raise NotImplementedError()

    def event(self, *args, **kwargs):
        raise NotImplementedError()

    def lock(self, *args, **kwargs):
        raise NotImplementedError()

    def signal(self, *args, **kwargs):
        return signal.signal(*args, **kwargs)

    def init(self):
        pass
