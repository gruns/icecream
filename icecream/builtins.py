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

from .icecream import ic


try:
    builtins = __import__('__builtin__')
except ImportError:
    builtins = __import__('builtins')


def install(ic_name='ic'):
    setattr(builtins, ic_name, ic)


def uninstall(ic_name='ic'):
    delattr(builtins, ic_name)
