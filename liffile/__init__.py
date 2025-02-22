# liffile/__init__.py

from .liffile import *
from .liffile import __all__, __doc__, __version__

# constants are repeated for documentation

__version__ = __version__
"""Liffile version string."""


def _set_module() -> None:
    """Set __module__ attribute for all public objects."""
    globs = globals()
    module = globs['__name__']
    for item in __all__:
        obj = globs[item]
        if hasattr(obj, '__module__'):
            obj.__module__ = module


_set_module()
