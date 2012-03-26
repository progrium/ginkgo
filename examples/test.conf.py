
from ginkgo import Service as _Service
from ginkgo import Setting

class MyService(_Service):
    foo = Setting("foo", default=("foo", 12), help="This is foo")
    bar = Setting("bar", help="This is bar")

    def do_start(self):
        print "Hello here"
        self.spawn(self.loop)

    def loop(self):
        while True:
            print "hello"
            self.async.sleep(1)

service = MyService
