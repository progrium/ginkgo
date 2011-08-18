#===
# 6. Consolidate into an application service

import gevent
from gevent.pywsgi import WSGIServer
from gevent.server import StreamServer
from gevent.socket import create_connection

from gevent_tools.service import Service

class TcpClient(Service):
    def __init__(self, address, handler):
        self.address = address
        self.handler = handler
        
    def do_start(self):
        self.spawn(self.handler, self.address)

class MyApplication(Service):
    def __init__(self):
        self.add_service(WSGIServer(('127.0.0.1', 8080), self.handle_http))
        self.add_service(StreamServer(('127.0.0.1', 1234), self.handle_tcp))
        self.add_service(TcpClient(('127.0.0.1', 1234), self.client_connect))
    
    def client_connect(self, address):
        sockfile = create_connection(address).makefile()
        while True:
            line = sockfile.readline() # returns None on EOF
            if line is not None:
                print "<<<", line,
            else:
                break
    
    def handle_tcp(self, socket, address):
        print 'new tcp connection!'
        while True:
            socket.send('hello\n')
            gevent.sleep(1)

    def handle_http(self, env, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        print 'new http request!'
        return ["hello world"]

app = MyApplication()
app.serve_forever()
