import os

import ginkgo

class Logger(object):
    logfile = ginkgo.Setting("logfile", default=None, help="""
        Path to primary logfile
        """.strip())

    def __init__(self, process):
        if self.logfile is None:
            process.config.set("logfile",
                    "/tmp/{}.log".format(process.app.service_name))

        #self.file = open(self.logfile, "w", buffering=0)

    def open(self):
        self.file = open(self.logfile, "w", buffering=0)

    def redirect(self, input):
        os.dup2(self.file.fileno(), input.fileno())

    def close(self):
        self.file.close()

    def print_log(self):
        with open(self.logfile, "r") as f:
            print f.read()

    def tail_log(self):
        with open(self.logfile, "r") as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print line.strip()
            while True:
                line = f.readline()
                if line:
                    print line.strip()
