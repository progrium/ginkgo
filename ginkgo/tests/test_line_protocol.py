import gevent.socket
import gevent.server

from ginkgo import util

def test_one_liner():
    one_line = 'hello and goodbye!'
    class SimpleServer(gevent.server.StreamServer):
        def handle(self, socket, address):
            socket.sendall(one_line)
            socket.shutdown(0)
    
    server = SimpleServer(('127.0.0.1', 0))
    server.start()
    client = gevent.socket.create_connection(('127.0.0.1', server.server_port))
    lines = [line for line in util.line_protocol(client)]
    assert len(lines) == 1, "Got too many (or not enough) lines"
    assert lines[0] == one_line, "Didn't get the line expected"
    server.stop()

def test_multi_lines():
    one_line = 'hello and goodbye!'
    number_lines = 5
    class SimpleServer(gevent.server.StreamServer):
        def handle(self, socket, address):
            socket.sendall('\n'.join([one_line for n in xrange(number_lines)]))
            socket.shutdown(0)
    
    server = SimpleServer(('127.0.0.1', 0))
    server.start()
    client = gevent.socket.create_connection(('127.0.0.1', server.server_port))
    lines = [line for line in util.line_protocol(client)]
    assert len(lines) == number_lines, "Got too many (or not enough) lines"
    assert lines.pop() == one_line, "Didn't get the line expected"
    server.stop()

def test_multi_lines_rn():
    one_line = 'hello and goodbye!'
    number_lines = 5
    class SimpleServer(gevent.server.StreamServer):
        def handle(self, socket, address):
            socket.sendall('\r\n'.join([one_line for n in xrange(number_lines)]))
            socket.shutdown(0)
    
    server = SimpleServer(('127.0.0.1', 0))
    server.start()
    client = gevent.socket.create_connection(('127.0.0.1', server.server_port))
    lines = [line for line in util.line_protocol(client)]
    assert len(lines) == number_lines, "Got too many (or not enough) lines"
    assert lines.pop() == one_line, "Didn't get the line expected"
    server.stop()

def test_strip_on_lines():
    one_line = 'hello and goodbye!\n'
    number_lines = 5
    class SimpleServer(gevent.server.StreamServer):
        def handle(self, socket, address):
            socket.sendall(''.join([one_line for n in xrange(number_lines)]))
            socket.shutdown(0)
    
    server = SimpleServer(('127.0.0.1', 0))
    server.start()
    client = gevent.socket.create_connection(('127.0.0.1', server.server_port))
    lines = [line for line in util.line_protocol(client)]
    assert len(lines) == number_lines, "Got too many (or not enough) lines"
    assert lines.pop() != one_line, "Line includes newlines (or something)"
    assert lines.pop() == one_line.strip(), "Line doesn't match when stripped"
    server.stop()

def test_no_strip_on_lines():
    one_line = 'hello and goodbye!\n'
    number_lines = 5
    class SimpleServer(gevent.server.StreamServer):
        def handle(self, socket, address):
            socket.sendall(''.join([one_line for n in xrange(number_lines)]))
            socket.sendall('\n')
            socket.shutdown(0)
    
    server = SimpleServer(('127.0.0.1', 0))
    server.start()
    client = gevent.socket.create_connection(('127.0.0.1', server.server_port))
    lines = [line for line in util.line_protocol(client, strip=False)]
    assert len(lines) == number_lines+1, "Got too many (or not enough) lines"
    assert lines.pop() == '\n', "Didn't get empty line"
    assert lines.pop() == one_line, "Line doesn't match line with newline"
    server.stop()
