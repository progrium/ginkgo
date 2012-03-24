import signal

import ginkgo
from ginkgo.service import Container
from ginkgo.config import Setting
from ginkgo.config import _default_config

class Process(Container):
    daemonize = Setting("daemonize", default=False)
    pidfile = Setting("pidfile", default="/tmp/ginkgo.pid")
    user = Setting("user", default=None)
    group = Setting("group", default=None)
    umask = Setting("umask", default=None)

    def __init__(self, app_service, _config=None):
        self.config = _config or _default_config
        self.app = app_service
        self.add_service(self.app)

        ginkgo.process = ginkgo.process or self

    def do_start(self):
        signal.signal(signal.SIGHUP, self.reload)
        signal.signal(signal.SIGTERM, self.stop)

    def __enter__(self):
        self._last_process = ginkgo.process
        self._last_settings = ginkgo.settings
        ginkgo.process = self
        ginkgo.settings = self.config
        return self

    def __exit__(self, type, value, traceback):
        ginkgo.process = self._last_process
        ginkgo.settings = self._last_settings
        self._last_settings = None
        self._last_process = None
