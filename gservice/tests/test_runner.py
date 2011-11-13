import gevent
import nose.tools

from gservice.tests import silencer
from gservice.tests import mock_open

@nose.tools.raises(SystemExit)
def test_runner_action_required():
    from gservice.runner import Runner
    Runner._args = []
    with silencer():
        Runner()

@nose.tools.raises(SystemExit)
def test_runner_config_required():
    from gservice.runner import Runner
    Runner._args = ['start']
    with silencer():
        Runner()

def test_runner_reads_config():
    from gservice.runner import Runner
    Runner._args = ['start', '-C', 'config']
    Runner._opener = mock_open({"config": "", "serviced.log": ""})
    with silencer():
        Runner()

@nose.tools.raises(SystemExit)
def test_runner_no_daemonize():
    from gservice.runner import Runner
    class EmptyRunner(Runner):
        def run(self): pass
    EmptyRunner._args = ['start', '-C', 'config', '-n']
    EmptyRunner._opener = mock_open({"config": "", "serviced.log": "", "serviced.pid": ""})
    with silencer():
        EmptyRunner()


def test_read_config_option():
    from gservice.runner import Runner
    from gservice.config import Option

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
    from gservice.runner import Runner

    class ConfigCheckRunner(Runner):
        def run(self):
            assert self.pidfile_path == 'mypidfile.pid'

    ConfigCheckRunner._args = ['run', '-C', 'config', '-p', 'mypidfile.pid']
    ConfigCheckRunner._opener = mock_open({"config": "pidfile = 'configpidfile.pid'"})

    with silencer():
        ConfigCheckRunner().do_action()


def test_extend_file_config_option():
    from gservice.runner import Runner
    from gservice.config import Option

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
    from gservice.runner import Runner
    from gservice.config import Option

    class ConfigCheckRunner(Runner):
        foo = Option('foo')
        def run(self):
            assert self.foo == 'bar2'

    ConfigCheckRunner._args = ['run', '-C', 'config1', '-X', "foo = 'bar2'"]
    ConfigCheckRunner._opener = mock_open({"config1": "foo = 'bar1'"})

    with silencer():
        ConfigCheckRunner().do_action()


def test_privileged_configuration():
    from gservice.runner import Runner
    from gservice import config

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
        import gservice.core
        class Service(gservice.core.Service):
            def do_start(self):
                print "asked to do_start"
                uids['start'] = os.getuid()

                def stop(): self.stop()
                gevent.spawn_later(0.1, stop)
            
            def do_stop(self):
                print "asked to do_stop"
                uids['stop'] = os.getuid()
                print "done stopping"

        return Service()

    config.load({'service': service,
                 '_allow_early_gevent_import_for_tests': True})

    print "before action"
    runner.do_action()
    
    assert uids['start'] != runner.uid
    assert uids['stop'] == runner.uid


def test_service_generator():
    
    import gservice.core
    class MyService(gservice.core.Service): pass

    expected_children = [('hi', MyService()), ('also named', MyService())]
    expected_main = MyService()

    def service():
        for name, child in expected_children:
            yield name, child
        yield expected_main
        
    from gservice.runner import Runner
    
    Runner._args = ['run', '-C', 'config', '-u', 'nobody']
    Runner._opener = mock_open({"config": ""})

    runner = Runner()
    
    service_gen = service()
        
    children, main_service = runner._expand_service_generators(service_gen)

    print children, main_service
    assert children == expected_children
    assert main_service == expected_main

def get_runner():
    from gservice.runner import Runner
    
    Runner._args = ['run', '-C', 'config', '-u', 'nobody']
    Runner._opener = mock_open({"config": ""})

    runner = Runner()
    return runner

def test_invalid_names_throw():
    import gservice.core
    from gservice.runner import RunnerStartException
    class MyService(gservice.core.Service): pass

    def service():
        try:
            print "about to yield"
            yield 1, MyService()
            assert False, "non-string names should throw"
        except RunnerStartException:
            print "non string threw"
        yield MyService() #main service

    runner = get_runner()
    children, main_service = runner._expand_service_generators(service())    

def test_invalid_name_empty_throw():
    import gservice.core
    from gservice.runner import RunnerStartException
    class MyService(gservice.core.Service): pass

    def service():
        try:
            yield '', MyService()
            assert False, "empty string names should throw"
        except RunnerStartException:
            print "empty string threw"
        yield MyService #main service

    runner = get_runner()
    children, main_service = runner._expand_service_generators(service())

def test_invalid_tuple_length_throws():
    import gservice.core
    from gservice.runner import RunnerStartException
    class MyService(gservice.core.Service): pass
 
    def service():
        try:
            yield 'string', MyService(), 'bad value'
            assert False, "three-tuple should throw"
        except RunnerStartException:
            pass
        yield MyService() #main service
        
    runner = get_runner()
    children, main_service = runner._expand_service_generators(service())

def test_setting_main_before_named_throws():
    import gservice.core
    from gservice.runner import RunnerStartException
    class MyService(gservice.core.Service): pass

    def service():
        yield MyService() #set mainservice

        try:
            yield 'string', MyService()
            assert False, "sending named services after main service should throw"
        except RunnerStartException:
            pass

    runner = get_runner()
    children, main_service = runner._expand_service_generators(service())

def test_named_global_services():
    from gservice import config
    from collections import defaultdict
    expected = defaultdict(list)
    lookup = {}


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

    def service():
        import gservice.core
        class MainService(gservice.core.Service):
            def __init__(self, name):
                self.name = name
                
            def do_start(self):
                print "main service starting"
                gevent.spawn_later(0.1, self.stop)
                lookup['named'] = gservice.core.Service('named')
                lookup['named2'] = gservice.core.Service('named2')
                lookup['foo'] = gservice.core.Service('foo')
                expected[self.name].append('start')
            
            def do_stop(self):
                print "asked to do_stop"
                expected[self.name].append('stop')

        class GS(gservice.core.Service):

            def __init__(self, name):
                self.name = name
                
            def do_start(self):
                print self.name, "starting"
                expected[self.name].append('start')

            def do_stop(self):
                print self.name, "stopping"
                expected[self.name].append('stop')

        yield 'named', GS('named')
        yield 'named2', GS('named2')

        yield MainService('main')


    runner = get_runner()

    config.load({'service': service,
                 '_allow_early_gevent_import_for_tests': True})

    print 'do action'
    runner.do_action()

    print 'after action'
    print expected
    print lookup
    for name in 'named', 'named2':
        assert lookup[name].name == name
        assert expected[name] == ['start', 'stop']

    assert expected['main'] == ['start', 'stop']

    assert lookup['foo'] is None
