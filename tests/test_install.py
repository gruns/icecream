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

import unittest

import icecream
from .test_icecream import (
    disableColoring, captureStandardStreams, parseOutputIntoPairs)

from .install_test_import import runMe


class TestIceCreamInstall(unittest.TestCase):
    def testInstall(self):
        icecream.install()
        with disableColoring(), captureStandardStreams() as (out, err):
            runMe()
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('x', '3')
        icecream.uninstall()  # Clean up builtins.

    def testUninstall(self):
        try:
            icecream.uninstall()
        except AttributeError:  # Already uninstalled.
            pass

        # NameError: global name 'ic' is not defined.
        with self.assertRaises(NameError):
            runMe()
