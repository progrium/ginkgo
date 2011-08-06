from flask import Flask
app = Flask(__name__)
port = 8888

@app.route("/")
def hello():
    return "Hello World!"

def service():
    from gevent.wsgi import WSGIServer
    from gevent_tools.util import ServiceWrapper
    return ServiceWrapper(WSGIServer, ('', port), app)    