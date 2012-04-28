Ginkgo Service Framework
========================

Ginkgo is a lightweight framework for writing network service daemons in
Python. It currently focuses on gevent as its core networking and concurrency
layer.

Here's what writing a simple server application looks like:

::

    import random
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

    $ ginkgo server.NumberServer

As well as a more full featured service management tool:

    $ ginkgoctl server.NumberServer start

Check out the Quickstart to see how you can reload this service and see it
apply configuration changes without stopping!

Features
========
- Service primitive for composing large (or small) apps from simple components
- Dynamic configuration loaded from regular Python source files
- Runner and service manager tool for easy, consistent usage and deployment
- Integrated support for standard Python logging

User Guide
==========

.. toctree::
   :maxdepth: 2

   user/intro
   user/install
   user/quickstart
   user/advanced

API Reference
=============

.. toctree::
   :maxdepth: 2

   api

Developer Guide
===============

.. toctree::
   :maxdepth: 1

   dev/internals
   dev/todo
   dev/authors


* :ref:`search`

