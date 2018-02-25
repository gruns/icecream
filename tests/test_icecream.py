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
try:  # Python 2.x.
    from StringIO import StringIO
except ImportError:  # Python 3.x.
    from io import StringIO
from contextlib import contextmanager
from os.path import basename, splitext

import icecream
from icecream import ic

MYFILENAME = basename(__file__)


def noop(*args, **kwargs):
    return


@contextmanager
def configureIcecreamOutput(prefix=None, outputFunction=None):
    oldPrefix = ic.prefix
    oldOutputFunction = ic.outputFunction

    if prefix:
        ic.configureOutput(prefix=prefix)
    if outputFunction:
        ic.configureOutput(outputFunction=outputFunction)

    yield

    ic.configureOutput(oldPrefix, oldOutputFunction)


@contextmanager
def captureStandardStreams():
    newStdout = StringIO()
    newStderr = StringIO()
    realStdout = sys.stdout
    realStderr = sys.stderr
    try:
        sys.stdout = newStdout
        sys.stderr = newStderr
        yield newStdout, newStderr
    finally:
        sys.stdout = realStdout
        sys.stderr = realStderr


def pairIsNoArgumentsOutput(pair):
    name, ext = splitext(pair[0])
    return (
        name == splitext(MYFILENAME)[0] and ext in ['.py', '.pyc', '.pyo'] and
        int(pair[1]) > 0)


def parseOutputIntoPairs(out, err, assertNumLines,
                         prefix=icecream.DEFAULT_PREFIX):
    if isinstance(out, StringIO):
        out = out.getvalue()
    if isinstance(err, StringIO):
        err = err.getvalue()

    assert not out

    lines = err.splitlines()
    for line in lines:
        assert line.startswith(prefix)
    if assertNumLines:
        assert len(lines) == assertNumLines

    linePairs = []
    prefixStripped = [line[len(prefix):] for line in lines]
    for line in prefixStripped:
        pairStrs = line.split(', ')
        split = [s.split(':', 1) for s in pairStrs]
        pairs = [(arg.strip(), val.strip()) for arg, val in split]
        linePairs.append(pairs)

    return linePairs


class TestIceCream(unittest.TestCase):
    def testWithoutArgs(self):
        with captureStandardStreams() as (out, err):
            ic()
        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert pairIsNoArgumentsOutput(pair)

    def testAsArgument(self):
        with captureStandardStreams() as (out, err):
            noop(ic(1), ic(2))
        pairs = parseOutputIntoPairs(out, err, 2)
        assert pairs[0][0] == ('1', '1') and pairs[1][0] == ('2', '2')

        with captureStandardStreams() as (out, err):
            d = {1: ic(1)}
            l = [ic(2), ic()]
        pairs = parseOutputIntoPairs(out, err, 3)
        assert pairs[0][0] == ('1', '1')
        assert pairs[1][0] == ('2', '2')
        assert pairIsNoArgumentsOutput(pairs[2][0])

    def testSingleArgument(self):
        with captureStandardStreams() as (out, err):
            ic(1)
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('1', '1')

    def testMultipleArguments(self):
        with captureStandardStreams() as (out, err):
            ic(1, 2)
        pairs = parseOutputIntoPairs(out, err, 1)[0]
        assert pairs == [('1', '1'), ('2', '2')]

    def testNestedMultiline(self):
        with captureStandardStreams() as (out, err):
            ic(
                )
        assert pairIsNoArgumentsOutput(parseOutputIntoPairs(out, err, 1)[0][0])

        with captureStandardStreams() as (out, err):
            ic(1,
               'foo')
        pairs = parseOutputIntoPairs(out, err, 1)[0]
        assert pairs == [('1', '1'), ("'foo'", "'foo'")]

        with captureStandardStreams() as (out, err):
            noop(noop(noop({1: ic(
                noop())})))
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('noop()', 'None')

    def testExpressionArguments(self):
        class klass():
            attr = 'yep'
        d = {'d': {1: 'one'}, 'k': klass}

        with captureStandardStreams() as (out, err):
            ic(d['d'][1])
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ("d['d'][1]", "'one'")

        with captureStandardStreams() as (out, err):
            ic(d['k'].attr)
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ("d['k'].attr", "'yep'")

    def testMultipleCallsOnSameLine(self):
        with captureStandardStreams() as (out, err):
            ic(1); ic(2, 3)
        pairs = parseOutputIntoPairs(out, err, 2)
        assert pairs[0][0] == ('1', '1')
        assert pairs[1] == [('2', '2'), ('3', '3')]

    def testCallSurroundedByExpressions(self):
        with captureStandardStreams() as (out, err):
            noop(); ic(1); noop()
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('1', '1')

    def testComments(self):
        with captureStandardStreams() as (out, err):
            """Comment."""; ic(); # Comment.
        assert pairIsNoArgumentsOutput(parseOutputIntoPairs(out, err, 1)[0][0])

    def testMethodArguments(self):
        class Foo:
            def foo(self):
                return 'foo'
        f = Foo()
        with captureStandardStreams() as (out, err):
            ic(f.foo())
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('f.foo()', "'foo'")

    def testComplicated(self):
        with captureStandardStreams() as (out, err):
            noop(); ic(); noop(); ic(1,
                                     2, noop.__class__.__name__,
                                         noop ()); noop()
        pairs = parseOutputIntoPairs(out, err, 2)
        assert pairIsNoArgumentsOutput(pairs[0][0])
        assert pairs[1] == [
            ('1', '1'), ('2', '2'), ('noop.__class__.__name__', "'function'"),
            ('noop ()', 'None')]

    def testReturnValue(self):
        with captureStandardStreams() as (out, err):
            assert ic() is None
            assert ic(1) == 1
            assert ic(1, 2, 3) == (1, 2, 3)

    def testDifferentName(self):
        from icecream import ic as foo
        with captureStandardStreams() as (out, err):
            foo()
        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert pairIsNoArgumentsOutput(pair)

        newname = foo
        with captureStandardStreams() as (out, err):
            newname(1)
        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert pair == ('1', '1')

    def testPrefixConfiguration(self):
        prefix = 'lolsup '
        with configureIcecreamOutput(prefix):
            with captureStandardStreams() as (out, err):
                ic(1)
        pair = parseOutputIntoPairs(out, err, 1, prefix=prefix)[0][0]
        assert pair == ('1', '1')

        def prefixFunction():
            return 'lolsup '
        with configureIcecreamOutput(prefix=prefixFunction):
            with captureStandardStreams() as (out, err):
                ic(2)
        pair = parseOutputIntoPairs(out, err, 1, prefix=prefixFunction())[0][0]
        assert pair == ('2', '2')

    def testOutputFunction(self):
        l = []
        def appendTo(s):
            l.append(s)

        with configureIcecreamOutput(ic.prefix, appendTo):
            with captureStandardStreams() as (out, err):
                ic(1)
        assert not out.getvalue() and not err.getvalue()

        with configureIcecreamOutput(outputFunction=appendTo):
            with captureStandardStreams() as (out, err):
                ic(2)
        assert not out.getvalue() and not err.getvalue()

        pairs = parseOutputIntoPairs(out, '\n'.join(l), 2)
        assert pairs == [[('1', '1')], [('2', '2')]]

    def testEnableDisable(self):
        def noDebug():
            raise RuntimeError('you shall not pass')

        with captureStandardStreams() as (out, err):
            assert ic(1) == 1
            assert ic.enabled

            ic.disable(noDebug)
            assert not ic.enabled
            assert ic.callInstead
            with self.assertRaises(RuntimeError):
                ic(2)

            ic.disable()
            assert not ic.enabled
            assert not ic.callInstead
            assert ic(3) == 3

            ic.enable()
            assert ic.enabled
            assert ic(4) == 4

        pairs = parseOutputIntoPairs(out, err, 2)
        assert pairs == [[('1', '1')], [('4', '4')]]
