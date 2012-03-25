import argparse
import sys
import runpy
import os.path

import ginkgo

def load_class(class_path):
    module_name, class_name = class_path.rsplit('.', 1)
    module = runpy.run_module(module_name)
    return module[class_name]

def parse_target(target):
    if os.path.exists(target):
        ginkgo.setttings.load_file(target)
        config_filepath = target
        app_path = ginkgo.settings.get("service")
    else:
        config_filepath = None
        app_path = target
    return app_path, config_filepath

def run_ginkgo():
    parser = argparse.ArgumentParser(prog="ginkgo")
    parser.add_argument("-v", "--version",
        action="version", version="%(prog)s {}".format(ginkgo.__version__))
    parser.add_argument("target", help="""
        service class path to run (modulename.ServiceClass) or
        configuration file path to use (/path/to/config.py)
        """.strip())
    args = parser.parse_args()
    print parse_target(args.target)


def run_ginkgoctl():
    pass
