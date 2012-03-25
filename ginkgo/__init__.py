version_info = (0, 5, 0)
__version__ = ".".join(map(str, version_info))

from .config import Config
from .service import Service

process = None
settings = Config()
Setting = settings.setting

_processes = []
def _push_process(new_process):
    _processes.append(process)
    process = new_process
    settings = process.config
    Setting = settings.setting

def _pop_process():
    if len(_processes):
        process = _processes.pop()
        settings = process.config
        Setting = settings.setting
