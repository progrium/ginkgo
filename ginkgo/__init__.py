version_info = (0, 5, 0)
__version__ = ".".join(map(str, version_info))

from .config import _default_config

process = None
settings = _default_config
