#!/usr/bin/env python
import os
from setuptools import setup, find_packages

from ginkgo import __version__

setup(
    name='Ginkgo',
    version=__version__+"dev",
    author='Jeff Lindsay',
    author_email='jeff.lindsay@twilio.com',
    description='Lightweight service framework',
    packages=find_packages(),
    setup_requires=['nose'],
    tests_require=['nose'],
    test_suite='nose.collector',
    data_files=[],
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    entry_points={
        'console_scripts': [
            'ginkgo = ginkgo.runner:run_ginkgo',
            'ginkgoctl = ginkgo.runner:run_ginkgoctl']},
)
