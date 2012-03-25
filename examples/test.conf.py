
from ginkgo import Service
from ginkgo import Setting

class MyService(Service):
    foo = Setting("foo", default=("foo", 12), help="This is foo")
    bar = Setting("bar", help="This is bar")

    def do_start(self):
        print "Hello here"
        self.spawn(self.loop)

    def loop(self):
        print "hello"
        self.async.sleep(1)
