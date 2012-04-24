import logging
from ginkgo import Service as _Service
from ginkgo import Setting


daemon = True
delay = 1
logconfig = {"filename": "/tmp/MyService.log", "level": logging.DEBUG}

class MyService(_Service):
    foo = Setting("foo", default=("foo", 12), help="This is foo")
    bar = Setting("bar", help="This is bar")
    delay = Setting("delay", default=1, help="Delay between hello printing")

    def __init__(self):
        import logging
        self.log = logging.getLogger(__name__)

    def do_start(self):
        self.log.info("Hello here")
        self.spawn(self.loop)

    def do_reload(self):
        self.log.info("reloaded!")

    def loop(self):
        while True:
            self.log.info("hello")
            self.async.sleep(self.delay)

service = MyService
