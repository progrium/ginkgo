"""Ginkgo runner

The runner module is responsible for creating a "container" to run services in,
and tools to manage that container. The container is itself a service based on
a class called `Process`, which is intended to model the running process that
contains the service. The process service takes an application service to run,
associates a configuration with this "container", and then initializes the
process to daemonize. This `Process` object is then assigned as a toplevel
singleton, which you can use as a reference to the top of the service tree.

The `ControlInterface` class models the commands you can use to start or
control a daemonized service. This is exposed via two command line utilities
`ginkgo` and `ginkgoctl`, both of which have their entry points defined in this
module.

The runner module and Ginkgo command line utilities are completely optional.
You can always just write your own Python script or console command that takes
your application service and calls `serve_forever()` on it.

"""
import argparse
import logging
import pwd
import grp
import os
import os.path
import runpy
import signal
import sys

import ginkgo.core
import ginkgo.logger
import ginkgo.util

STOP_SIGNAL = signal.SIGTERM
RELOAD_SIGNAL = signal.SIGHUP

sys.path.insert(0, os.getcwd())

logger = logging.getLogger(__name__)

def run_ginkgo():
    parser = argparse.ArgumentParser(prog="ginkgo", add_help=False)
    parser.add_argument("-v", "--version",
        action="version", version="%(prog)s {}".format(ginkgo.__version__))
    parser.add_argument("-h", "--help", action="store_true", help="""
        show program's help text and exit
        """.strip())
    parser.add_argument("-d", "--daemonize", action="store_true", help="""
        daemonize the service process
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
            try:
                app = setup_process(args.target)
                app.config.print_help()
            except RuntimeError, e:
                parser.error(e)
    else:
        if args.target:
            try:
                ControlInterface().start(args.target, args.daemonize)
            except RuntimeError, e:
                parser.error(e)
        else:
            parser.print_usage()

def run_ginkgoctl():
    parser = argparse.ArgumentParser(prog="ginkgoctl")
    parser.add_argument("-v", "--version",
        action="version", version="%(prog)s {}".format(ginkgo.__version__))
    parser.add_argument("-p", "--pid", help="""
        pid or pidfile to use instead of target
        """.strip())
    parser.add_argument("target", nargs='?', help="""
        service class path to use (modulename.ServiceClass) or
        configuration file path to use (/path/to/config.py)
        """.strip())
    parser.add_argument("action",
        choices="start stop restart reload status log logtail".split())
    args = parser.parse_args()
    if args.pid and args.target:
        parser.error("You cannot specify both a target and a pid")
    try:
        if args.action in "start restart log logtail".split():
            if not args.target:
                parser.error("You need to specify a target for {}".format(args.action))
            getattr(ControlInterface(), args.action)(args.target)
        else:
            getattr(ControlInterface(), args.action)(resolve_pid(args.pid, args.target))
    except RuntimeError, e:
        parser.error(e)

def resolve_pid(pid=None, target=None):
    if pid and not os.path.exists(pid):
        return int(pid)
    if target is not None:
        setup_process(target, daemonize=True)
        pid = ginkgo.settings.get("pidfile")
    if pid is not None:
        if os.path.exists(pid):
            with open(pid, "r") as f:
                pid = f.read().strip()
            return int(pid)
        else:
            return
    raise RuntimeError("Unable to resolve pid from {}".format(pid or target))

def load_class(class_path):
    if '.' not in class_path:
        raise RuntimeError("Invalid class path")
    module_name, class_name = class_path.rsplit('.', 1)
    try:
        try:
            module = runpy.run_module(module_name)
        except ImportError:
            module = runpy.run_module(module_name + ".__init__")
    except ImportError, e:
        import traceback, pkgutil
        tb_tups = traceback.extract_tb(sys.exc_info()[2])
        if pkgutil.__file__.startswith(tb_tups[-1][0]):
            # If the bottommost frame in our stack was in pkgutil,
            # then we can safely say that this ImportError occurred
            # because the top level class path was not found.
            raise RuntimeError("Unable to load class path: {}:\n{}".format(
                class_path, e))
        else:
            # If the ImportError occurred further down,
            # raise original exception.
            raise
    try:
        return module[class_name]
    except KeyError, e:
        raise RuntimeError("Unable to find class in module: {}".format(
            class_path))

def resolve_target(target):
    if target.endswith('.py'):
        if os.path.exists(target):
            config = ginkgo.settings.load_file(target)
            try:
                return config['service']
            except KeyError:
                raise RuntimeError(
                    "Configuration does not specify a service factory")
        else:
            raise RuntimeError(
                'Configuration file %s does not exist' % target)
    else:
        return target

def setup_process(target, daemonize=True):
    service_factory = resolve_target(target)
    if isinstance(service_factory, str):
        service_factory = load_class(service_factory)

    if callable(service_factory):
        if daemonize:
            return DaemonProcess(service_factory)
        else:
            return Process(service_factory)
    else:
        raise RuntimeError("Does not appear to be a valid service factory")

class ControlInterface(object):
    def start(self, target, daemonize=True):
        print "Starting process with {}...".format(target)
        app = setup_process(target, daemonize)
        try:
            app.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            app.stop()

    def restart(self, target):
        self.stop(resolve_pid(target=target))
        self.start(target)

    def stop(self, pid):
        if self._validate(pid):
            print "Stopping process {}...".format(pid)
            os.kill(pid, STOP_SIGNAL)

    def reload(self, pid):
        if self._validate(pid):
            print "Reloading process {}...".format(pid)
            os.kill(pid, RELOAD_SIGNAL)

    def status(self, pid):
        if self._validate(pid):
            print "Process is running as {}.".format(pid)

    def _validate(self, pid):
        try:
            os.kill(pid, 0)
            return pid
        except (OSError, TypeError):
            print "Process is NOT running."

    def log(self, target):
        app = setup_process(target)
        app.logger.print_log()

    def logtail(self, target):
        try:
            app = setup_process(target)
            app.logger.tail_log()
        except KeyboardInterrupt:
            pass

class Process(ginkgo.core.Service, ginkgo.util.GlobalContext):
    singleton_attr = (ginkgo, 'process')
    start_before = True

    rundir = ginkgo.Setting("rundir", default=None, help="""
        Change to a directory before running
        """)
    user = ginkgo.Setting("user", default=None, help="""
        Change to a different user before running
        """)
    group = ginkgo.Setting("group", default=None, help="""
        Change to a different group before running
        """)
    umask = ginkgo.Setting("umask", default=None, help="""
        Change file mode creation mask before running
        """)

    def __init__(self, app_factory, config=None):
        self.app_factory = app_factory
        self.app = None

        self.config = config or ginkgo.settings
        self.logger = ginkgo.logger.Logger(self)

        self.pid = os.getpid()
        self.uid = os.geteuid()
        self.gid = os.getegid()
        self.environ = os.environ

        ginkgo.process = ginkgo.process or self

    @property
    def service_name(self):
        if self.app is None:
            # if the factory callable is called "service"
            # we need something better to name it, so we try
            # using first word of docstring if available
            if self.app_factory.__name__ == 'service':
                name = self.app_factory.__doc__ or self.app_factory.__name__
                return name.split(' ', 1)[0]
            else:
                return self.app_factory.__name__
        else:
            return self.app.service_name

    def do_start(self):
        if self.umask is not None:
            os.umask(self.umask)

        if self.rundir is not None:
            os.chdir(self.rundir)

        self.app = self.app_factory()
        self.add_service(self.app)

        self.async.init()
        self.async.signal(RELOAD_SIGNAL, self.reload)
        self.async.signal(STOP_SIGNAL, self.stop)

    def post_start(self):
        if self.group is not None:
            grp_record = grp.getgrnam(self.group)
            self.gid = grp_record.gr_gid
            os.setgid(self.gid)

        if self.user is not None:
            pw_record = pwd.getpwnam(self.user)
            self.uid = pw_record.pw_uid
            self.gid = pw_record.pw_gid
            os.setgid(self.gid)
            os.setuid(self.uid)

    def do_stop(self):
        logger.info("Stopping.")
        self.logger.shutdown()

    def do_reload(self):
        try:
            self.config.reload_file()
            self.logger.load_config()
        except RuntimeError, e:
            logger.warn(e)

    def trigger_hook(self, name, *args, **kwargs):
        """ Experimental """
        hook = self.config.get(name)
        if hook is not None and callable(hook):
            try:
                hook(*args, **kwargs)
            except Exception, e:
                raise RuntimeError("Hook Error: {}".format(e))

    def __enter__(self):
        self.__class__._push_context(self)
        Config._push_context(self.config)
        return self

    def __exit__(self, type, value, traceback):
        Config._pop_context()
        self.__class__._pop_context()


class DaemonProcess(Process):
    pidfile = ginkgo.Setting("pidfile", default=None, help="""
        Path to pidfile to use when daemonizing
        """)

    def __init__(self, app_factory, config=None):
        super(DaemonProcess, self).__init__(app_factory, config)

        if self.pidfile is None:
            self.config.set("pidfile", os.path.expanduser(
                            "~/.{}.pid".format(self.service_name)))
        self.pidfile = ginkgo.util.Pidfile(str(self.pidfile))


    def do_start(self):
        ginkgo.util.prevent_core_dump()
        ginkgo.util.daemonize(
            preserve_fds=self.logger.file_descriptors)
        self.logger.capture_stdio()
        self.pid = os.getpid()
        self.pidfile.create(self.pid)
        super(DaemonProcess, self).do_start()

    def do_stop(self):
        super(DaemonProcess, self).do_stop()
        self.pidfile.unlink()

