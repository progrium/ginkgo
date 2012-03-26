import argparse
import sys
import runpy
import os.path
import signal
import logging

import ginkgo
from ginkgo.service import Container, Service

def load_class(class_path):
    if '.' not in class_path:
        raise RuntimeError("Invalid class path")
    module_name, class_name = class_path.rsplit('.', 1)
    try:
        module = runpy.run_module(module_name)
        return module[class_name]
    except (ImportError, KeyError):
        raise RuntimeError("Unable to find class path")

def prepare_app(target):
    if os.path.exists(target):
        config = ginkgo.settings.load_file(target)
        try:
            service = config['service']
        except KeyError:
            raise RuntimeError("Configuration does not specify a service")
    else:
        service = target
    if isinstance(service, str):
        service = load_class(service)()
    elif callable(service):
        # Class or factory
        service = service()
    else:
        raise RuntimeError("Does not appear to be a valid service")
    return Process(service)

def run_ginkgo():
    parser = argparse.ArgumentParser(prog="ginkgo", add_help=False)
    parser.add_argument("-v", "--version",
        action="version", version="%(prog)s {}".format(ginkgo.__version__))
    parser.add_argument("-h", "--help", action="store_true", help="""
        show program's help text and exit
        """.strip())
    parser.add_argument("target", nargs='?', help="""
        service class path to run (modulename.ServiceClass) or
        configuration file path to use (/path/to/config.py)
        """.strip())
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        if args.target:
            print # blank line
            app = prepare_app(args.target)
            app.config.print_help()
    else:
        if args.target:
            app = prepare_app(args.target)
            app.serve_forever()
        else:
            parser.print_usage()

def run_ginkgoctl():
    pass

class Process(Container):
    daemonize = ginkgo.Setting("daemonize", default=False)
    pidfile = ginkgo.Setting("pidfile", default="/tmp/ginkgo.pid")
    user = ginkgo.Setting("user", default=None)
    group = ginkgo.Setting("group", default=None)
    umask = ginkgo.Setting("umask", default=None)

    def __init__(self, app_service, config=None):
        self.config = config or ginkgo.settings
        self.app = app_service
        self.add_service(self.app)

        ginkgo.process = ginkgo.process or self

    def do_start(self):
        import gevent
        # TODO: upgrade to gevent 1.0 and use standard signal
        gevent.signal(signal.SIGHUP, self.reload)
        gevent.signal(signal.SIGTERM, self.stop)

    def do_stop(self):

    def __enter__(self):
        ginkgo._push_process(self)
        return self

    def __exit__(self, type, value, traceback):
        ginkgo._pop_process()
