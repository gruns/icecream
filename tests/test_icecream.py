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
def configureIcecreamOutput(prefix=None, outputFunction=None,
                            argToStringFunction=None):
    oldPrefix = ic.prefix
    oldOutputFunction = ic.outputFunction
    oldArgToStringFunction = ic.argToStringFunction

    if prefix:
        ic.configureOutput(prefix=prefix)
    if outputFunction:
        ic.configureOutput(outputFunction=outputFunction)
    if argToStringFunction:
        ic.configureOutput(argToStringFunction=argToStringFunction)

    yield

    ic.configureOutput(oldPrefix, oldOutputFunction, oldArgToStringFunction)


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
    if assertNumLines:
        assert len(lines) == assertNumLines

    linePairs = []
    for line in lines:
        if line.startswith(prefix):
            line = line[len(prefix) : ]

        pairStrs = line.split(', ')
        split = [s.split(':', 1) for s in pairStrs]
        if len(split[0]) == 1:  # A line of a multiline value.
            arg, value = linePairs[-1][-1]
            looksLikeAString = value[0] in ["'", '"']
            prefix = (arg + ': ') + (' ' if looksLikeAString else '')
            dedented = line[len(ic.prefix) + len(prefix) : ]
            linePairs[-1][-1] = (arg, value + '\n' + dedented)
        else:
            pairs = [(arg.strip(), value.strip()) for arg, value in split]
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
        with captureStandardStreams() as (out, err):
            assert ic(1) == 1
            assert ic.enabled

            ic.disable()
            assert not ic.enabled
            assert ic(2) == 2

            ic.enable()
            assert ic.enabled
            assert ic(3) == 3

        pairs = parseOutputIntoPairs(out, err, 2)
        assert pairs == [[('1', '1')], [('3', '3')]]

    def testArgToStringFunction(self):
        hello = lambda obj: 'hello'

        with configureIcecreamOutput(argToStringFunction=hello):
            with captureStandardStreams() as (out, err):
                ic(1)
        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert pair == ('1', 'hello')

    def testSingleArgumentLongLineNotWrapped(self):
        # A single long line with one argument is not line wrapped.
        longStr = '*' * (ic.lineWrapWidth + 1)
        with captureStandardStreams() as (out, err):
            ic(longStr)
        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert len(err.getvalue()) > ic.lineWrapWidth
        assert pair == ('longStr', ic.argToStringFunction(longStr))

    def testMultipleArgumentsLongLineWrapped(self):
        # A single long line with multiple variables is line wrapped.
        v1 = v2 = v3 = v4 = '*' * int(ic.lineWrapWidth / 4)
        with captureStandardStreams() as (out, err):
            ic(v1, v2, v3, v4)
        pairs = parseOutputIntoPairs(out, err, 4)
        assert pairs == [
            [('v1', ic.argToStringFunction(v1))],
            [('v2', ic.argToStringFunction(v2))],
            [('v3', ic.argToStringFunction(v3))],
            [('v4', ic.argToStringFunction(v4))],]

    def testMultilineValueWrapped(self):
        # Multiline values are line wrapped.
        multilineStr = 'line1\nline2'
        with captureStandardStreams() as (out, err):
            ic(multilineStr)
        pair = parseOutputIntoPairs(out, err, 2)[0][0]
        assert pair == ('multilineStr', ic.argToStringFunction(multilineStr))
