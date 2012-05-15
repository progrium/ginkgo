"""Ginkgo logger

This module provides the class for a logger object used by the runner module's
`Process` object to manage, configure, and provide services around Python's
standard logging module. Most notably it allows you to easily configure the
Python logger using Ginkgo configuration.

"""
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
        Log level to use. Valid options: debug, info, warning, critical
        Ignored if logconfig is set.
        """)
    config = ginkgo.Setting("logconfig", default=None, help="""
        Configuration of standard Python logger. Can be dict for basicConfig,
        dict with version key for dictConfig, or ini filepath for fileConfig.
        """)

    def __init__(self, process):
        self.process = process

        if self.logfile is None:
            process.config.set("logfile", os.path.expanduser(
                               "~/.{}.log".format(process.service_name)))

        self.load_config()

    def load_config(self):
        if self.config is None:
            self._load_default_config()
        else:
            if isinstance(self.config, str) and os.path.exists(self.config):
                logging.config.fileConfig(self.config)
            elif 'version' in self.config:
                logging.config.dictConfig(self.config)
            else:
                self._reset_basic_config(self.config)

    def _load_default_config(self):
        default_config = dict(
            format=DEFAULT_FORMAT,
            level=getattr(logging, self.loglevel.upper()))
        if hasattr(self.process, 'pidfile'):
            default_config['filename'] = self.logfile
        self._reset_basic_config(default_config)

    def _reset_basic_config(self, config):
        for h in logging.root.handlers[:]:
            logging.root.removeHandler(h)
        logging.basicConfig(**config)

    def capture_stdio(self):
        # TODO: something smarter than this?
        try:
            os.dup2(logging._handlerList[0]().stream.fileno(), sys.stdout.fileno())
            os.dup2(logging._handlerList[0]().stream.fileno(), sys.stderr.fileno())
        except:
            pass

    @property
    def file_descriptors(self):
        return [handler.stream.fileno() for handler in [wr() for wr in
            logging._handlerList] if isinstance(handler, logging.FileHandler)]

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
