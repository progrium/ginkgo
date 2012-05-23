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
    data_files=[],
    entry_points={
        'console_scripts': [
            'ginkgo = ginkgo.runner:run_ginkgo',
            'ginkgoctl = ginkgo.runner:run_ginkgoctl']},
)
