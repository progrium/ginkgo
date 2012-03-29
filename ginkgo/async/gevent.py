from __future__ import absolute_import

import gevent
import gevent.event
import gevent.queue
import gevent.timeout
import gevent.pool
import gevent.baseserver

from ..core import BasicService
from ..util import defaultproperty

class AsyncManager(BasicService):
    """Starting with just gevent"""
    stop_timeout = defaultproperty(int, 1)

    def __init__(self):
        self._greenlets = gevent.pool.Group()

    def do_stop(self):
        if gevent.getcurrent() in self._greenlets:
            return gevent.spawn(self.do_stop).join()
        if self._greenlets:
            self._greenlets.join(timeout=self.stop_timeout)
            self._greenlets.kill(block=True, timeout=1)

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


class ServerWrapper(Service):
    """Wrapper for gevent servers that are based on gevent.baseserver.BaseServer

    Although BaseServer objects mostly look like they have the Service interface,
    there are certain extra methods (like reload, service_name, etc) that are assumed
    to be available. This class allows us to wrap gevent servers so they actually
    behave as a Service. There is no automatic wrapping like 0.3.0 and earlier,
    so you have to explicitly wrap gevent servers:

        from ginkgo.core import Service
        from ginkgo.async.gevent import ServerWrapper
        from gevent.pywsgi import WSGIServer

        class MyService(Service):
            def __init__(self):
                self.server = WSGIServer(('0.0.0.0', 80), self.handle)
                self.add_service(ServerWrapper(self.server))

    """
    def __init__(self, server, *args, **kwargs):
        super(ServerWrapper, self).__init__()
        if isinstance(server, gevent.baseserver.BaseServer):
            self.wrapped = server
        else:
            raise RuntimeError(
                "Object being wrapped is not a BaseServer instance")

    def do_start(self):
        self.spawn(self.wrapped.start)

    def do_stop(self):
        self.wrapped.stop()
