# -*- coding: utf-8 -*-

#
# IceCream - Never use print() to debug again
#
# Ansgar Grunseid
# grunseid.com
# grunseid@gmail.com
#
# License: MIT
#

# Import all variables in __version__.py without explicit imports.
from . import __version__
from .builtins import install, uninstall
from .icecream import *  # noqa

globals().update(dict((k, v) for k, v in __version__.__dict__.items()))

# Public API - these functions are imported to make them available at module level
__all__ = ['ic', 'install', 'uninstall']
