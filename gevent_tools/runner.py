import optparse
import os.path
import sys
import time

import setproctitle
import daemon
import daemon.runner


class Runner(daemon.runner.DaemonRunner):
    _args = sys.argv[1:]
    _opener = open
    
    def __init__(self):
        parser = optparse.OptionParser()
        parser.add_option("-n", "--nodaemon", dest="daemonize", default=True, action="store_false",
                        help="Don't daemonize (stay in foreground)")
        parser.add_option("-C", "--config", dest="config", metavar="<file>",
                        help="Path to Python script to configure and return service to run")
        parser.add_option("-X", "--extend", dest="extensions", metavar="<file/python>", action="append",
                        help="Python code or script path to extend over the config script")
        parser.add_option("-l", "--logfile", dest="logfile", metavar="<logfile>", default="serviced.log",
                        help="Log to a specified file, - for stdout (default: serviced.log)")
        parser.add_option("-p", "--pidfile", dest="pidfile", metavar="<pidfile>", default="serviced.pid",
                        help="Save pid in specified file (default: serviced.pid)")
        parser.add_option("-c", "--chroot", dest="chroot", metavar="<chroot>",
                        help="Chroot to a directory before running (default: don't chroot)")
        parser.add_option("-d", "--rundir", dest="rundir", metavar="<directory>",
                        help="Change to a directory before running, but after any chroot (default: .)")
        parser.add_option("-u", "--user", dest="user", metavar="<user>",
                        help="The user to run as. (default: don't change)")
        parser.add_option("-g", "--group", dest="group", metavar="<group>",
                        help="The group to run as. (default: don't change)")
        parser.add_option("-N", "--name", dest="name", metavar="<name>",
                        help="Name of the process using setprocname. (default: don't change)")
        parser.add_option("-m", "--umask", dest="umask", metavar="<mask>",
                        help="The (octal) file creation mask to apply. (default: 0077 if daemonized)")
        self.parser = parser
        self.service = None
        
        self.parse_args()
        self.app = self
        self.daemon_context = daemon.DaemonContext()
        self.daemon_context.stdin = self._open(self.stdin_path, 'r')
        self.daemon_context.stdout = self._open(self.stdout_path, 'w+')
        self.daemon_context.stderr = self._open(
            self.stderr_path, 'w+', buffering=0)

        self.pidfile = None
        if self.pidfile_path is not None:
            self.pidfile = daemon.runner.make_pidlockfile(
                self.pidfile_path, self.pidfile_timeout)
        self.daemon_context.pidfile = self.pidfile
    
    def load_config(self):
        options, args = self.parser.parse_args(self._args)
        if options.config:
            config_file = self._open(options.config, 'r')
            d = {'__file__': options.config}
            exec config_file.read() in d, d
            self.parser.set_defaults(**d)
        elif len(args) == 0 or args[0] in ['start', 'restart']:
            self.parser.error("a configuration file is required to start")
    
    def parse_args(self):
        self.load_config()
        options, args = self.parser.parse_args(self._args)
        self.options = options
        if not options.daemonize:
            self.run()
            sys.exit(0)
        
        self.stdin_path = '/dev/null'
        self.stdout_path = options.logfile
        self.stderr_path = options.logfile
        
        self.pidfile_path = os.path.abspath(options.pidfile)
        self.pidfile_timeout = 3
        self.action = args[0]
        if self.action not in self.action_funcs:
            self._usage_exit(args)
    
    def run(self):
        if self.options.name:
            setproctitle.setproctitle(self.options.name)
        self.service = self.options.service()
        self.service.catch(SystemExit, lambda e,g: self.service.stop())
        self.service.serve_forever()

    def _open(self, *args, **kwargs):
        return self.__class__.__dict__['_opener'](*args, **kwargs)