"""A distributed group membership module

This provides distributed group membership for easily building clustered
applications with gevent. Using this in your app, you just provide the IP
of another node in the cluster and it will receive the IPs of all nodes in
the cluster. When a node joins or drops from the cluster, all other nodes find
out immediately.

The roster is managed by a leader. When you create a cluster, you tell the
first node it is the leader (by simply pointing it to its own IP). As you
add nodes, you can point them to the leader or any other node. If a node
is not the leader, it will redirect the connection to the leader. All nodes
also maintain a keepalive with the leader.

If the leader drops from the cluster, the nodes will dumbly pick a new leader
by taking the remaining node list, sorting it, and picking the first node. If
a node happens to get a different leader, as long as it is in the cluster, it
will be redirected to the right leader. 

To try it out on one machine, you need to make several more loopback interfaces:

In OSX:
 ifconfig lo0 inet 127.0.0.2 add
 ifconfig lo0 inet 127.0.0.3 add
 ifconfig lo0 inet 127.0.0.4 add

In Linux:
 ifconfig lo:2 127.0.0.2 up
 ifconfig lo:3 127.0.0.3 up
 ifconfig lo:4 127.0.0.4 up
 
Now you can start the first node on 127.0.0.1:
 INTERFACE=127.0.0.1 python cluster.py

The first argument is the leader, the second is the interface to bind to.
 
Start the others pointing to 127.0.0.1:
 INTERFACE=127.0.0.2 LEADER=127.0.0.1 python cluster.py
 INTERFACE=127.0.0.3 LEADER=127.0.0.1 python cluster.py

Try starting the last one pointing to a non-leader:
 INTERFACE=127.0.0.4 LEADER=127.0.0.3 python cluster.py

Now you can kill any node (including the leader) and bring up another node 
pointing to any other node, and they all get updated immediately.

"""
import gevent.monkey; gevent.monkey.patch_all(thread=False)

import logging
import socket
import json

import gevent
import gevent.server
import gevent.socket

import util
import service

CLIENT_TIMEOUT_SECONDS = 10
SERVER_KEEPALIVE_SECONDS = 5

def logger(obj):
    name = '%s.%s' % (obj.__module__, obj.__class__.__name__)
    return logging.getLogger(name)

class ClusterError(Exception): pass
class NewLeader(Exception): pass

class ClusterManager(service.Service):
    def __init__(self, callback, listen_address, leader_address=None, client_hostname=None):
        super(ClusterManager, self).__init__()
        self.server = PeerServer(self, listen_address)
        self.client = PeerClient(self, leader_address, client_hostname)
        self.cluster = set()
        self._callback = callback
        
        self.add_service(self.server)
        if leader_address:
            self.add_service(self.client)
            self.is_leader = False
        else:
            self.is_leader = True
    
    def trigger_callback(self):
        if self._callback:
            self._callback(self.cluster.copy())

class PeerServer(service.Service):
    def __init__(self, manager, address):
        super(PeerServer, self).__init__()
        self.logger = logger(self)
        self.manager = manager
        self.address = address
        self.clients = {}
        self.server = gevent.server.StreamServer(address, 
                        handle=self.handle, spawn=self.spawn)
        
        self.add_service(self.server)
    
    def do_start(self):
        if self.manager.is_leader:
            self.manager.cluster.add(self.address[0])
            self.manager.trigger_callback()
    
    def handle(self, socket, address):
        """
        If not a leader, a node will simply return a single item list pointing
        to the leader. Otherwise, it will add the host of the connected client
        to the cluster roster, broadcast to all nodes the new roster, and wait
        for keepalives. If no keepalive within timeout or the client drops, it
        drops it from the roster and broadcasts to all remaining nodes. 
        """
        self.logger.debug('New connection from %s:%s' % address)
        if not self.manager.is_leader:
            socket.send(json.dumps({'leader': self.manager.client.leader_address[0], 
                'port': self.manager.client.leader_address[1]}))
            socket.close()
            self.logger.debug("Redirected to %s:%s" % self.manager.client.leader_address)
        else:
            socket.send(self._cluster_message())
            sockfile = socket.makefile()
            name = sockfile.readline()
            if not name:
                return
            if name == '\n':
                name = address[0]
            else:
                name = name.strip()
            self._update(add={'host': name, 'socket': socket})
            # TODO: Use TCP keepalives
            timeout = self._client_timeout(socket)
            for line in util.line_protocol(sockfile, strip=False):
                timeout.kill()
                timeout = self._client_timeout(socket)
                socket.send('\n')
                self.logger.debug("Keepalive from %s:%s" % address)
            self.logger.debug("Client disconnected from %s:%s" % address)
            self._update(remove=name)
    
    def _client_timeout(self, socket):
        def shutdown(socket):
            try:
                socket.shutdown(0)
            except IOError:
                pass
        return self.spawn_later(CLIENT_TIMEOUT_SECONDS, 
                lambda: shutdown(socket))
    
    def _cluster_message(self):
        return '%s\n' % json.dumps({'cluster': list(self.manager.cluster)})
    
    def _update(self, add=None, remove=None):
        """ Used by leader to manage and broadcast roster """
        if add is not None:
            self.manager.cluster.add(add['host'])
            self.clients[add['host']] = add['socket']
            self.logger.debug("Added to cluster: %s" % add['host'])
        if remove is not None:
            self.manager.cluster.remove(remove)
            del self.clients[remove]
            self.logger.debug("Removed from cluster: %s" % remove)
        for client in self.clients:
            self.clients[client].send(self._cluster_message())
        self.manager.trigger_callback()

class PeerClient(service.Service):
    def __init__(self, manager, leader_address, client_hostname=None):
        super(PeerClient, self).__init__()
        self.logger = logger(self)
        self.manager = manager
        self.leader_address = leader_address
        self.client_hostname = client_hostname
        
        # For connection retries. None means default
        self._max_retries = 5
        self._delay = None
        self._max_delay = None
    
    def do_start(self):
        self.spawn(self.connect)
        return service.NOT_READY

    def connect(self):
        while True:
            self.logger.debug("Connecting to leader at %s:%s" % 
                                self.leader_address)
            try:
                socket = util.connect_and_retry(self.leader_address, 
                            max_retries=self._max_retries, delay=self._delay, 
                            max_delay=self._max_delay)
            except IOError:
                raise ClusterError("Unable to connect to leader %s:%s" % 
                                                    self.leader_address)
            self.handle(socket)
    
    def handle(self, socket):
        self.set_ready()
        self.logger.debug("Connected to leader")
        client_address = self.client_hostname or socket.getsockname()[0]
        socket.send('%s\n' % client_address)
        # TODO: Use TCP keepalives
        keepalive = self._server_keepalive(socket)
        try:
            for line in util.line_protocol(socket, strip=False):
                if line == '\n':
                    # Keepalive ack from leader
                    keepalive.kill()
                    keepalive = self._server_keepalive(socket)
                else:
                    cluster = json.loads(line)
                    if 'leader' in cluster:
                        # Means you have the wrong leader, redirect
                        host = cluster['leader']
                        port = cluster.get('port', self.leader_address[1])
                        self.leader_address = (host, port)
                        self.logger.info("Redirected to %s:%s..." % 
                                            self.leader_address)
                        raise NewLeader()
                    elif client_address in cluster['cluster']:
                        # Only report cluster once I'm a member
                        self.manager.cluster = set(cluster['cluster'])
                        self.manager.trigger_callback()
            self._leader_election()
        except NewLeader:
            self.manager.trigger_callback()
            if self.leader_address[0] == client_address:
                self.manager.is_leader = True
                self.stop()
            else:
                return
    
    def _server_keepalive(self, socket):
        return self.spawn_later(SERVER_KEEPALIVE_SECONDS, 
            lambda: socket.send('\n'))
    
    def _leader_election(self):
        candidates = list(self.manager.cluster)
        candidates.remove(self.leader_address[0])
        candidates.sort()
        self.manager.leader = candidates[0]
        self.logger.info("New leader %s:%s..." % self.manager.leader_address)
        # TODO: if i end up thinking i'm the leader when i'm not
        # then i will not rejoin the cluster
        raise NewLeader()

