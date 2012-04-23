import logging
import logging.config
import os
import os.path
import sys

import ginkgo

DEFAULT_FORMAT = "%(asctime)s %(levelname) 7s %(module)s: %(message)s"

class Logger(object):
    logfile = ginkgo.Setting("logfile", default=None, help="""
        Path to primary log file. Ignored if logconfig is set.
        """)
    loglevel = ginkgo.Setting("loglevel", default='debug', help="""
        Log level to use. Options: debug, info, warning, critical
        Ignored if logconfig is set.
        """)
    config = ginkgo.Setting("logconfig", default=None, help="""
        Configuration of standard Python logger. Can be dict for basicConfig,
        dict with version key for dictConfig, or filepath for fileConfig.
        """)

    def __init__(self, process):
        if self.logfile is None:
            process.config.set("logfile",
                    "/tmp/{}.log".format(process.service_name))

        if self.config is None:
            default_config = dict(
                format=DEFAULT_FORMAT,
                level=getattr(logging, self.loglevel.upper()))
            if process.daemon:
                default_config['filename'] = self.logfile
            logging.basicConfig(**default_config)
        else:
            if isinstance(self.config, str) and os.path.exists(self.config):
                logging.config.fileConfig(self.config)
            elif 'version' in self.config:
                logging.config.dictConfig(self.config)
            else:
                logging.basicConfig(**self.config)

    def capture_stdio(self):
        # TODO: something smarter than this?
        os.dup2(logging._handlerList[0]().stream.fileno(), sys.stdout.fileno())
        os.dup2(logging._handlerList[0]().stream.fileno(), sys.stderr.fileno())

    def reopen_logs(self):
        for wr in logging._handlerList:
            handler = wr() # _handlerList items are weak references
            if isinstance(handler, logging.FileHandler):
                handler.acquire()
                try:
                    if handler.stream:
                        handler.stream.close()
                        handler.stream = handler._open()
                finally:
                    handler.release()

    def shutdown(self):
        logging.shutdown()

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
