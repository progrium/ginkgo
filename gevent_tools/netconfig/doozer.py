from __future__ import absolute_import
import doozer

from gevent_tools import netconfig

class DoozerStore(netconfig.ConfigStoreService):
    name = 'doozer'
    
    def __init__(self, uri=None):
        super(DoozerStore, self).__init__()
        self.uri = uri
        self.client = None
        doozer._spawner = self.spawn
    
    def do_start(self):
        self.client = doozer.connect(self.uri)
    
    def do_stop(self):
        if self.client:
            self.client.disconnect()
    
    def get(self, path):
        return self.client.get(path).value
    
    def set(self, path, value):
        latest_rev = self.client.rev().rev
        self.client.set(path, value, latest_rev)
    
    def delete(self, path):
        latest_rev = self.client.rev().rev
        self.client.delete(path, latest_rev)
    
    def list(self, path):
        entities = self.client.getdir(path)
        return [entity.path for entity in entities]

netconfig.register(DoozerStore)