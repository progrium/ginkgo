#!/usr/bin/env python

from setuptools import setup

setup(
    name='gevent_tools',
    version='0.1',
    author='Jeff Lindsay',
    author_email='jeff.lindsay@twilio.com',
    description='gevent related goodies',
    packages=['gevent_tools'],
    scripts=['scripts/serviced'],
    install_requires=['gevent', 'setproctitle'],
    data_files=[]
)
