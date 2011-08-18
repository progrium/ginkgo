#===
# 4. Organizing with greenlets

import gevent
from gevent.pywsgi import WSGIServer
from gevent.server import StreamServer
from gevent.socket import create_connection

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
    sockfile = create_connection(address).makefile()
    while True:
        line = sockfile.readline() # returns None on EOF
        if line is not None:
            print "<<<", line,
        else:
            break

tcp_server = StreamServer(('127.0.0.1', 1234), handle_tcp)
http_server = WSGIServer(('127.0.0.1', 8080), handle_http)
greenlets = [
    gevent.spawn(tcp_server.serve_forever),
    gevent.spawn(http_server.serve_forever),
    gevent.spawn(client_connect, ('127.0.0.1', 1234)),
]
gevent.joinall(greenlets)


#===
# Now you need gevent-tools, or write your own:
# * Organization with Services
# * Daemonizing (easy, right?)
# * Daemon options/infrastructure (chroot, privs, pidfile, logfile)
# * Daemon/"service" management (start, stop, restart, reload?)
# * Configuration
#===