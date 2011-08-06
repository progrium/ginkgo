import io
import optparse
import os.path
import sys
import time

import setproctitle
import daemon
import daemon.runner

from gevent_tools import config

def main():
    """Entry point for serviced console script"""
    Runner().do_action()

def runner_options():
    parser = optparse.OptionParser()
    parser.add_option("-C", "--config", dest="config", metavar="<file>",
                    help="Path to Python script to configure and return service to run")
    #parser.add_option("-X", "--extend", dest="extensions", metavar="<file/python>", action="append",
    #                help="Python code or script path to extend over the config script")
    parser.add_option("-l", "--logfile", dest="logfile", metavar="<logfile>", default="serviced.log",
                    help="Log to a specified file, - for stdout (default: serviced.log)")
    parser.add_option("-p", "--pidfile", dest="pidfile", metavar="<pidfile>", default="serviced.pid",
                    help="Save pid in specified file (default: serviced.pid)")
    #parser.add_option("-c", "--chroot", dest="chroot", metavar="<chroot>",
    #                help="Chroot to a directory before running (default: don't chroot)")
    #parser.add_option("-d", "--rundir", dest="rundir", metavar="<directory>",
    #                help="Change to a directory before running, but after any chroot (default: .)")
    #parser.add_option("-u", "--user", dest="user", metavar="<user>",
    #                help="The user to run as. (default: don't change)")
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
    
    logfile_path = config.Option('logfile')
    pidfile_path = config.Option('pidfile')
    proc_name = config.Option('name')
    
    service_factory = config.Option('service')
    
    def __init__(self):
        self.action_funcs = {
            'start': '_start',
            'stop': '_stop',
            'restart': '_restart',
            'run': '_run', }
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
        if self.pidfile_abspath is not None:
            self.pidfile = daemon.runner.make_pidlockfile(
                self.pidfile_abspath, self.pidfile_timeout)
        self.daemon_context.pidfile = self.pidfile
    
    def load_config(self, parser):
        options, args = parser.parse_args(self._args)
        if options.config:
            config_file = self._open(options.config, 'r')
            d = {'__file__': options.config}
            exec config_file.read() in d, d
            parser.set_defaults(**d)
        elif len(args) == 0 or args[0] in ['start', 'restart', 'run']:
            parser.error("a configuration file is required to start")
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
        
        self.pidfile_abspath = os.path.abspath(self.pidfile_path)
        self.pidfile_timeout = 3
        
        if self.action not in self.action_funcs:
            self._usage_exit(args)
    
    def run(self):
        if self.proc_name:
            setproctitle.setproctitle(self.proc_name)
        self.service = self.service_factory()
        if hasattr(self.service, 'catch'):
            self.service.catch(SystemExit, lambda e,g: self.service.stop())
        self.service.serve_forever()
    
    def _run(self):
        print "Starting service..."
        self.run()
    
    def do_action(self):
        func = self._get_action_func()
        getattr(self, func)()

    def _open(self, *args, **kwargs):
        return self.__class__.__dict__['_opener'](*args, **kwargs)