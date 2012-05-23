"""Gevent async module

This module provides the `AsyncManager` for gevent, as well as other utilities
useful for building gevent based Ginkgo apps. Obviously, this is the only async
module at the moment.

Of note, this module provides wrapped versions of the gevent bundled servers
that should be used instead of the gevent classes. These wrapped classes adapt
gevent servers to be Ginkgo services. They currently include:

    * StreamServer
    * WSGIServer (based on the pywsgi.WSGIServer)
    * BackdoorServer

"""
from __future__ import absolute_import

import gevent
import gevent.event
import gevent.queue
import gevent.timeout
import gevent.pool
import gevent.baseserver
import gevent.socket

import gevent.backdoor
import gevent.server
import gevent.pywsgi

from ..core import BasicService, Service
from ..util import defaultproperty, ObjectWrapper
from ..async import AbstractAsyncManager

class AsyncManager(AbstractAsyncManager):
    """Async primitives from gevent"""
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

    def signal(self, *args, **kwargs):
        gevent.signal(*args, **kwargs)

    def init(self):
        gevent.reinit()


class ServerWrapper(Service):
    """Wrapper for gevent servers that are based on gevent.baseserver.BaseServer

    DEPRECATED: Please use the pre-wrapped gevent servers in the same module.

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

class StreamClient(Service):
    """StreamServer-like TCP client service"""

    def __init__(self, address, handler=None):
        self.address = address
        self.handler = handler

    def do_start(self):
        self.spawn(self.connect)

    def connect(self):
        self.handle(
            gevent.socket.create_connection(self.address))

    def handle(self, socket):
        if self.handler:
            self.handler(socket)

class _ServerWrapper(Service, ObjectWrapper):
    server = state = __subject__ = None
    _children = []

    def __init__(self, *args, **kwargs):
        self.server = self.server(*args, **kwargs)
        ObjectWrapper.__init__(self, self.server)

    def do_start(self):
        self.spawn(self.server.start)

    def do_stop(self):
        self.server.stop()

class StreamServer(_ServerWrapper):
    server = gevent.server.StreamServer

class WSGIServer(_ServerWrapper):
    server = gevent.pywsgi.WSGIServer

class BackdoorServer(_ServerWrapper):
    server = gevent.backdoor.BackdoorServer
