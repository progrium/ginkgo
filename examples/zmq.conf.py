name = "zmqservice demo"

def service():
    from gevent_tools.toys.pubsub import PubSubService
    return PubSubService()