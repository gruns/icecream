#!/usr/bin/env python
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

import os
import sys
from os.path import dirname, join as pjoin
from glob import glob
from setuptools import Command, setup
from setuptools.command.test import test as TestCommand

this_dir = dirname(__file__)

class Publish(Command):
    """Publish to PyPI with twine."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        dist_dir = pjoin(this_dir, "dist")
        os.system(sys.executable + " -m build -nwxs " + this_dir)
        files = glob(pjoin(dist_dir, "*.whl")) + glob(pjoin(dist_dir, "*.tar.gz"))
        rc = os.system(sys.executable + " -m twine upload " + " ".join(files))

        sys.exit(rc)


class RunTests(TestCommand):
    """
    Run the unit tests.

    By default, `python setup.py test` fails if tests/ isn't a Python
    module (that is, if the tests/ directory doesn't contain an
    __init__.py file). But the tests/ directory shouldn't contain an
    __init__.py file and tests/ shouldn't be a Python module. See

      http://doc.pytest.org/en/latest/goodpractices.html

    Running the unit tests manually here enables `python setup.py test`
    without tests/ being a Python module.
    """
    def run_tests(self):
        from unittest import TestLoader, TextTestRunner
        tests_dir = pjoin(this_dir, 'tests')
        suite = TestLoader().discover(tests_dir)
        result = TextTestRunner().run(suite)
        sys.exit(0 if result.wasSuccessful() else -1)


setup(
    cmdclass={
        'test': RunTests,
        'publish': Publish,
    },
)
