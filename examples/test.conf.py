from ginkgo import Service as _Service
from ginkgo import Setting

daemon = True
delay = 1

class MyService(_Service):
    foo = Setting("foo", default=("foo", 12), help="This is foo")
    bar = Setting("bar", help="This is bar")
    delay = Setting("delay", default=1, help="Delay between hello printing")

    def do_start(self):
        print "Hello here"
        self.spawn(self.loop)

    def do_reload(self):
        print "reloaded!"

    def loop(self):
        while True:
            print "hello"
            self.async.sleep(self.delay)

service = MyService
