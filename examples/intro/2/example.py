#===
# 2. Basic gevent TCP server and WSGI server

import gevent
from gevent.pywsgi import WSGIServer
from gevent.server import StreamServer

def handle_http(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    print 'new http request!'
    return ["hello world"]

def handle_tcp(socket, address):
    print 'new tcp connection!'
    while True:
        socket.send('hello\n')
        gevent.sleep(1)

tcp_server = StreamServer(('127.0.0.1', 1234), handle_tcp)
tcp_server.start()

http_server = WSGIServer(('127.0.0.1', 8080), handle_http)
http_server.serve_forever()