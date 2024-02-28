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

import functools
import sys
import unittest
import warnings

from io import StringIO
from contextlib import contextmanager
from os.path import basename, splitext, realpath

import icecream
from icecream import ic, argumentToString, stderrPrint, NO_SOURCE_AVAILABLE_WARNING_MESSAGE

TEST_PAIR_DELIMITER = '| '
MY_FILENAME = basename(__file__)
MY_FILEPATH = realpath(__file__)


a = 1
b = 2
c = 3


def noop(*args, **kwargs):
    return


def hasAnsiEscapeCodes(s):
    # Oversimplified, but ¯\_(ツ)_/¯. TODO(grun): Test with regex.
    return '\x1b[' in s


class FakeTeletypeBuffer(StringIO):
    """
    Extend StringIO to act like a TTY so ANSI control codes aren't stripped
    when wrapped with colorama's wrap_stream().
    """
    def isatty(self):
        return True


@contextmanager
def disableColoring():
    originalOutputFunction = ic.outputFunction

    ic.configureOutput(outputFunction=stderrPrint)
    yield
    ic.configureOutput(outputFunction=originalOutputFunction)


@contextmanager
def configureIcecreamOutput(prefix=None, outputFunction=None,
                            argToStringFunction=None, includeContext=None,
                            contextAbsPath=None):
    oldPrefix = ic.prefix
    oldOutputFunction = ic.outputFunction
    oldArgToStringFunction = ic.argToStringFunction
    oldIncludeContext = ic.includeContext
    oldContextAbsPath = ic.contextAbsPath

    if prefix:
        ic.configureOutput(prefix=prefix)
    if outputFunction:
        ic.configureOutput(outputFunction=outputFunction)
    if argToStringFunction:
        ic.configureOutput(argToStringFunction=argToStringFunction)
    if includeContext:
        ic.configureOutput(includeContext=includeContext)
    if contextAbsPath:
        ic.configureOutput(contextAbsPath=contextAbsPath)

    yield

    ic.configureOutput(
        oldPrefix, oldOutputFunction, oldArgToStringFunction,
        oldIncludeContext, oldContextAbsPath)


@contextmanager
def captureStandardStreams():
    realStdout = sys.stdout
    realStderr = sys.stderr
    newStdout = FakeTeletypeBuffer()
    newStderr = FakeTeletypeBuffer()
    try:
        sys.stdout = newStdout
        sys.stderr = newStderr
        yield newStdout, newStderr
    finally:
        sys.stdout = realStdout
        sys.stderr = realStderr


def stripPrefix(line):
    if line.startswith(ic.prefix):
        line = line.strip()[len(ic.prefix):]
    return line


def lineIsContextAndTime(line):
    line = stripPrefix(line)  # ic| f.py:33 in foo() at 08:08:51.389
    context, time = line.split(' at ')

    return (
        lineIsContext(context) and
        len(time.split(':')) == 3 and
        len(time.split('.')) == 2)


def lineIsContext(line):
    line = stripPrefix(line)  # ic| f.py:33 in foo()
    sourceLocation, function = line.split(' in ')  # f.py:33 in foo()
    filename, lineNumber = sourceLocation.split(':')  # f.py:33
    name, ext = splitext(filename)

    return (
        int(lineNumber) > 0 and
        ext in ['.py', '.pyc', '.pyo'] and
        name == splitext(MY_FILENAME)[0] and
        (function == '<module>' or function.endswith('()')))

def lineIsAbsPathContext(line):
    line = stripPrefix(line)  # ic| /absolute/path/to/f.py:33 in foo()
    sourceLocation, function = line.split(' in ')  # /absolute/path/to/f.py:33 in foo()
    filepath, lineNumber = sourceLocation.split(':')  # /absolute/path/to/f.py:33
    path, ext = splitext(filepath)

    return (
        int(lineNumber) > 0 and
        ext in ['.py', '.pyc', '.pyo'] and
        path == splitext(MY_FILEPATH)[0] and
        (function == '<module>' or function.endswith('()')))

def lineAfterContext(line, prefix):
    if line.startswith(prefix):
        line = line[len(prefix):]

    toks = line.split(' in ', 1)
    if len(toks) == 2:
        rest = toks[1].split(' ')
        line = ' '.join(rest[1:])

    return line


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
        line = lineAfterContext(line, prefix)

        if not line:
            linePairs.append([])
            continue

        pairStrs = line.split(TEST_PAIR_DELIMITER)
        pairs = [tuple(s.split(':', 1)) for s in pairStrs]
        # Indented line of a multiline value.
        if len(pairs[0]) == 1 and line.startswith(' '):
            arg, value = linePairs[-1][-1]
            looksLikeAString = value[0] in ["'", '"']
            prefix = ((arg + ': ' if arg is not None else '')  # A multiline value
                      + (' ' if looksLikeAString else ''))
            dedented = line[len(ic.prefix) + len(prefix):]
            linePairs[-1][-1] = (arg, value + '\n' + dedented)
        else:
            items = [
                (None, p[0].strip()) if len(p) == 1  # A value, like ic(3).
                else (p[0].strip(), p[1].strip())  # A variable, like ic(a).
                for p in pairs]
            linePairs.append(items)

    return linePairs


class TestIceCream(unittest.TestCase):
    def setUp(self):
        ic._pairDelimiter = TEST_PAIR_DELIMITER

    def testMetadata(self):
        def is_non_empty_string(s):
            return isinstance(s, str) and s
        assert is_non_empty_string(icecream.__title__)
        assert is_non_empty_string(icecream.__version__)
        assert is_non_empty_string(icecream.__license__)
        assert is_non_empty_string(icecream.__author__)
        assert is_non_empty_string(icecream.__contact__)
        assert is_non_empty_string(icecream.__description__)
        assert is_non_empty_string(icecream.__url__)

    def testWithoutArgs(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            ic()
        assert lineIsContextAndTime(err.getvalue())

    def testAsArgument(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            noop(ic(a), ic(b))
        pairs = parseOutputIntoPairs(out, err, 2)
        assert pairs[0][0] == ('a', '1') and pairs[1][0] == ('b', '2')

        with disableColoring(), captureStandardStreams() as (out, err):
            dic = {1: ic(a)}  # noqa
            lst = [ic(b), ic()]  # noqa
        pairs = parseOutputIntoPairs(out, err, 3)
        assert pairs[0][0] == ('a', '1')
        assert pairs[1][0] == ('b', '2')
        assert lineIsContextAndTime(err.getvalue().splitlines()[-1])

    def testSingleArgument(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            ic(a)
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('a', '1')

    def testMultipleArguments(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            ic(a, b)
        pairs = parseOutputIntoPairs(out, err, 1)[0]
        assert pairs == [('a', '1'), ('b', '2')]

    def testNestedMultiline(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            ic(
                )
        assert lineIsContextAndTime(err.getvalue())

        with disableColoring(), captureStandardStreams() as (out, err):
            ic(a,
               'foo')
        pairs = parseOutputIntoPairs(out, err, 1)[0]
        assert pairs == [('a',  '1'), (None, "'foo'")]

        with disableColoring(), captureStandardStreams() as (out, err):
            noop(noop(noop({1: ic(
                noop())})))
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('noop()', 'None')

    def testExpressionArguments(self):
        class klass():
            attr = 'yep'
        d = {'d': {1: 'one'}, 'k': klass}

        with disableColoring(), captureStandardStreams() as (out, err):
            ic(d['d'][1])
        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert pair == ("d['d'][1]", "'one'")

        with disableColoring(), captureStandardStreams() as (out, err):
            ic(d['k'].attr)
        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert pair == ("d['k'].attr", "'yep'")

    def testMultipleCallsOnSameLine(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            ic(a); ic(b, c)  # noqa
        pairs = parseOutputIntoPairs(out, err, 2)
        assert pairs[0][0] == ('a', '1')
        assert pairs[1] == [('b', '2'), ('c', '3')]

    def testCallSurroundedByExpressions(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            noop(); ic(a); noop()  # noqa
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('a', '1')

    def testComments(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            """Comment."""; ic(); # Comment.  # noqa
        assert lineIsContextAndTime(err.getvalue())

    def testMethodArguments(self):
        class Foo:
            def foo(self):
                return 'foo'
        f = Foo()
        with disableColoring(), captureStandardStreams() as (out, err):
            ic(f.foo())
        assert parseOutputIntoPairs(out, err, 1)[0][0] == ('f.foo()', "'foo'")

    def testComplicated(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            noop(); ic(); noop(); ic(a,  # noqa
                                     b, noop.__class__.__name__,  # noqa
                                         noop ()); noop()  # noqa
        pairs = parseOutputIntoPairs(out, err, 2)
        assert lineIsContextAndTime(err.getvalue().splitlines()[0])
        assert pairs[1] == [
            ('a', '1'), ('b', '2'), ('noop.__class__.__name__', "'function'"),
            ('noop ()', 'None')]

    def testReturnValue(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            assert ic() is None
            assert ic(1) == 1
            assert ic(1, 2, 3) == (1, 2, 3)

    def testDifferentName(self):
        from icecream import ic as foo
        with disableColoring(), captureStandardStreams() as (out, err):
            foo()
        assert lineIsContextAndTime(err.getvalue())

        newname = foo
        with disableColoring(), captureStandardStreams() as (out, err):
            newname(a)
        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert pair == ('a', '1')

    def testPrefixConfiguration(self):
        prefix = 'lolsup '
        with configureIcecreamOutput(prefix, stderrPrint):
            with disableColoring(), captureStandardStreams() as (out, err):
                ic(a)
        pair = parseOutputIntoPairs(out, err, 1, prefix=prefix)[0][0]
        assert pair == ('a', '1')

        def prefixFunction():
            return 'lolsup '
        with configureIcecreamOutput(prefix=prefixFunction):
            with disableColoring(), captureStandardStreams() as (out, err):
                ic(b)
        pair = parseOutputIntoPairs(out, err, 1, prefix=prefixFunction())[0][0]
        assert pair == ('b', '2')

    def testOutputFunction(self):
        lst = []

        def appendTo(s):
            lst.append(s)

        with configureIcecreamOutput(ic.prefix, appendTo):
            with captureStandardStreams() as (out, err):
                ic(a)
        assert not out.getvalue() and not err.getvalue()

        with configureIcecreamOutput(outputFunction=appendTo):
            with captureStandardStreams() as (out, err):
                ic(b)
        assert not out.getvalue() and not err.getvalue()

        pairs = parseOutputIntoPairs(out, '\n'.join(lst), 2)
        assert pairs == [[('a', '1')], [('b', '2')]]

    def testEnableDisable(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            assert ic(a) == 1
            assert ic.enabled

            ic.disable()
            assert not ic.enabled
            assert ic(b) == 2

            ic.enable()
            assert ic.enabled
            assert ic(c) == 3

        pairs = parseOutputIntoPairs(out, err, 2)
        assert pairs == [[('a', '1')], [('c', '3')]]

    def testArgToStringFunction(self):
        def hello(obj):
            return 'zwei'

        with configureIcecreamOutput(argToStringFunction=hello):
            with disableColoring(), captureStandardStreams() as (out, err):
                eins = 'ein'
                ic(eins)
        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert pair == ('eins', 'zwei')

    def testSingledispatchArgumentToString(self):
        def argumentToString_tuple(obj):
            return "Dispatching tuple!"

        # Prepare input and output
        x = (1, 2)
        default_output = ic.format(x)

        # Register
        argumentToString.register(tuple, argumentToString_tuple)
        assert tuple in argumentToString.registry
        assert str.endswith(ic.format(x), argumentToString_tuple(x))

        # Unregister
        argumentToString.unregister(tuple)
        assert tuple not in argumentToString.registry
        assert ic.format(x) == default_output

    def testSingleArgumentLongLineNotWrapped(self):
        # A single long line with one argument is not line wrapped.
        longStr = '*' * (ic.lineWrapWidth + 1)
        with disableColoring(), captureStandardStreams() as (out, err):
            ic(longStr)
        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert len(err.getvalue()) > ic.lineWrapWidth
        assert pair == ('longStr', ic.argToStringFunction(longStr))

    def testMultipleArgumentsLongLineWrapped(self):
        # A single long line with multiple variables is line wrapped.
        val = '*' * int(ic.lineWrapWidth / 4)
        valStr = ic.argToStringFunction(val)

        v1 = v2 = v3 = v4 = val
        with disableColoring(), captureStandardStreams() as (out, err):
            ic(v1, v2, v3, v4)

        pairs = parseOutputIntoPairs(out, err, 4)
        assert pairs == [[(k, valStr)] for k in ['v1', 'v2', 'v3', 'v4']]

        lines = err.getvalue().splitlines()
        assert (
            lines[0].startswith(ic.prefix) and
            lines[1].startswith(' ' * len(ic.prefix)) and
            lines[2].startswith(' ' * len(ic.prefix)) and
            lines[3].startswith(' ' * len(ic.prefix)))

    def testMultilineValueWrapped(self):
        # Multiline values are line wrapped.
        multilineStr = 'line1\nline2'
        with disableColoring(), captureStandardStreams() as (out, err):
            ic(multilineStr)
        pair = parseOutputIntoPairs(out, err, 2)[0][0]
        assert pair == ('multilineStr', ic.argToStringFunction(multilineStr))

    def testIncludeContextSingleLine(self):
        i = 3
        with configureIcecreamOutput(includeContext=True):
            with disableColoring(), captureStandardStreams() as (out, err):
                ic(i)

        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        assert pair == ('i', '3')

    def testContextAbsPathSingleLine(self):
        i = 3
        with configureIcecreamOutput(includeContext=True, contextAbsPath=True):
            with disableColoring(), captureStandardStreams() as (out, err):
                ic(i)
        # Output with absolute path can easily exceed line width, so no assert line num here.
        pairs = parseOutputIntoPairs(out, err, 0)
        assert [('i', '3')] in pairs

    def testValues(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            # Test both 'asdf' and "asdf"; see
            # https://github.com/gruns/icecream/issues/53.
            ic(3, 'asdf', "asdf")

        pairs = parseOutputIntoPairs(out, err, 1)
        assert pairs == [[(None, '3'), (None, "'asdf'"), (None, "'asdf'")]]

    def testIncludeContextMultiLine(self):
        multilineStr = 'line1\nline2'
        with configureIcecreamOutput(includeContext=True):
            with disableColoring(), captureStandardStreams() as (out, err):
                ic(multilineStr)

        firstLine = err.getvalue().splitlines()[0]
        assert lineIsContext(firstLine)

        pair = parseOutputIntoPairs(out, err, 3)[1][0]
        assert pair == ('multilineStr', ic.argToStringFunction(multilineStr))

    def testContextAbsPathMultiLine(self):
        multilineStr = 'line1\nline2'
        with configureIcecreamOutput(includeContext=True, contextAbsPath=True):
            with disableColoring(), captureStandardStreams() as (out, err):
                ic(multilineStr)

        firstLine = err.getvalue().splitlines()[0]
        assert lineIsAbsPathContext(firstLine)

        pair = parseOutputIntoPairs(out, err, 3)[1][0]
        assert pair == ('multilineStr', ic.argToStringFunction(multilineStr))
    
    def testFormat(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            """comment"""; noop(); ic(  # noqa
                'sup'); noop()  # noqa
        """comment"""; noop(); s = ic.format(  # noqa
            'sup'); noop()  # noqa
        assert s == err.getvalue().rstrip()

    def testMultilineInvocationWithComments(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            ic(  # Comment.

                a,  # Comment.

                # Comment.

                b,  # Comment.

                )  # Comment.

        pairs = parseOutputIntoPairs(out, err, 1)[0]
        assert pairs == [('a', '1'), ('b', '2')]

    def testNoSourceAvailablePrintsValues(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            with warnings.catch_warnings():
                # we ignore the warning so that it doesn't interfere
                # with parsing ic's output
                warnings.simplefilter("ignore")
                eval('ic(a, b)')
                pairs = parseOutputIntoPairs(out, err, 1)
                self.assertEqual(pairs, [[(None, '1'), (None, "2")]])

    def testNoSourceAvailablePrintsMultiline(self):
        """
        This tests for a bug which caused only multiline prints to fail.
        """
        multilineStr = 'line1\nline2'
        with disableColoring(), captureStandardStreams() as (out, err):
            with warnings.catch_warnings():
                # we ignore the warning so that it doesn't interfere
                # with parsing ic's output
                warnings.simplefilter("ignore")
                eval('ic(multilineStr)')
                pair = parseOutputIntoPairs(out, err, 2)[0][0]
                self.assertEqual(pair, (None, ic.argToStringFunction(multilineStr)))

    def testNoSourceAvailableIssuesExactlyOneWarning(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            with warnings.catch_warnings(record=True) as allWarnings:
                eval('ic(a)')
                eval('ic(b)')
                assert len(allWarnings) == 1
                warning = allWarnings[-1]
                assert NO_SOURCE_AVAILABLE_WARNING_MESSAGE in str(warning.message)

    def testSingleTupleArgument(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            ic((a, b))

        pair = parseOutputIntoPairs(out, err, 1)[0][0]
        self.assertEqual(pair, ('(a, b)', '(1, 2)'))

    def testMultilineContainerArgs(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            ic((a,
                b))
            ic([a,
                b])
            ic((a,
                b),
               [list(range(15)),
                list(range(15))])

        self.assertEqual(err.getvalue().strip(), """
ic| (a,
     b): (1, 2)
ic| [a,
     b]: [1, 2]
ic| (a,
     b): (1, 2)
    [list(range(15)),
     list(range(15))]: [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
                        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]]
        """.strip())

        with disableColoring(), captureStandardStreams() as (out, err):
            with configureIcecreamOutput(includeContext=True):
                ic((a,
                    b),
                   [list(range(15)),
                    list(range(15))])

        lines = err.getvalue().strip().splitlines()
        self.assertRegex(
            lines[0],
            r'ic\| test_icecream.py:\d+ in testMultilineContainerArgs\(\)',
        )
        self.assertEqual('\n'.join(lines[1:]), """\
    (a,
     b): (1, 2)
    [list(range(15)),
     list(range(15))]: [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
                        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]]""")

    def testMultipleTupleArguments(self):
        with disableColoring(), captureStandardStreams() as (out, err):
            ic((a, b), (b, a), a, b)

        pair = parseOutputIntoPairs(out, err, 1)[0]
        self.assertEqual(pair, [
            ('(a, b)', '(1, 2)'), ('(b, a)', '(2, 1)'), ('a', '1'), ('b', '2')])

    def testColoring(self):
        with captureStandardStreams() as (out, err):
            ic({1: 'str'})  # Output should be colored with ANSI control codes.

        assert hasAnsiEscapeCodes(err.getvalue())

    def testConfigureOutputWithNoParameters(self):
        with self.assertRaises(TypeError):
            ic.configureOutput()
