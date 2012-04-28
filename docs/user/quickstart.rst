Here's what writing a simple server application looks like:

::

    # server.py

    import random

    from gevent.server import StreamServer

    from ginkgo import Service, Setting
    from ginkgo.async.gevent import ServerWrapper

    class NumberServer(Service):
        """TCP server that emits random numbers"""

        address = Setting("numbers.bind", default=('0.0.0.0', 7776))
        emit_rate = Setting("numbers.rate_per_min", default=60)

        def __init__(self):
            self.add_service(ServerWrapper(
                    StreamServer(self.address, self.handle)))

        def handle(self, socket, address):
            while True:
                try:
                    number = random.randint(0, 10)
                    socket.send("{}\n".format(number))
                    self.async.sleep(60 / self.emit_rate)
                except IOError:
                    break # Connection lost

With this module you now have a configurable, daemonizable server ready to be
deployed. Ginkgo gives you a simple runner to execute your app:

::

    $ ginkgo server.NumberServer

As well as a more full featured service management tool:

::

    $ ginkgoctl server.NumberServer start

