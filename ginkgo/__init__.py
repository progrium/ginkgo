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
import sys

from .config import Config

process = None
settings = Config()
Setting = lambda *args, **kwargs: settings.setting(*args, **kwargs)

# Set the singleton location for Config global context
Config.singleton_attr = (sys.modules[__name__], 'settings')

from .core import Service

__all__ = ["Service", "Setting", "process", "settings"]
__author__ = "Jeff Lindsay <jeff.lindsay@twilio.com>"
__license__ = "MIT"
__version__ = ".".join(map(str, (0, 6, 0)))
