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


def install(attribute='ic', value=icecream.ic):
    setattr(builtins, attribute, value)


def uninstall(attribute='ic'):
    delattr(builtins, attribute)
