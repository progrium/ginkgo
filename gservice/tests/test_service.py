import gevent
import nose.tools

from gservice import service

class SlowReadyService(service.Service):
    def do_start(self):
        self.spawn(self._run)
        return service.NOT_READY
    
    def _run(self):
        gevent.sleep(0.5)
        self.set_ready()

class ParentService(service.Service):
    def __init__(self):
        self.child = SlowReadyService()
        self.add_service(self.child)

def test_basic_service():
    class NamedService(service.Service):
        def __init__(self, name):
            self.name = name

    s = NamedService('test')
    s.start()
    assert s.started, "Service is not started"
    assert s.ready, "Service is not ready"
    s.stop()
    assert not s.started, "Service did not stop"

def test_slow_ready_service():
    s = SlowReadyService()
    s.start(block_until_ready=False)
    assert not s.ready, "Service was ready too quickly"
    assert s.started, "Service is not started"
    s.stop()
    assert not s.ready, "Service was still ready after stop"
    assert not s.started, "Service did not stop"
    
    s.start()
    assert s.ready, "Service was not ready after blocking start"
    s.stop()
    assert not s.ready, "Service was still ready after stop"

def test_exception_on_start_stops_service():
    class ErroringService(ParentService):
        def do_start(self):
            raise Exception("Error")
    
    s = ErroringService()
    try:
        s.start()
    except:
        pass
    assert not s.child.started, "Child service still started"
    assert not s.started, "Service is still started"

@nose.tools.raises(NotImplementedError)
def test_greenlet_exception_catching_service():
    class GreenletExceptionService(service.Service):
        def __init__(self):
            self.raised = False
            self.catch(IOError, self.handle_error)
            
        def do_start(self):
            self.spawn(self.run)
            return service.NOT_READY
        
        def handle_error(self, error, greenlet):
            self.raised = True
            raise NotImplementedError("Second Error")
        
        def run(self):
            self.set_ready()
            raise IOError("First Error")
        
    s = GreenletExceptionService()
    def outer_handle(e,g):
        assert s.raised, "Error handler was not called"
        g.throw(e)
    s.catch(NotImplementedError, outer_handle)
    s.start()
    s.stop() # Probably not run

def test_service_serves_forever():
    class StoppingService(service.Service):
        def do_start(self):
            self.spawn(self._run)

        def _run(self):
            gevent.sleep(0.5)
            self.stop()
    
    s = StoppingService()
    g = gevent.spawn(s.serve_forever)
    s._ready_event.wait()
    assert s.started, "Service is not started"
    g.join()
    assert not s.started, "Service is still running"

def test_child_service_starts_with_parent():
    s = ParentService()
    s.start()
    assert s.child.ready, "Child service is not ready"
    assert s.ready, "Parent service is not ready"
    s.stop()
    assert not s.child.started, "Child service is still started"
    assert not s.child.ready, "Child service is still ready"

def test_removed_child_service_still_runs():
    s = ParentService()
    s.start()
    assert s.child.ready, "Child service is not ready"
    assert s.ready, "Parent service is not ready"
    s.remove_service(s.child)
    s.stop()
    assert s.child.started, "Removed service is not still started"
    assert s.child.ready, "Removed service is not still ready"

def test_service_greenlets():
    class GreenletService(service.Service):
        def do_start(self):
            for n in xrange(3):
                self.spawn(self._run, n)
            self.spawn_later(1, self._run, 0)

        def _run(self, index):
            while True:
                gevent.sleep(0.1)
    
    s = GreenletService()
    s.start()
    for greenlet in s._greenlets:
        assert not greenlet.ready(), "Greenlet is ready when it shouldn't be"
    s.stop()
    for greenlet in s._greenlets:
        assert greenlet.ready(), "Greenlet isn't ready after stop"

                
