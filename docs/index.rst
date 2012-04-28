Ginkgo Service Framework
========================

Ginkgo is a lightweight framework for writing network service daemons in
Python. It currently focuses on gevent as its core networking and concurrency
layer.

The core idea behind Ginkgo is the "service model", where your primary building
block or component of applications are composable services. A service is a
mostly self-contained module of your application that can start/stop/reload,
contain other services, manage async operations, and expose configuration.

::

    class ExampleService(Service):
        setting = Setting("example.setting", default="Foobar")

        def __init__(self):
            logging.info("Service is initializing.")

            self.subservice = AnotherService(self.setting)
            self.add_service(self.subservice)

        def do_start(self):
            logging.info("Service is starting.")

            self.spawn(self.something_async)

        def do_stop(self):
            logging.info("Service is stopping.")

        def do_reload(self):
            logging.info("Service is reloading.")

        # ...

Around this little bit of structure and convention, Ginkgo provides just a few
baseline features to make building both complex and simple network daemons much
easier.

Features
========
- Service class primitive for composing daemon apps from simple components
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

