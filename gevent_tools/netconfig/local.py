import os.path
import fnmatch

import netconfig

class LocalStore(netconfig.ConfigStoreService):
    name = 'local'
    data = {}
    
    def do_start(self):
        pass
    
    def do_stop(self):
        pass
    
    def get(self, path):
        return self.data.get(path)
    
    def set(self, path, value):
        self.data[path] = value
    
    def list(self, path):
        pattern = "%s/*" % path
        children = filter(lambda x: fnmatch.fnmatch(x, pattern), 
                            self.data.keys())
        return map(os.path.basename, children)

    def delete(self, path):
        del self.data[path]

netconfig.register(LocalStore)