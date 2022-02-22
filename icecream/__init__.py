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
from .__version__ import __version__
from .builtins import install, uninstall

meta = {"__version__": __version__}
