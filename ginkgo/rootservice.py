import ginkgo.core

class RootService(ginkgo.core.Service):
    """
    RootService is the main service for all gsevice based daemons.
    Creation and management of RootService is managed directly by the ginkgo
    runner.

    RootService is the parent service for all named global services, and they
    will be stopped when RootService is stopped.  RootService is also the
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
            ginkgo.core.Service.register_named_service(name=name,
                service=service)
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
            # tell the other children to stop now
        except KeyboardInterrupt:
            # swallowing keyboard interrupt
            self.stop(timeout=stop_timeout)            
        except:
            # raising other exceptions
            self.stop(timeout=stop_timeout)
            raise
        else:
            # or just stopping if no exception
            self.stop(timeout=stop_timeout)
