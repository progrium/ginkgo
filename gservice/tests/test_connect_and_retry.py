import gevent
import gevent.socket
import gevent.server
import nose.tools

from gservice import util

def test_does_connect():
    class SimpleServer(gevent.server.StreamServer):
        def handle(self, socket, address):
            socket.sendall("hello and goodbye!")
            socket.shutdown(0)

    server = SimpleServer(('127.0.0.1', 0))
    server.start()
    client = util.connect_and_retry(('127.0.0.1', server.server_port))
    lines = [line for line in util.line_protocol(client)]
    assert len(lines) == 1, "Didn't receive the line"
    server.stop()

@nose.tools.raises(IOError)
def test_max_retries():
    client = util.connect_and_retry(('127.0.0.1', 16666), max_retries=2, delay=0.1, max_delay=0.5)

def test_eventual_connect():
    class SimpleServer(gevent.server.StreamServer):
        def handle(self, socket, address):
            socket.sendall("hello and goodbye!")
            socket.shutdown(0)

    server = SimpleServer(('127.0.0.1', 16667))
    gevent.spawn_later(0.5, server.start)
    client = util.connect_and_retry(('127.0.0.1', 16667), max_delay=1)
    lines = [line for line in util.line_protocol(client)]
    assert len(lines) == 1, "Didn't receive the line"
    server.stop()