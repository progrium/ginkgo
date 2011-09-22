#!/usr/bin/env python
import os
from setuptools import Command
from setuptools import setup, find_packages

def shell(cmdline):
    args = cmdline.split(' ')
    os.execlp(args[0], *args)

class GToolsCommand(Command):
    def initialize_options(self): pass
    def finalize_options(self): pass
    user_options = []

class TestCommand(GToolsCommand):
    description = "run tests with nose"
    
    def run(self):
        shell("nosetests")

class CoverageCommand(GToolsCommand):
    description = "run test coverage report with nose"
    
    def run(self):
        shell("nosetests --with-coverage --cover-package=gevent_tools")

setup(
    name='gservice',
    version='0.2.0',
    author='Jeff Lindsay',
    author_email='jeff.lindsay@twilio.com',
    description='gevent related goodies',
    packages=find_packages(),
    install_requires=['gevent==0.13.3', 'setproctitle', 'nose', 'python-daemon',],
    data_files=[],
    entry_points={
        'console_scripts': [
            'gservice = gevent_tools.runner:main',]},
    cmdclass={
        'test': TestCommand,
        'coverage': CoverageCommand,}
)
