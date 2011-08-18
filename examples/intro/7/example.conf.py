#===
# 7. Running and configuring daemon with serviced

# example.conf.py

pidfile = 'example.pid'
logfile = 'example.log'

def service():
    from example import MyApplication
    return MyApplication()

# $ gservice -C example.conf.py run
# $ gservice -C example.conf.py start
# $ gservice -C example.conf.py restart
# $ gservice -C example.conf.py stop
# $ gservice -C example.conf.py --logfile example2.log start
# $ gservice -C example.conf.py stop
# $ gservice --help
