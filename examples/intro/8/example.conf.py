#===
# 8. Using configuration file for app configuration


def service():
    pidfile = 'example.pid'
    logfile = 'example.log'
    http_port = 8080
    tcp_port = 1234
    connect_address = ('127.0.0.1', 1234)

    from example import MyApplication
    return MyApplication(locals())
