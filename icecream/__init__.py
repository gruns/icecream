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

from os.path import dirname, join as pjoin

from .icecream import *  # noqa
from .builtins import install, uninstall

# Import all variables in __version__.py without explicit imports.
meta = {}
with open(pjoin(dirname(__file__), '__version__.py')) as f:
    exec(f.read(), meta)
globals().update(dict((k, v) for k, v in meta.items() if k not in globals()))
