"""Ginkgo module

This toplevel module exposes most of the API you would use making Ginkgo
applications. Rarely would you need to import from other modules, unless you're
doing tests or something more advanced. This is a simple example of the common
case building Ginkgo services::

    from ginkgo import Service
    from ginkgo import Setting

    class HelloWorld(Service):
        message = Setting("message", default="Hello world")

        def do_start(self):
            self.spawn(self.message_forever)

        def message_forever(self):
            while True:
                print self.message
                self.async.sleep(1)

"""
from .core import Service
from .config import Config

__author__ = "Jeff Lindsay <jeff.lindsay@twilio.com>"
__license__ = "MIT"
__version__ = ".".join(map(str, (0, 5, 0)))

__all__ = ["Service", "Setting", "process", "settings"]

process = None
settings = Config()
Setting = settings.setting

_processes = []
def push_process(new_process):
    """Internal function to set the process singleton"""
    _processes.append(process)
    process = new_process
    settings = process.config
    Setting = settings.setting

def pop_process():
    """Internal function to unset the process singleton"""
    if len(_processes):
        process = _processes.pop()
        settings = process.config
        Setting = settings.setting
