import os

# These are configuration values that can be overridden by command 
# line arguments. 
pidfile = "demo.pid"
logfile = "demo.log"
name = "demo daemon"

# These values can be used as custom app configuration, maybe passing to 
# the service returned below using globals()
foo = "bar"
widgets = 90
from_env = os.environ.get("ENV_VAR", "default value")

# A "service" function is expected to be defined and return a Service
# object that represents the application to run as a daemon
def service():
    # It's important to know you MUST make any imports that
    # use gevent to happen INSIDE this function
    import gevent
    from gservice.core import Service
    
    # Normally you would just import your app and instanciate, but here
    # we are making a service up right here.
    class DemoService(Service):
        def do_start(self):
            self.spawn(self.run)
        
        def run(self):
            while True:
                print "Hello"
                gevent.sleep(1) 
    
    return DemoService()