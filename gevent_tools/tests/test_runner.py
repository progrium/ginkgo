import gevent
import nose.tools

from gevent_tools.tests import silencer
from gevent_tools.tests import mock_open

@nose.tools.raises(SystemExit)
def test_runner_action_required():
    from gevent_tools.runner import Runner
    Runner._args = []
    with silencer():
        Runner()

@nose.tools.raises(SystemExit)
def test_runner_config_required():
    from gevent_tools.runner import Runner
    Runner._args = ['start']
    with silencer():
        Runner()

def test_runner_reads_config():
    from gevent_tools.runner import Runner
    Runner._args = ['start', '-C', 'config']
    Runner._opener = mock_open({"config": "", "serviced.log": ""})
    with silencer():
        Runner()

@nose.tools.raises(SystemExit)
def test_runner_no_daemonize():
    from gevent_tools.runner import Runner
    class EmptyRunner(Runner):
        def run(self): pass
    EmptyRunner._args = ['start', '-C', 'config', '-n']
    EmptyRunner._opener = mock_open({"config": "", "serviced.log": "", "serviced.pid": ""})
    with silencer():
        EmptyRunner()


def test_read_config_option():
    from gevent_tools.runner import Runner
    from gevent_tools.config import Option

    class ConfigCheckRunner(Runner):
        foo = Option('foo')
        def run(self):
            assert self.foo == 'bar'

    ConfigCheckRunner._args = ['run', '-C', 'config']
    ConfigCheckRunner._opener = mock_open({"config": "foo = 'bar'"})

    with silencer():
        ConfigCheckRunner().do_action()

def test_command_line_override_config():
    """ Test that specifying an option on the command line override any
        value set in a config file"""
    from gevent_tools.runner import Runner

    class ConfigCheckRunner(Runner):
        def run(self):
            assert self.pidfile_path == 'mypidfile.pid'

    ConfigCheckRunner._args = ['run', '-C', 'config', '-p', 'mypidfile.pid']
    ConfigCheckRunner._opener = mock_open({"config": "pidfile = 'configpidfile.pid'"})

    with silencer():
        ConfigCheckRunner().do_action()


def test_extend_file_config_option():
    from gevent_tools.runner import Runner
    from gevent_tools.config import Option

    class ConfigCheckRunner(Runner):
        foo = Option('foo')
        def run(self):
            assert self.foo == 'bar2'

    ConfigCheckRunner._args = ['run', '-C', 'config1', '-X', 'config2']
    ConfigCheckRunner._opener = mock_open({"config1": "foo = 'bar1'", 
                                           "config2": "foo = 'bar2'"})

    with silencer():
        ConfigCheckRunner().do_action()

def test_extend_file_config_option():
    from gevent_tools.runner import Runner
    from gevent_tools.config import Option

    class ConfigCheckRunner(Runner):
        foo = Option('foo')
        def run(self):
            assert self.foo == 'bar2'

    ConfigCheckRunner._args = ['run', '-C', 'config1', '-X', "foo = 'bar2'"]
    ConfigCheckRunner._opener = mock_open({"config1": "foo = 'bar1'"})

    with silencer():
        ConfigCheckRunner().do_action()

