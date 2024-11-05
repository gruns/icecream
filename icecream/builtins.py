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

import icecream


try:
    builtins = __import__('__builtin__')
except ImportError:
    builtins = __import__('builtins')


def install(ic='ic'):
    # type: (str) -> None
    setattr(builtins, ic, icecream.ic)


def uninstall(ic='ic'):
    # type: (str) -> None
    delattr(builtins, ic)
