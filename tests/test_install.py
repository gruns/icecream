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
from tests.test_icecream import (
    disable_coloring, capture_standard_streams, parse_output_into_pairs)

from tests.install_test_import import runMe


class TestIceCreamInstall(unittest.TestCase):
    def test_install(self):
        icecream.install()
        with disable_coloring(), capture_standard_streams() as (out, err):
            runMe()
        assert parse_output_into_pairs(out, err, 1)[0][0] == ('x', '3')
        icecream.uninstall()  # Clean up builtins.

    def test_uninstall(self):
        try:
            icecream.uninstall()
        except AttributeError:  # Already uninstalled.
            pass

        # NameError: global name 'ic' is not defined.
        with self.assertRaises(NameError):
            runMe()
