
import doozerd
import gevent

form gevent_tools import service

def ZMQService(name, base=service.Service):
    class zmq_service(base):
        def pre_start(self):
            # init doozer if not
            # listen for requests, dispatch to exposed methods
        
        def post_start(self):
            super(zmq_service, self).post_start()
            # register on post_start
        
        def post_stop(self):
            # close doozer on stop if last
    return zmq_service