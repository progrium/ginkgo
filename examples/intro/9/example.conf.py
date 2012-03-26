#===
# 9. Sane application configuration

# example.conf.py

pidfile = 'example.pid'
logfile = 'example.log'
http_port = 8080
tcp_port = 1234
connect_address = ('127.0.0.1', 1234)

def service():
    from example import MyApplication
    return MyApplication()

# $ ginkgo -C example.conf.py -X 'http_port = 7070'
