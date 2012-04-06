import argparse
import os
import os.path
import runpy
import signal
import sys

import ginkgo.core
import ginkgo.util

STOP_SIGNAL = signal.SIGTERM
RELOAD_SIGNAL = signal.SIGHUP

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
            try:
                app = prepare_app(args.target)
                app.config.print_help()
            except RuntimeError, e:
                parser.error(e)
    else:
        if args.target:
            try:
                ControlInterface().start(args.target)
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
        choices=["start", "stop", "restart", "reload", "status"])
    args = parser.parse_args()
    if args.pid and args.target:
        parser.error("You cannot specify both a target and a pid")
    ginkgo.settings.set("daemon", True)
    try:
        if args.action in ["start", "restart"]:
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
        prepare_app(target)
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
        return module[class_name]
    except (ImportError, KeyError), e:
        raise RuntimeError("Unable to load class path: {}:\n{}".format(
            class_path, e))

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

class ControlInterface(object):
    def start(self, target):
        print "Starting process with {}...".format(target)
        app = prepare_app(target)
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

class Process(ginkgo.core.Service):
    start_before = True

    daemon = ginkgo.Setting("daemon", default=False, help="""
        True or False whether to daemonize
        """.strip())
    pidfile = ginkgo.Setting("pidfile", default=None, help="""
        Path to pidfile to use when daemonizing
        """.strip())
    rundir = ginkgo.Setting("rundir", default=None, help="""
        Change to a directory before running
        """.strip())
    user = ginkgo.Setting("user", default=None, help="""
        Change to a different user before running
        """.strip())
    group = ginkgo.Setting("group", default=None, help="""
        Change to a different group before running
        """.strip())
    umask = ginkgo.Setting("umask", default=None, help="""
        Change file mode creation mask before running
        """.strip())

    def __init__(self, app_service, config=None):
        self.config = config or ginkgo.settings
        self.app = app_service
        self.add_service(self.app)

        if self.daemon:
            if self.pidfile is None:
                self.config.set("pidfile",
                        "/tmp/{}.pid".format(self.app.service_name))
            self.pidfile = ginkgo.util.Pidfile(str(self.pidfile))
        else:
            self.pidfile = None

        self.pid = os.getpid()
        self.uid = os.geteuid()
        self.gid = os.getegid()
        self.environ = os.environ

        ginkgo.process = ginkgo.process or self

    def do_start(self):
        ginkgo.util.prevent_core_dump()

        if self.umask is not None:
            os.umask(self.umask)

        if self.rundir is not None:
            os.chdir(self.rundir)

        if self.user is not None:
            pw_record = pwd.getpwnam(self.user)
            self.uid = pw_record.pw_uid
            self.gid = pw_record.pw_gid
            os.setuid(self.uid)
            os.setgid(self.gid)

        if self.group is not None:
            grp_record = grp.getgrnam(self.group)
            self.gid = grp_record.gr_gid
            os.setgid(gid)

        if self.daemon:
            ginkgo.util.daemonize()
            self.pid = os.getpid()
            self.pidfile.create(self.pid)

            # TODO: placeholder for logs
            f = open("/tmp/test.log", "w", buffering=0)
            os.dup2(f.fileno(), sys.stderr.fileno())
            os.dup2(f.fileno(), sys.stdout.fileno())

        # TODO: move this to async manager?
        import gevent
        gevent.core.reinit()

        # TODO: upgrade to gevent 1.0 and use standard signal
        gevent.signal(RELOAD_SIGNAL, self.reload)
        gevent.signal(STOP_SIGNAL, self.stop)

        # TODO: use all those settings

    def do_stop(self):
        print "Stopping."
        if self.daemon:
            self.pidfile.unlink()

    def do_reload(self):
        self.config.reload_file()

    def trigger_hook(self, name, *args, **kwargs):
        hook = self.config.get(name)
        if hook is not None and callable(hook):
            try:
                hook(*args, **kwargs)
            except Exception, e:
                raise RuntimeError("Hook Error: {}".format(e))

    def __enter__(self):
        ginkgo.push_process(self)
        return self

    def __exit__(self, type, value, traceback):
        ginkgo.pop_process()
