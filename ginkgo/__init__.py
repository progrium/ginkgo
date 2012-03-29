version_info = (0, 5, 0)
__version__ = ".".join(map(str, version_info))

from .config import Config as _Config
from .core import Service

process = None
settings = _Config()
Setting = settings.setting

_processes = []
def push_process(new_process):
    """Internal function to set the process singleton"""
    _processes.append(process)
    process = new_process
    settings = process.config
    Setting = settings.setting

def pop_process():
    """Internal function to unset the process singleton"""
    if len(_processes):
        process = _processes.pop()
        settings = process.config
        Setting = settings.setting
