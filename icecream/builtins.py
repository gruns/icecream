# -*- coding: utf-8 -*-

#
# IceCream - A little library for sweet and creamy print debugging.
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
    setattr(builtins, ic, icecream.ic)


def uninstall(ic='ic'):
    delattr(builtins, ic)
