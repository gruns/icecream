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
from install_test_import import (
    runMeCustom,
    runMeDefault,
)
from test_icecream import (
    captureStandardStreams,
    disableColoring,
    parseOutputIntoPairs,
)


class TestIceCreamInstall(unittest.TestCase):

    def testInstallDefault(self):
        icecream.install()
        with disableColoring(), captureStandardStreams() as (out, err):
            runMeDefault()

        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('x', '3')
        icecream.uninstall()  # Clean up builtins.

    def testUninstallDefault(self):
        try:
            icecream.uninstall()
        except AttributeError:  # Already uninstalled.
            pass

        # NameError: global name 'ic' is not defined.
        with self.assertRaises(NameError):
            runMeDefault()

    def testInstallCustom(self):
        # Create new instance of IceCream and install it.
        ik = icecream.IceCreamDebugger()
        ik.configureOutput(includeContext=False, prefix='')
        icecream.install(attribute='ik', value=ik)

        with disableColoring(icecream_instance=ik), captureStandardStreams() as (out, err):
            runMeCustom()

        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('x', '4')
        icecream.uninstall(attribute='ik')  # Clean up builtins.

    def testUninstallCustom(self):
        try:
            icecream.uninstall('ik')
        except AttributeError:  # Already uninstalled.
            pass

        # NameError: global name 'ik' is not defined.
        with self.assertRaises(NameError):
            runMeCustom()
