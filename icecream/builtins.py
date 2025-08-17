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


def install(ic: str='ic') -> None:
    setattr(builtins, ic, icecream.ic)


def uninstall(ic: str='ic') -> None:
    delattr(builtins, ic)
