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

import sys
import unittest
from os.path import basename
try:  # Python 2.x.
    from StringIO import StringIO
except ImportError:  # Python 3.x.
    from io import StringIO
from contextlib import contextmanager

from icecream import ic, PREFIX

MYFILENAME = basename(__file__)


def noop(*args, **kwargs):
    return


@contextmanager
def captureStdout():
    newStdout = StringIO()
    realStdout = sys.stdout
    try:
        sys.stdout = newStdout
        yield newStdout
    finally:
        sys.stdout = realStdout


def pairIsNoArgumentsOutput(pair):
    return pair[0] == MYFILENAME and int(pair[1]) > 0


def parseOutputIntoPairs(out, assertNumLines):
    out = out.getvalue()

    lines = out.splitlines()
    for line in lines:
        assert line.startswith(PREFIX)
    if assertNumLines:
        assert len(lines) == assertNumLines

    linePairs = []
    prefixStripped = [line[len(PREFIX):] for line in lines]
    for line in prefixStripped:
        pairStrs = line.split(', ')
        split = [s.split(':', 1) for s in pairStrs]
        pairs = [(arg.strip(), val.strip()) for arg, val in split]
        linePairs.append(pairs)

    return linePairs


class TestIceCream(unittest.TestCase):
    def testWithoutArgs(self):
        with captureStdout() as out:
            ic()
        pairs = parseOutputIntoPairs(out, 1)[0]
        assert pairIsNoArgumentsOutput(pairs[0])

    def testAsArgument(self):
        with captureStdout() as out:
            noop(ic(1), ic(2))
        pairs = parseOutputIntoPairs(out, 2)
        assert pairs[0][0] == ('1', '1') and pairs[1][0] == ('2', '2')

        with captureStdout() as out:
            d = {1: ic(1)}
            l = [ic(2), ic()]
        pairs = parseOutputIntoPairs(out, 3)
        assert pairs[0][0] == ('1', '1')
        assert pairs[1][0] == ('2', '2')
        assert pairIsNoArgumentsOutput(pairs[2][0])

    def testSingleArgument(self):
        with captureStdout() as out:
            ic(1)
        assert parseOutputIntoPairs(out, 1)[0][0] == ('1', '1')

    def testMultipleArguments(self):
        with captureStdout() as out:
            ic(1, 2)
        pairs = parseOutputIntoPairs(out, 1)[0]
        assert pairs == [('1', '1'), ('2', '2')]

    def testNestedMultiline(self):
        with captureStdout() as out:
            ic(
                )
        assert pairIsNoArgumentsOutput(parseOutputIntoPairs(out, 1)[0][0])

        with captureStdout() as out:
            ic(1,
               'foo')
        pairs = parseOutputIntoPairs(out, 1)[0]
        assert pairs == [('1', '1'), ("'foo'", "'foo'")]

        with captureStdout() as out:
            noop(noop(noop({1: ic(
                noop())})))
        assert parseOutputIntoPairs(out, 1)[0][0] == ('noop()', 'None')

    def testExpressionArguments(self):
        class klass():
            attr = 'yep'
        d = {'d': {1: 'one'}, 'k': klass}

        with captureStdout() as out:
            ic(d['d'][1])
        assert parseOutputIntoPairs(out, 1)[0][0] == ("d['d'][1]", "'one'")

        with captureStdout() as out:
            ic(d['k'].attr)
        assert parseOutputIntoPairs(out, 1)[0][0] == ("d['k'].attr", "'yep'")

    def testMultipleCallsOnSameLine(self):
        with captureStdout() as out:
            ic(1); ic(2, 3)
        pairs = parseOutputIntoPairs(out, 2)
        assert pairs[0][0] == ('1', '1')
        assert pairs[1] == [('2', '2'), ('3', '3')]

    def testCallSurroundedByExpressions(self):
        with captureStdout() as out:
            noop(); ic(1); noop()
        assert parseOutputIntoPairs(out, 1)[0][0] == ('1', '1')

    def testComments(self):
        with captureStdout() as out:
            """Comment."""; ic(); # Comment.
        assert pairIsNoArgumentsOutput(parseOutputIntoPairs(out, 1)[0][0])

    def testMethodArguments(self):
        class Foo:
            def foo(self):
                return 'foo'
        f = Foo()
        with captureStdout() as out:
            ic(f.foo())
        assert parseOutputIntoPairs(out, 1)[0][0] == ('f.foo()', "'foo'")

    def testComplicated(self):
        with captureStdout() as out:
            noop(); ic(); noop(); ic(1,
                                     2, noop.__class__.__name__,
                                         noop ()); noop()
        pairs = parseOutputIntoPairs(out, 2)
        assert pairIsNoArgumentsOutput(pairs[0][0])
        assert pairs[1] == [
            ('1', '1'), ('2', '2'), ('noop.__class__.__name__', "'function'"),
            ('noop ()', 'None')]

    def testReturnValue(self):
        with captureStdout() as out:
            assert ic() is None
            assert ic(1) == 1
            assert ic(1, 2, 3) == (1, 2, 3)
