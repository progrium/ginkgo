import gevent_tools.service

class GlobalService(gevent_tools.service.Service):
    """
    GlobalService is the main service for all gevent-tools based daemons.
    Creation and management if MasterService is managed directly by the gservice
    runner.

    GlobalService is the parent service for all named global services, and they
    will be stopped when GlobalService is stopped.  GlobalService is also the
    parent for the main service.
    """
    
    def __init__(self, children, main_service):
        """
        Children is a list of 2-tuples (string, service) that should be started
        prior to the main service.

        main is the main service for this daemon
        """
        self._children = []
        for name, service in children:
            self._children.append(service)
            gevent_tools.service.Service(name=name, service=service, register=True)
        # we'll keep a copy of this children array so that we don't
        # force child services to implement __eq__ correctly by calling
        # remove
        self._shutdown_wait_children = list(self._children)
        
        # and append main_service so that it's started last
        self._children.append(main_service)
        self.main_service = main_service

    def serve_forever(self, stop_timeout=None, ready_callback=None):
        if not self.started:
            self.start()
            if ready_callback:
                ready_callback()
        try:
            self.main_service._stopped_event.wait()
            # we've already waited for the main_service so we just need to
            # tell the other children to stop now, swap out _children
            # note: do *not* call .remove_child() here because it forces
            # all application-level services to implement __eq__ correctly
            self._children = self._shutdown_wait_children
            self.stop(timeout=stop_timeout)
        except:
            self.stop(timeout=stop_timeout)
            raise
