#===
# 1. Basic gevent TCP server

import gevent
from gevent.server import StreamServer

def handle_tcp(socket, address):
    print 'new tcp connection!'
    while True:
        socket.send('hello\n')
        gevent.sleep(1)

tcp_server = StreamServer(('127.0.0.1', 1234), handle_tcp)
tcp_server.serve_forever()