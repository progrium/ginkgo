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


def test_privileged_configuration():
    from gevent_tools.runner import Runner
    from gevent_tools import config

    uids = {}

    Runner._args = ['run', '-C', 'config', '-u', 'nobody']
    Runner._opener = mock_open({"config": ""})

    runner = Runner()

    # mock out the os getuid/setuid modules
    import os
    props = {'uid': 0, 'gid': 0}
    def getuid(): return props['uid']
    def setuid(uid): props['uid'] = uid
    def getgid(): return props['gid']
    def setgid(gid): props['gid'] = gid

    os.getuid = getuid
    os.setuid = setuid
    os.getgid = getgid
    os.setgid = setgid

    # capture the uid of the service at start and stop time
    def service():
        import gevent_tools.service
        class Service(gevent_tools.service.Service):
            def do_start(self):
                uids['start'] = os.getuid()

                def stop(): self.stop()
                gevent.spawn_later(0.1, stop)
            
            def do_stop(self):
                uids['stop'] = os.getuid()

        return Service()

    config.load({'service': service})

    with silencer():
        runner.do_action()
    
    assert uids['start'] != runner.uid
    assert uids['stop'] == runner.uid
