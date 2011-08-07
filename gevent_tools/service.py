import gevent
import gevent.baseserver
import gevent.event
import gevent.pool
import gevent.util

from gevent_tools.util import ServiceWrapper

NOT_READY = 1

class Service(object):
    """Service base class for creating standalone or composable services
    
    A service is a container for two things: other services and greenlets. It
    then provides a common interface for starting and stopping them, based on
    a subset of the gevent.baseserver interface. This way you can include
    StreamServer or WSGIServer as child services.
    
    Service also lets you catch exceptions in the greenlets started from this
    service and introduces the concept of `ready`, letting us block :meth:`start`
    until the service is actually ready.
    
    """
    stop_timeout = 1
    ready_timeout = 2
    
    def __init__(self):
        self._stopped_event = gevent.event.Event()
        self._ready_event = gevent.event.Event()
        self._children = set()
        self._greenlets = gevent.pool.Group()
        self._error_handlers = {}
        self.started = False
    
    @property
    def ready(self):
        """This property returns whether this service is ready for business"""
        return self._ready_event.isSet()
    
    def set_ready(self):
        """Internal convenience function to proclaim readiness"""
        self._ready_event.set()
    
    def add_service(self, service):
        """Add a child service to this service
        
        The service added will be started when this service starts, before 
        its :meth:`_start` method is called. It will also be stopped when this 
        service stops, before its :meth:`_stop` method is called.
        
        """
        if isinstance(service, gevent.baseserver.BaseServer):
            service = ServiceWrapper(service)
        self._children.add(service)
    
    def remove_service(self, service):
        """Remove a child service from this service"""
        self._children.remove(service)
    
    def _wrap_errors(self, func):
        """Wrap a callable for triggering error handlers
        
        This is used by the greenlet spawn methods so you can handle known
        exception cases instead of gevent's default behavior of just printing
        a stack trace for exceptions running in parallel greenlets.
        
        """
        def wrapped_f(*args, **kwargs):
            exceptions = tuple(self._error_handlers.keys())
            try:
                return func(*args, **kwargs)
            except exceptions, exception:
                for type in self._error_handlers:
                    if isinstance(exception, type):
                        handler, greenlet = self._error_handlers[type]
                        self._wrap_errors(handler)(exception, greenlet)
                return exception
        return wrapped_f
    
    def catch(self, type, handler):
        """Set an error handler for exceptions of `type` raised in greenlets"""
        self._error_handlers[type] = (handler, gevent.getcurrent())
    
    def spawn(self, func, *args, **kwargs):
        """Spawn a greenlet under this service"""
        func_wrap = self._wrap_errors(func)
        return self._greenlets.spawn(func_wrap, *args, **kwargs)
    
    def spawn_later(self, seconds, func, *args, **kwargs):
        """Spawn a greenlet in the future under this service"""
        group = self._greenlets
        func_wrap = self._wrap_errors(func)
        g = group.greenlet_class(func_wrap, *args, **kwargs)
        g.start_later(seconds)
        group.add(g)
        return g
    
    def start(self, block_until_ready=True):
        """Public interface for starting this service and children. By default it blocks until ready."""
        assert not self.started, '%s already started' % self.__class__.__name__
        self._stopped_event.clear()
        self._ready_event.clear()
        try:
            self.pre_start()
            for child in self._children:
                if isinstance(child, Service):
                    child.start(block_until_ready)
                elif isinstance(child, gevent.baseserver.BaseServer):
                    child.start()
            ready = self.do_start()
            if ready == NOT_READY and block_until_ready is True:
                self._ready_event.wait(self.ready_timeout)
            elif ready != NOT_READY:
                self._ready_event.set()
            self.started = True
            self.post_start()
        except:
            self.stop()
            raise
    
    def pre_start(self):
        pass
    
    def post_start(self):
        pass
    
    def do_start(self):
        """Empty implementation of service start. Implement me!
        
        Return `service.NOT_READY` to block until :meth:`set_ready` is
        called (or `ready_timeout` is reached).
        
        """
        return
    
    def stop(self, timeout=None):
        """Stop this service and child services

        If the server uses a pool to spawn the requests, then :meth:`stop` also waits
        for all the handlers to exit. If there are still handlers executing after *timeout*
        has expired (default 1 second), then the currently running handlers in the pool are killed."""
        if gevent.getcurrent() in self._greenlets:
            return gevent.spawn(self.stop)
        self.started = False
        try:
            self.pre_stop()
            for child in self._children:
                child.stop()
            self.do_stop()
        finally:
            if timeout is None:
                timeout = self.stop_timeout
            if self._greenlets:
                self._greenlets.join(timeout=timeout)
                self._greenlets.kill(block=True, timeout=1)
            self._ready_event.clear()
            self._stopped_event.set()
            self.post_stop()
    
    def pre_stop(self):
        pass
    
    def post_stop(self):
        pass
    
    def do_stop(self):
        """Empty implementation of service stop. Implement me!"""
        return
    
    def do_reload(self):
        """Empty implementation of service reload. Implement me!"""
        pass

    def serve_forever(self, stop_timeout=None):
        """Start the service if it hasn't been already started and wait until it's stopped."""
        if not self.started:
            self.start()
        try:
            self._stopped_event.wait()
        except:
            self.stop(timeout=stop_timeout)
            raise
