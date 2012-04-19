#===
# 5. Wrap client in a service, create parent service

import gevent
from gevent.pywsgi import WSGIServer
from gevent.server import StreamServer
from gevent.socket import create_connection

from ginkgo import Service
from ginkgo.async.gevent import ServerWrapper

class TcpClient(Service):
    def __init__(self, address, handler):
        self.address = address
        self.handler = handler
        
    def do_start(self):
        self.spawn(self.handler, self.address)

def handle_http(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    print 'new http request!'
    return ["hello world"]

def handle_tcp(socket, address):
    print 'new tcp connection!'
    while True:
        socket.send('hello\n')
        gevent.sleep(1)

def client_connect(address):
    gevent.sleep(1)
    sockfile = create_connection(address).makefile()
    while True:
        line = sockfile.readline() # returns None on EOF
        if line is not None:
            print "<<<", line,
        else:
            break

app = Service()
app.add_service(ServerWrapper(StreamServer(('127.0.0.1', 1234), handle_tcp)))
app.add_service(ServerWrapper(WSGIServer(('127.0.0.1', 8080), handle_http)))
app.add_service(TcpClient(('127.0.0.1', 1234), client_connect))
app.serve_forever()

