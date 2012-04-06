try:
    from .config import Config as _Config
except ImportError:
    # Avoid dependencies when
    # running setup.py
    class _Config:
        setting = None

from .core import Service

__author__ = "Jeff Lindsay <jeff.lindsay@twilio.com>"
__license__ = "MIT"
__version__ = ".".join(map(str, (0, 5, 0)))

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
