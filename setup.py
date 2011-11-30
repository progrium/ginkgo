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

class BuildPagesCommand(GToolsCommand):
    description = "rebuild the website"
    
    def run(self):
        os.execlp("bash", "bash", "-c", """branch=$(git status | grep 'On branch' | cut -f 4 -d ' ')
            git checkout gh-pages && 
            git commit --allow-empty -m 'trigger pages rebuild' && 
            git push origin gh-pages && 
            git checkout $branch""")

class CoverageCommand(GToolsCommand):
    description = "run test coverage report with nose"
    
    def run(self):
        shell("nosetests --with-coverage --cover-package=gservice")

setup(
    name='gservice',
    version='0.3.0',
    author='Jeff Lindsay',
    author_email='jeff.lindsay@twilio.com',
    description='gevent related goodies',
    packages=find_packages(),
    install_requires=['gevent==0.13.3', 'setproctitle', 'nose', 'python-daemon',],
    data_files=[],
    entry_points={
        'console_scripts': [
            'gservice = gservice.runner:main',]},
    cmdclass={
        'test': TestCommand,
        'coverage': CoverageCommand,
        'build_pages': BuildPagesCommand,}
)
