
def service():
    import gevent
    from gevent_tools.service import Service
    
    class DemoService(Service):
        def do_start(self):
            self.spawn(self.run)
        
        def run(self):
            while True:
                print "Hello"
                gevent.sleep(1) 
    
    return DemoService()