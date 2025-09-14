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

from typing import Optional
import icecream

builtins = __import__('builtins')


def install(
    ic: str = 'ic',
    configured_ic: Optional[icecream.IceCreamDebugger] = None
) -> None:
    if configured_ic is None:
        configured_ic = icecream.ic
    setattr(builtins, ic, configured_ic)


def uninstall(ic: str = 'ic') -> None:
    delattr(builtins, ic)
