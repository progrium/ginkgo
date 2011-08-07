import gevent

from gevent_tools.ext import zmqservice
from gevent_zeromq import zmq

class PubSubService(zmqservice.ZMQService()):
    def __init__(self):
        self.zmq_setup('mypubsub')
    
    def do_start(self):
        self.spawn(self._run)
        print "started"
    
    def _run(self):
        while True:
            print "ok"
            gevent.sleep(2)
    
    def foo(self):
        return "bar"
    
    def another(self, echo):
        return echo
