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