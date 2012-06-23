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

If you save this as *hello.py* you can run it with the Ginkgo runner::

    $ ginkgo hello.HelloWorld

This should run your service, giving you a stream of "Hello World" lines.

To stop your service, hit Ctrl+C.

Writing a Server
----------------
A service is not a server until you make it one. Using gevent, this is
easy using the StreamServer service to do the work of running a TCP
server::

    from ginkgo import Service
    from ginkgo.async.gevent import StreamServer

    class HelloWorldServer(Service):
        def __init__(self):
            self.add_service(StreamServer(('0.0.0.0', 7000), self.handle))

        def handle(self, socket, address):
            while True:
                socket.send("Hello World\n")
                self.async.sleep(1)

Save this as *quickstart.py* and run with::

    $ ginkgo quickstart.HelloWorldServer

It will start listening on port 7000. We can connect with netcat::

    $ nc localhost 7000

Again we see a stream of "Hello World" lines, but this time being sent over
TCP. You can open more netcat connections to see it running concurrently
just fine.

Notice our HelloWorldServer implementation is *composed* of a generic
StreamServer and doesn't need to implement anything else other than a
handler for that StreamServer.

Writing a Client
----------------
A client that maintains a persistent connection (or maybe pool of
connections) to a server also makes sense to be modeled as a Service.
Let's add a client to our HelloWorldServer in our quickstart module. Now
it looks like this::

    from ginkgo import Service
    from ginkgo.async.gevent import StreamServer
    from ginkgo.async.gevent import StreamClient

    class HelloWorldServer(Service):
        def __init__(self):
            self.add_service(StreamServer(('0.0.0.0', 7000), self.handle))

        def handle(self, socket, address):
            while True:
                socket.send("Hello World\n")
                self.async.sleep(1)

    class HelloWorldClient(Service):
        def __init__(self):
            self.add_service(StreamClient(('0.0.0.0', 7000), self.handle))

        def handle(self, socket):
            fileobj = socket.makefile()
            while True:
                print fileobj.readline().strip()

Save and run the server first with::

    $ ginkgo quickstart.HelloWorldServer

Let that run, switch to a new terminal and run the client with::

    $ ginkgo quickstart.HelloWorldClient

As you'd expect, the client connects to the server and prints all the
"Hello World" lines it receives.

Service Composition
-------------------
We've already been doing service composition by using generic TCP server
and client services to build our HelloWorld services. These primitives
are services themselves, just like the ones you've been making. So you
can compose and aggregate your own services the same way.

Let's combine our client and server by add a HelloWorld service in
our quickstart module. It now looks like this::

    from ginkgo import Service
    from ginkgo.async.gevent import StreamServer
    from ginkgo.async.gevent import StreamClient

    class HelloWorldServer(Service):
        def __init__(self):
            self.add_service(StreamServer(('0.0.0.0', 7000), self.handle))

        def handle(self, socket, address):
            while True:
                socket.send("Hello World\n")
                self.async.sleep(1)

    class HelloWorldClient(Service):
        def __init__(self):
            self.add_service(StreamClient(('0.0.0.0', 7000), self.handle))

        def handle(self, socket):
            fileobj = socket.makefile()
            while True:
                print fileobj.readline().strip()

    class HelloWorld(Service):
        def __init__(self):
            self.add_service(HelloWorldServer())
            self.add_service(HelloWorldClient())

Save and we can run our new aggregate service::

    $ ginkgo quickstart.HelloWorld

Now the client and server are both running, giving us effectively what
we came in with.

Using a Web Framework
---------------------
Adding a web server our HelloWorld service is quite trivial. Here we use
gevent's WSGI server implementation::

    from ginkgo import Service
    from ginkgo.async.gevent import StreamServer
    from ginkgo.async.gevent import StreamClient
    from ginkgo.async.gevent import WSGIServer

    class HelloWorldServer(Service):
        def __init__(self):
            self.add_service(StreamServer(('0.0.0.0', 7000), self.handle))

        def handle(self, socket, address):
            while True:
                socket.send("Hello World\n")
                self.async.sleep(1)

    class HelloWorldClient(Service):
        def __init__(self):
            self.add_service(StreamClient(('0.0.0.0', 7000), self.handle))

        def handle(self, socket):
            fileobj = socket.makefile()
            while True:
                print fileobj.readline().strip()

    class HelloWorldWebServer(Service):
        def __init__(self):
            self.add_service(WSGIServer(('0.0.0.0', 8000), self.handle))

        def handle(self, environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/html')])
            return ["<strong>Hello World</strong>"]

    class HelloWorld(Service):
        def __init__(self):
            self.add_service(HelloWorldServer())
            self.add_service(HelloWorldClient())
            self.add_service(HelloWorldWebServer())

Running `quickstart.HelloWorld` with Ginkgo will run a server, a client,
and a web server. The client will be printing our stream of "Hello
World" lines. Our server is also available to be connected to via
netcat. And we can also connect to our web server with curl::

    $ curl http://localhost:8000

And we see a strong declaration of "Hello World".

In that example our web server implements a small WSGI application, but
you can also use any WSGI compatible web framework. Here is an example
of the Flask Hello World runnable with Ginkgo using `AppServer`::

    from flask import Flask
    from ginkgo.async.gevent import WSGIServer

    app = Flask(__name__)

    @app.route("/")
    def hello():
        return "Hello World!"

    def AppServer():
        return WSGIServer(('0.0.0.0', 8000), app)

Notice AppServer a callable that returns a service, in this case a
pre-configured WSGIServer.

Using Configuration
-------------------
TODO



