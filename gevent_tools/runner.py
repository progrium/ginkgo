import io
import optparse
import os.path
import sys
import time
import signal
import logging.config
import pwd

import setproctitle
import daemon
import daemon.daemon
import daemon.runner

from gevent_tools import config

def main():
    """Entry point for serviced console script"""
    Runner().do_action()

def runner_options():
    parser = optparse.OptionParser()
    parser.add_option("-C", "--config", dest="config", metavar="<file>",
                    help="Path to Python script to configure and return service to run")
    parser.add_option("-X", "--extend", dest="extensions", metavar="<file/python>", action="append",
                    help="Python code or script path to extend over the config script", default = [])
    parser.add_option("-l", "--logfile", dest="logfile", metavar="<logfile>", default="serviced.log",
                    help="Log to a specified file, - for stdout (default: serviced.log)")
    parser.add_option("-p", "--pidfile", dest="pidfile", metavar="<pidfile>", default="serviced.pid",
                    help="Save pid in specified file (default: serviced.pid)")
    parser.add_option("-c", "--chroot", dest="chroot", metavar="<chroot>",
                    help="Chroot to a directory before running (default: don't chroot)")
    #parser.add_option("-d", "--rundir", dest="rundir", metavar="<directory>",
    #                help="Change to a directory before running, but after any chroot (default: .)")
    parser.add_option("-u", "--user", dest="user", metavar="<user>",
                    help="The user to run as. (default: don't change)")
    #parser.add_option("-g", "--group", dest="group", metavar="<group>",
    #                help="The group to run as. (default: don't change)")
    parser.add_option("-N", "--name", dest="name", metavar="<name>",
                    help="Name of the process using setprocname. (default: don't change)")
    #parser.add_option("-m", "--umask", dest="umask", metavar="<mask>",
    #                help="The (octal) file creation mask to apply. (default: 0077 if daemonized)")
    return parser

class Runner(daemon.runner.DaemonRunner):
    _args = sys.argv[1:]
    _opener = io.open
    
    logfile_path =      config.Option('logfile')
    pidfile_path =      config.Option('pidfile')
    proc_name =         config.Option('name')
    service_factory =   config.Option('service')
    chroot_path =       config.Option('chroot') 
    user =              config.Option('user')
    log_config =        config.Option('log_config')
    
    def __init__(self):
        self.action_funcs = {
            'start': '_start',
            'stop': '_stop',
            'restart': '_restart',
            'run': '_run',
            'reload': '_reload', }

        self.service = None
        self.app = self
        
        self.parse_args(self.load_config(runner_options()))
        self.daemon_context = daemon.DaemonContext()
        self.daemon_context.stdin = self._open(self.stdin_path, 'r')
        self.daemon_context.stdout = self._open(
            self.stdout_path, 'a+', buffering=1)
        self.daemon_context.stderr = self._open(
            self.stderr_path, 'a+', buffering=1)

        self.pidfile = None
        if self.pidfile_abspath:
            pidfilepath = self.pidfile_abspath
            # workaround for bug in python-daemon that can not correctly
            # determine where the pid file is located when the chroot option
            # is specified
            if self.chroot_abspath:
                pidfilepath = os.path.join(self.chroot_abspath,
                                           self.pidfile_abspath[1:])
            self.pidfile = daemon.runner.make_pidlockfile(pidfilepath,
                self.pidfile_timeout)
        self.daemon_context.pidfile = self.pidfile
        self.daemon_context.chroot_directory = self.chroot_abspath
    
    def load_config(self, parser):
        options, args = parser.parse_args(self._args)
        self.config_path = options.config
        
        def load_file(filename):
            f = self._open(filename, 'r')
            d = {'__file__': filename}
            exec f.read() in d,d
            return d

        if options.config:
            parser.set_defaults(**load_file(options.config))
        elif len(args) == 0 or args[0] in ['start', 'restart', 'run']:
            parser.error("a configuration file is required to start")

        for ex in options.extensions:
            try:
                parser.set_defaults(**load_file(ex))
            except IOError:
                # couldn't open the file try to interpret as python
                d = {}
                exec ex in d,d
                parser.set_defaults(**d)

        # Now we parse args again with the config file settings as defaults
        options, args = parser.parse_args(self._args)
        config.load(options.__dict__)
        return args
    
    def parse_args(self, args):
        try:
            self.action = args[0]
        except IndexError:
            self.action = 'run'
        
        self.stdin_path = '/dev/null'
        self.stdout_path = self.logfile_path
        self.stderr_path = self.logfile_path
        
        def abspath(f):
            return os.path.abspath(f) if f is not None else None

        self.pidfile_abspath = abspath(self.pidfile_path)
        self.pidfile_timeout = 3
        
        self.config_abspath = abspath(self.config_path)
        self.chroot_abspath = abspath(self.chroot_path)

        if self.action not in self.action_funcs:
            self._usage_exit(args)

        # convert user name into uid/gid pair
        self.uid = self.gid = None
        if self.user is not None:
            pw_record = pwd.getpwnam(self.user)
            self.uid = pw_record.pw_uid
            self.gid = pw_record.pw_gid
    
    def _log_config(self):
        if self.log_config:
            logging.config.dictConfig(self.log_config)
            
    def do_reload(self):
        self._log_config()
        self.service.reload()

    def run(self):
        # gevent complains if you import it before you daemonize
        import gevent
        gevent.signal(signal.SIGUSR1, self.do_reload)
        gevent.signal(signal.SIGTERM, self.terminate)

        if self._get_action_func() == '_run':
            # to make debugging easier, we're including the directory where
            # the configuration file lives as well as the current working
            # directory in the module search path
            sys.path.append(os.path.dirname(self.config_path))
            sys.path.append(os.getcwd())

        self._log_config()

        if self.proc_name:
            setproctitle.setproctitle(self.proc_name)

        self.service = self.service_factory()

        if hasattr(self.service, 'catch'):
            self.service.catch(SystemExit, lambda e,g: self.service.stop())

        def shed_privileges():
            if self.uid and self.gid:
                daemon.daemon.change_process_owner(self.uid, self.gid)
            
        self.service.serve_forever(ready_callback = shed_privileges)
    
    def terminate(self):
        # XXX: multiple SIGTERM signals should forcibly quit the process
        self.service.stop()

    def _reload(self):
        os.kill(int(self.pidfile.read_pid()), signal.SIGUSR1)

    def _start(self):
        # workaround for bug in python-daemon that can not correctly
        # determine where the pid file is located when the chroot option
        # is specified
        if self.pidfile_abspath:
            self.pidfile = daemon.runner.make_pidlockfile(
                self.pidfile_abspath, self.pidfile_timeout)
            self.daemon_context.pidfile = self.pidfile
        super(Runner, self)._start()

    def _run(self):
        print "Starting service..."
        self.run()
    
    def do_action(self):
        func = self._get_action_func()
        getattr(self, func)()

    def _open(self, *args, **kwargs):
        return self.__class__.__dict__['_opener'](*args, **kwargs)
