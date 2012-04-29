Quickstart
==========

Before you get started, be sure you have Ginkgo installed.

Hello World Service
-------------------
The simplest service you could write looks something like this::

    from ginkgo import Service

    class HelloWorld(Service):
        def do_start(self):
            self.spawn(self.hello_forever)

        def hello_forever(self):
            while True:
                print "Hello World"
                self.async.sleep(1)

If you save this as *service.py* you can run it with the Ginkgo runner::

    $ ginkgo service.HelloWorld

This should run your service, giving you a stream of "Hello World" lines.

To stop your service, hit Ctrl+C.

Using Configuration
-------------------
Add the ``-h`` argument flag to our runner call::

    $ ginkgo service.HelloWorld -h

You'll see that the ``ginkgo`` runner command itself is very simple, but what's
interesting is the last section::

    config settings:
      daemon         True or False whether to daemonize [False]
      group          Change to a different group before running [None]
      logconfig      Configuration of standard Python logger. Can be dict for basicConfig,
                      dict with version key for dictConfig, or ini filepath for fileConfig. [None]
      logfile        Path to primary log file. Ignored if logconfig is set. [/tmp/HelloWorld.log]
      loglevel       Log level to use. Valid options: debug, info, warning, critical
                      Ignored if logconfig is set. [debug]
      pidfile        Path to pidfile to use when daemonizing [None]
      rundir         Change to a directory before running [None]
      umask          Change file mode creation mask before running [None]
      user           Change to a different user before running [None]

These are builtin settings and their default values. If you want to set any of
these, you have to create a configuration file. But you can also create your
own settings, so let's first change our Hello World service to be configurable::

    from ginkgo import Service, Setting

    class HelloWorld(Service):
        message = Setting("message", default="Hello World",
            help="Message to print out while running")

        def do_start(self):
            self.spawn(self.message_forever)

        def message_forever(self):
            while True:
                print self.message
                self.async.sleep(1)

Running ``ginkgo service.HelloWorld -h`` again should now include your new
setting. Let's create a configuration file now called *service.conf.py*::

    import os
    daemon = bool(os.environ.get("DAEMONIZE", False))
    message = "Services all the way down."
    service = "service.HelloWorld"

A configuration file is simply a valid Python source file. In it, you define
variables of any type using the setting name to set them.

There's a special setting calling ``service`` that must be set, which is the
class path target telling it what service to run. To run with this
configuration, you just point ``ginkgo`` to the configuration file::

    $ ginkgo service.conf.py

And it should start and you should see "Services all the way down" repeating.

You don't have direct access to set config settings from the ``ginkgo`` tool,
but you can set values in your config to pull from the environment. For
example, our configuration above lets us force our service to daemonize by
setting the ``DAEMONIZE`` environment variable::

    $ DAEMONIZE=yes ginkgo service.conf.py

To stop the daemonized process, you can manually kill it or use the service
management tool ``ginkgoctl``::

    $ ginkgoctl service.conf.py stop

Service Manager
---------------
Running and stopping your service is easy with ``ginkgo``, but once you
daemonize, it gets harder to interface with it. The ``ginkgoctl`` utility is
for managing a daemonized service process.

::

    $ ginkgoctl -h
    usage: ginkgoctl [-h] [-v] [-p PID]
                     [target] {start,stop,restart,reload,status,log,logtail}

    positional arguments:
      target                service class path to use (modulename.ServiceClass) or
                            configuration file path to use (/path/to/config.py)
      {start,stop,restart,reload,status,log,logtail}

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      -p PID, --pid PID     pid or pidfile to use instead of target

Like ``ginkgo`` it takes a target class path or configuration file. For
``stop``, ``reload``, and ``status`` it can also just take a pid or pidfile
with the ``pid`` argument.

Using ``ginkgoctl`` will always force your service to daemonize
when you use the ``start`` action.

Service Model and Reloading
---------------------------
Our service model lets you implement three main hooks on services:
``do_start()``, ``do_stop()``, and ``do_reload()``. We've used ``do_start()``,
which is run when a service is starting up. Not surprisingly, ``do_stop()`` is
run when a service is shutting down. When is ``do_reload()`` run? Well,
whenever ``reload()`` is called. :)

Services are designed to contain other services like object composition. Though
after adding services to a service, when you call any of the service interface
methods, they will propogate down to child services. This is done in the actual
``start()``, ``stop()``, and ``reload()`` methods. The ``do_`` methods are for
you to implement specifically what happens for *that* service to
start/stop/reload. 

So when is ``reload()`` called? Okay, I'll skip ahead and just say it gets
called when the process receives a SIGHUP signal. As you may have guessed, for
convenience, this is exposed in ``ginkgoctl`` with the ``reload`` action.

The semantics of ``reload`` are up to you and your application or service.
Though one thing happens automatically when a process gets a reload signal:
configuration is reloaded. 

One use of ``do_reload()`` is to take new configuration and perform any
operations to apply that configuration to your running service. However, as
long as you access a configuration setting by reference via the ``Setting``
descriptor, you may not need to do anything -- the value will just update in
real-time.

Let's see this in action. We'll change our Hello World service to have a
``rate_per_minute`` setting that will be used for our delay between messages::

    from ginkgo import Service, Setting

    class HelloWorld(Service):
        message = Setting("message", default="Hello World",
            help="Message to print out while running")

        rate = Setting("rate_per_minute", default=60,
            help="Rate at which to emit message")

        def do_start(self):
            self.spawn(self.message_forever)

        def message_forever(self):
            while True:
                print self.message
                self.async.sleep(60.0 / self.rate)

The default is 60 messages a minute, which results in the same behavior as
before. So let's change our configuration to use a different rate::

    import os
    daemon = bool(os.environ.get("DAEMONIZE", False))
    message = "Services all the way down."
    rate_per_minute = 180
    service = "service.HelloWorld"

Use ``ginkgo`` to start the service::

    $ ginkgo service.conf.py

As you can see, it's emitting messages a bit faster now. About 3 per second.
Now while that's running, open the configuration file and change
rate_per_minute to some other value. Then, in another terminal, change to that
directory and reload::

    $ ginkgoctl service.conf.py reload

Look back at your running service to see that it's now using the new emit rate.

Using Logging
-------------
Logging with Ginkgo is based on standard Python logging. We make sure it works
with daemonization and provide Ginkgo-friendly ways to configure it with good
defaults. We even support reloading logging configuration.

Out of the box, you can just start logging. We encourage you to use the common
convention of module level loggers, but obviously there is a lot of freedom in
how you use Python logging. Let's add some logging to our Hello World,
including changing our print call to a logger call as it's better practice::

    import logging
    from ginkgo import Service, Setting

    logger = logging.getLogger(__name__)

    class HelloWorld(Service):
        message = Setting("message", default="Hello World",
            help="Message to print out while running")

        rate = Setting("rate_per_minute", default=60,
            help="Rate at which to emit message")

        def do_start(self):
            logger.info("Starting up!")
            self.spawn(self.message_forever)

        def do_stop(self):
            logger.info("Goodbye.")

        def message_forever(self):
            while True:
                logger.info(self.message)
                self.async.sleep(60.0 / self.rate)

Let's run it with our existing configuration for a bit and then stop::

    $ ginkgo service.conf.py
    Starting process with service.conf.py...
    2012-04-28 17:21:32,608    INFO service: Starting up!
    2012-04-28 17:21:32,608    INFO service: Services all the way down.
    2012-04-28 17:21:33,609    INFO service: Services all the way down.
    2012-04-28 17:21:34,610    INFO service: Services all the way down.
    2012-04-28 17:21:35,714    INFO service: Goodbye.
    2012-04-28 17:21:35,714    INFO runner: Stopping.

Running ``-h`` will show you that the default logfile is going to be
*/tmp/HelloWorld.log*, which logging will create and append to if you
daemonize.

To configure logging, Ginkgo exposes two settings for simple case
configuration: ``logfile`` and ``loglevel``. If that's not enough, you can use
``logconfig``, which will override any value for ``logfile`` and ``loglevel``.

Using ``logconfig`` you can configure logging as expressed by
``logging.basicConfig``. By default, if you set ``logconfig`` to a dictionary,
it will apply those keyword arguments to ``logging.basicConfig``.  You can
learn more about ``logging.basicConfig``
`here <http://docs.python.org/library/logging.html#logging.basicConfig>`_.

For advanced configuration, we also let you use ``logging.config`` from the
``logconfig`` setting. If ``logconfig`` is a dictionary with a ``version`` key,
we will load it into ``logging.config.dictConfig``. If ``logconfig`` is a path
to a file, we load it into ``logging.config.fileConfig``.  Both of these are
ways to define a configuration structure that lets you create just about any
logging configuration. Read more about ``logging.config``
`here <http://docs.python.org/library/logging.config.html#module-logging.config>`_.


Writing a Server
----------------

TODO

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



Writing a Client
----------------

TODO

Composing Services
------------------

TODO

Async Programming
-----------------

TODO

Using a Web Framework
---------------------

TODO
