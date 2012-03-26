#===
# 7. Running and configuring daemon with serviced

# example.conf.py

pidfile = 'example.pid'
logfile = 'example.log'

def service():
    from example import MyApplication
    return MyApplication()

# $ ginkgo -C example.conf.py run
# $ ginkgo -C example.conf.py start
# $ ginkgo -C example.conf.py restart
# $ ginkgo -C example.conf.py stop
# $ ginkgo -C example.conf.py --logfile example2.log start
# $ ginkgo -C example.conf.py stop
# $ ginkgo --help
