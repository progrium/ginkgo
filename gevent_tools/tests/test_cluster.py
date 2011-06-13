import json

from gevent.hub import greenlet
import gevent
import gevent.event
import gevent.socket
import nose.tools

from gevent_tools.toys import cluster

port = 6000

class ClusterManagerMock(object):
    is_leader = True

    class client:
        leader_address = ('127.0.0.1', port)
    
    def __init__(self):
        self.cluster = set()
    
    def trigger_callback(self):
        pass

def yield_(n=1):
    for i in xrange(n):
        gevent.sleep(0)

# cluster.PeerServer

def test_leader_first_returns_existing_cluster():
    cm = ClusterManagerMock()
    cm.cluster = set(['a', 'b', 'c'])
    s = cluster.PeerServer(cm, ('127.0.0.1', port))
    s.start()
    socket = gevent.socket.create_connection(('127.0.0.1', port))
    sockfile = socket.makefile()
    line = sockfile.readline()
    obj = json.loads(line.strip())
    assert set(obj['cluster']) == cm.cluster, \
        "First line didn't report correct cluster: %s" % line
    s.stop()

def test_nonleader_redirects_to_leader_with_port():
    cm = ClusterManagerMock()
    cm.is_leader = False
    s = cluster.PeerServer(cm, ('127.0.0.1', port))
    s.start()
    socket = gevent.socket.create_connection(('127.0.0.1', port))
    sockfile = socket.makefile()
    line = sockfile.readline()
    obj = json.loads(line.strip())
    assert obj['leader'] == cm.client.leader_address[0], \
        "First line didn't point to leader: %s" % line
    assert 'port' in obj, "Did not include port"
    s.stop()

def test_leader_adds_node_to_cluster_by_name():
    node_name = 'node-a'
    cm = ClusterManagerMock()
    cm.is_leader = True
    s = cluster.PeerServer(cm, ('127.0.0.1', port))
    s.start()
    socket = gevent.socket.create_connection(('127.0.0.1', port))
    sockfile = socket.makefile()
    line = sockfile.readline()
    socket.send("%s\n" % node_name)
    line = sockfile.readline()
    assert node_name in cm.cluster, \
        "Leader did not add name to cluster: %s" % line
    s.stop()
    del socket
    del sockfile

def test_leader_adds_node_to_cluster_by_hostip():
    cm = ClusterManagerMock()
    cm.is_leader = True
    s = cluster.PeerServer(cm, ('127.0.0.1', port))
    s.start()
    socket = gevent.socket.create_connection(('127.0.0.1', port))
    sockfile = socket.makefile()
    line = sockfile.readline()
    socket.send("\n")
    line = sockfile.readline()
    assert '127.0.0.1' in cm.cluster, \
        "Leader did not add host to cluster: %s" % line
    s.stop()

def test_drop_node_on_disconnect():
    node_name = 'node'
    cm = ClusterManagerMock()
    cm.is_leader = True
    s = cluster.PeerServer(cm, ('127.0.0.1', port))
    s.start()
    socket = gevent.socket.create_connection(('127.0.0.1', port))
    sockfile = socket.makefile()
    line = sockfile.readline() # cluster list pre-join
    socket.send("%s\n" % node_name)
    line = sockfile.readline() # cluster list post-join
    assert node_name in cm.cluster, \
        "Leader did not add host to cluster: %s" % line
    socket.shutdown(0)
    # Make sure to cleanup file descriptors:
    del sockfile
    del socket
    yield_(2) # Yield to let PeerServer catch the disconnect
    assert not node_name in cm.cluster, \
        "Leader did not remove host from cluster."
    s.stop()

# cluster.PeerClient

def test_joins_cluster():
    interface = '127.0.0.1' # I guess we'll just assume this
    cm = ClusterManagerMock()
    cm.is_leader = True
    cm.cluster = set()
    s = cluster.PeerServer(cm, ('0.0.0.0', port))
    s.start()
    assert len(cm.cluster) == 1, "Cluster is not only leader"
    c = cluster.PeerClient(cm, s.address)
    c.start() # This will block until "ready", in this case connected 
    yield_(2) # Yield to let PeerServer update cluster roster
    assert len(cm.cluster) > 1, "Client did not join cluster"
    assert interface in cm.cluster, \
        "Client did not join cluster using interface as name"
    c.stop()
    s.stop()

def test_joins_cluster_with_named_host():
    name = 'localhost'
    cm = ClusterManagerMock()
    cm.is_leader = True
    cm.cluster = set()
    s = cluster.PeerServer(cm, ('0.0.0.0', port))
    s.start()
    assert len(cm.cluster) == 1, "Cluster is not only leader"
    c = cluster.PeerClient(cm, s.address, client_hostname=name)
    c.start() # This will block until "ready", in this case connected 
    yield_(2) # Yield to let PeerServer update cluster roster
    assert len(cm.cluster) > 1, "Client did not join cluster"
    assert name in cm.cluster, \
        "Client did not join cluster using interface as name"
    c.stop()
    s.stop()

def test_follows_redirect_to_leader():
    follower = ClusterManagerMock()
    follower.is_leader = False
    follower.client.leader_address = ('127.0.0.1', 6001)
    s1 = cluster.PeerServer(follower, ('0.0.0.0', port))
    s1.start()
    leader = ClusterManagerMock()
    leader.is_leader = True
    s2 = cluster.PeerServer(leader, ('127.0.0.1', 6001))
    s2.start()
    cm = ClusterManagerMock()
    cm.is_leader = False
    c = cluster.PeerClient(cm, ('127.0.0.1', port))
    c.start()
    yield_(6)
    # If follower was a real node, it would not have an empty roster.
    # However it's useful here to see we connected to the right node.
    assert len(follower.cluster) == 0, "Joined on the wrong node: %s" % follower.cluster
    assert len(leader.cluster) > 0, "Didn't join on the right node"
    c.stop()
    s1.stop()
    s2.stop()

@nose.tools.raises(cluster.ClusterError)
def test_raise_when_cant_connect():
    cm = ClusterManagerMock()
    cm.is_leader = False
    c = cluster.PeerClient(cm, ('', 16666))
    c._max_retries = 1
    c._delay = 0.1
    c._max_delay = 0.5
    c.catch(cluster.ClusterError, lambda e,g: g.throw(e))
    c.start()
    c.stop()
    

def test_leader_election_on_disconnect():
    pass
    
# cluster.ClusterManager (integration/functional testing)

def test_cluster_manager_as_leader():
    roster = []
    updated = gevent.event.Event()
    def callback(c):
        del roster[:]
        roster.extend(c)
        updated.set()
    node1 = cluster.ClusterManager(callback, listen_address=('127.0.0.1', port))
    node1.start()
    updated.wait(timeout=1)
    assert '127.0.0.1' in roster, "Node is not in cluster"
    node1.stop()

def test_cluster_manager_as_follower():
    roster = []
    updated = gevent.event.Event()
    def callback(c):
        del roster[:]
        roster.extend(c)
        updated.set()
    leader = ClusterManagerMock()
    leader.is_leader = True
    s = cluster.PeerServer(leader, ('127.0.0.1', port))
    s.start()
    follower = cluster.ClusterManager(callback, listen_address=('127.0.0.1', port+1),
                        leader_address=('127.0.0.1', port), client_hostname="localhost")
    follower.start()
    updated.wait(timeout=1)
    assert set(roster) == set([u'127.0.0.1', u'localhost']), \
        "Follower did not get full roster: %s" % roster
    s.stop()
    follower.stop()