#!/usr/bin/env python3
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
from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand


meta = {}
with open(pjoin('icecream', '__version__.py')) as f:
    exec(f.read(), meta)


class Publish(Command):
    """Publish to PyPI with twine."""
    user_options = []

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        os.system('python3 setup.py sdist bdist_wheel')

        sdist = 'dist/icecream-%s.tar.gz' % meta['__version__']
        wheel = 'dist/icecream-%s-py3-none-any.whl' % meta['__version__']
        rc = os.system('twine upload "%s" "%s"' % (sdist, wheel))

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
    def run_tests(self) -> None:
        from unittest import TestLoader, TextTestRunner
        tests_dir = pjoin(dirname(__file__), 'tests')
        suite = TestLoader().discover(tests_dir)
        result = TextTestRunner().run(suite)
        sys.exit(0 if result.wasSuccessful() else -1)

setup(
    cmdclass={
        'test': RunTests,
        'publish': Publish,
    },
)
