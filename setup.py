#!/usr/bin/env python
import os
from setuptools import Command
from setuptools import setup

def shell(cmdline):
    args = cmdline.split(' ')
    os.execlp(args[0], *args)

class GToolsCommand(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

class TestCommand(GToolsCommand):
    description = "run tests with nose"
    
    def run(self):
        shell("nosetests")

class CoverageCommand(GToolsCommand):
    description = "run test coverage report with nose"
    
    def run(self):
        shell("nosetests --with-coverage --cover-package=gevent_tools")

setup(
    name='gevent_tools',
    version='0.1.0',
    author='Jeff Lindsay',
    author_email='jeff.lindsay@twilio.com',
    description='gevent related goodies',
    packages=['gevent_tools'],
    install_requires=['gevent', 'setproctitle', 'nose', 'python-daemon'],
    data_files=[],
    entry_points={
        'console_scripts': [
            'serviced = gevent_tools.runner:main',]},
    cmdclass={
        'test': TestCommand,
        'coverage': CoverageCommand,}
)
