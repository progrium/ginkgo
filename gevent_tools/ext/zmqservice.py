import socket
import time

import gevent
from gevent_zeromq import zmq

from gevent_tools import service
from gevent_tools import netconfig

context = zmq.Context()
public_ip = socket.gethostbyname_ex(socket.gethostname())[2][0]

def ZMQService(base=service.Service):
    class zmq_service(base):
        def zmq_setup(self, name=None, prefix='/zmq', type=zmq.REP):
            """Configure the ZMQ service"""
            if name is None:
                name = self.__class__.__name__
            self._zmq_name = '/'.join([prefix, name])
            self._zmq_type = type
        
        def pre_start(self):
            """Get netconfig, create ZMQ socket, start listening"""
            super(zmq_service, self).pre_start()
            self._netconfig = netconfig.get('doozer')
            if not self._netconfig.started:
                # We assume this means we're the first service
                # using the doozer netconfig, so we're responsible
                # for starting/stopping it.
                self.add_service(self._netconfig)
            self._zmq_sock = context.socket(self._zmq_type)
            bind_spec = 'tcp://%s' % public_ip
            port = self._zmq_sock.bind_to_random_port(bind_spec)
            print bind_spec, port
            self._zmq_host = '%s:%s' % (bind_spec, port)
            self.spawn(self._zmq_listen)
        
        def post_start(self):
            """Announce ZMQ socket to netconfig"""
            super(zmq_service, self).post_start()
            self._zmq_hostid = str(int(time.time()))
            self._netconfig.set('%s/hosts/%s' % (self._zmq_name, self._zmq_hostid), self._zmq_host)
            self._netconfig.set('%s/type' % self._zmq_name, str(self._zmq_type))
        
        def pre_stop(self):
            """Renounce ZMQ socket to netconfig"""
            super(zmq_service, self).pre_stop()
            if hasattr(self, '_zmq_hostid'):
                self._netconfig.delete('%s/hosts/%s' % (self._zmq_name, self._zmq_hostid))
        
        def _zmq_listen(self):
            """Listen for requests and dispatch to public methods"""
            while True:
                method, args, kwargs = self._zmq_sock.recv_pyobj()
                if not method.startswith('_'):
                    try:
                        response = getattr(self, method)(*args, **kwargs)
                        self._zmq_sock.send_pyobj(response)
                    except Exception, e:
                        self._zmq_sock.send_pyobj(e)
                else:
                    self._zmq_sock.send_pyobj(AttributeError("service does not provide '%s'" % method))
        
    return zmq_service

class ZMQClient(service.Service):
    def __init__(self, name, prefix='/zmq', type=zmq.REQ):
        super(ZMQClient, self).__init__()
        self._netconfig = netconfig.get('doozer')
        if not self._netconfig.started:
            # We assume this means we're the first service
            # using the doozer netconfig, so we're responsible
            # for starting/stopping it.
            self.add_service(self._netconfig)
        self._zmq_sock = context.socket(type)
        self._zmq_name = '/'.join([prefix, name])
    
    def do_start(self):
        hosts = self._netconfig.list('%s/hosts' % self._zmq_name)
        for host in hosts:
            bind_spec = self._netconfig.get('%s/hosts/%s' % (self._zmq_name, host))
            self._zmq_sock.connect(bind_spec)
    
    def do_stop(self):
        self._zmq_sock.close()
    
    @property
    def rpc(self):
        client = self
        class rpc_proxy(object):
            def __getattr__(self, name):
                def proxy(*args, **kwargs):
                    client._zmq_sock.send_pyobj([name, args, kwargs])
                    return client._zmq_sock.recv_pyobj()
                return proxy
        return rpc_proxy()