#!/usr/bin/env python
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

from __future__ import print_function

import inspect
import os
import pprint
import sys
import tokenize
from contextlib import contextmanager
from datetime import datetime
from os.path import basename

import colorama
from executing_node import Source
from pygments import highlight
# See https://gist.github.com/XVilka/8346728 for color support in various
# terminals and thus whether to use Terminal256Formatter or
# TerminalTrueColorFormatter.
from pygments.formatters import Terminal256Formatter
from pygments.lexers import PythonLexer as PyLexer, Python3Lexer as Py3Lexer

# Avoid a dependency on six (https://pythonhosted.org/six/) for just
# one import.
try:
    from StringIO import StringIO  # Python 2.
except ImportError:
    from io import StringIO  # Python 3.

from .coloring import SolarizedDark


PYTHON2 = (sys.version_info[0] == 2)


_absent = object()


def bindStaticVariable(name, value):
    def decorator(fn):
        setattr(fn, name, value)
        return fn
    return decorator


@bindStaticVariable('formatter', Terminal256Formatter(style=SolarizedDark))
@bindStaticVariable(
    'lexer', PyLexer(ensurenl=False) if PYTHON2 else Py3Lexer(ensurenl=False))
def colorize(s):
    self = colorize
    return highlight(s, self.lexer, self.formatter)


@contextmanager
def supportTerminalColorsInWindows():
    # Filter and replace ANSI escape sequences on Windows with equivalent Win32
    # API calls. This code does nothing on non-Windows systems.
    colorama.init()
    yield
    colorama.deinit()


def stderrPrint(*args):
    print(*args, file=sys.stderr)


def colorizedStderrPrint(s):
    colored = colorize(s)
    with supportTerminalColorsInWindows():
        stderrPrint(colored)


DEFAULT_PREFIX = 'ic| '
DEFAULT_INDENT = ' ' * 4
DEFAULT_LINE_WRAP_WIDTH = 70  # Characters.
DEFAULT_CONTEXT_DELIMITER = '- '
DEFAULT_OUTPUT_FUNCTION = colorizedStderrPrint
DEFAULT_ARG_TO_STRING_FUNCTION = pprint.pformat


class NoSourceAvailableError(OSError):
    """
    Raised when icecream fails to find or access required source code
    to parse and analyze. This can happen, for example, when

      - ic() is invoked inside an interactive shell, e.g. python -i

      - The source code is mangled and/or packaged, like with a project
        freezer like PyInstaller.

      - The underlying source code changed during execution. See
        https://stackoverflow.com/a/33175832.
    """
    infoMessage = (
        'Failed to access the underlying source code for analysis. Was ic() '
        'invoked in an interpreter (e.g. python -i), a frozen application '
        '(e.g. packaged with PyInstaller), or did the underlying source code '
        'change during execution?')


def callOrValue(obj):
    return obj() if callable(obj) else obj


def collapseWhitespaceBetweenTokens(s, removeNewlines=True):
    parsed = [
        t for t in tokenize.generate_tokens(StringIO(s).readline)
        if not removeNewlines or t[0] != tokenize.NL]

    tokens = [parsed[0]]
    for (_type, string, start, end, line) in parsed[1:]:
        startLine, startCol = start
        prevType, prevString, _, (prevEndLine, prevEndCol), _ = tokens[-1]

        if startLine != prevEndLine:  # Different line -> pass through as-is.
            token = (_type, string, start, end, line)
        else:  # Collapse whitespace.
            lineno = start[0]
            # Collapse all whitespace if <token> is a closing token or if the
            # previous token is an opening token. E.g. '2  ]' -> '2]' or '(  2'
            # -> '(2'.
            if (_type == tokenize.OP and string in ',)]}' or
                    prevType == tokenize.OP and prevString in '([{'):
                startCol = prevEndCol
            # Collapse to one space on a non-closing token. E.g. '3 +   2'
            # -> '3 + 2'.
            else:
                startCol = min(prevEndCol + 1, startCol)
            endCol = startCol + len(string)

            token = (_type, string, (lineno, startCol), (lineno, endCol), line)

        tokens.append(token)

    collapsed = tokenize.untokenize(tokens)

    return collapsed


def prefixLinesAfterFirst(prefix, s):
    lines = s.splitlines(True)

    for i in range(1, len(lines)):
        lines[i] = prefix + lines[i]

    return ''.join(lines)


def prefixIndent(prefix, s):
    indent = ' ' * len(prefix)

    looksLikeAString = s[0] + s[-1] in ["''", '""']
    if looksLikeAString:  # Align the start of multiline strings.
        s = prefixLinesAfterFirst(' ', s)

    return prefixLinesAfterFirst(indent, prefix + s)


def argumentToString(obj):
    s = DEFAULT_ARG_TO_STRING_FUNCTION(obj)
    s = s.replace('\\n', '\n')  # Preserve string newlines in output.
    return s


class IceCreamDebugger:
    _pairDelimiter = ', '  # Used by the tests in tests/.
    indent = DEFAULT_INDENT
    lineWrapWidth = DEFAULT_LINE_WRAP_WIDTH
    contextDelimiter = DEFAULT_CONTEXT_DELIMITER

    def __init__(self, prefix=DEFAULT_PREFIX,
                 outputFunction=DEFAULT_OUTPUT_FUNCTION,
                 argToStringFunction=argumentToString, includeContext=False):
        self.enabled = True
        self.prefix = prefix
        self.includeContext = includeContext
        self.outputFunction = outputFunction
        self.argToStringFunction = argToStringFunction

    def __call__(self, *args):
        if self.enabled:
            callFrame = inspect.currentframe().f_back
            try:
                out = self._format(callFrame, *args)
            except NoSourceAvailableError as err:
                prefix = callOrValue(self.prefix)
                out = prefix + 'Error: ' + err.infoMessage
            self.outputFunction(out)

        if not args:  # E.g. ic().
            passthrough = None
        elif len(args) == 1:  # E.g. ic(1).
            passthrough = args[0]
        else:  # E.g. ic(1, 2, 3).
            passthrough = args

        return passthrough

    def format(self, *args):
        callFrame = inspect.currentframe().f_back
        out = self._format(callFrame, *args)
        return out

    def _format(self, callFrame, *args):
        prefix = callOrValue(self.prefix)

        try:
            callNode = Source.executing_node(callFrame)
        except Exception:
            raise NoSourceAvailableError()

        context = self._formatContext(callFrame, callNode)
        if not args:
            time = self._formatTime()
            out = prefix + context + time
        else:
            if not self.includeContext:
                context = ''
            out = self._formatArgs(
                callFrame, callNode, prefix, context, args)

        return out

    def _formatArgs(self, callFrame, callNode, prefix, context, args):
        ast_tokens = Source.for_frame(callFrame).asttokens()
        sanitizedArgStrs = [
            collapseWhitespaceBetweenTokens(ast_tokens.get_text(arg))
            for arg in callNode.args]

        pairs = list(zip(sanitizedArgStrs, args))

        out = self._constructArgumentOutput(prefix, context, pairs)
        return out

    def _constructArgumentOutput(self, prefix, context, pairs):
        newline = os.linesep

        def argPrefix(arg):
            return '%s: ' % arg

        pairs = [(arg, self.argToStringFunction(val)) for arg, val in pairs]

        allArgsOnOneLine = self._pairDelimiter.join(
            val if arg == val else argPrefix(arg) + val for arg, val in pairs)
        multilineArgs = len(allArgsOnOneLine.splitlines()) > 1

        contextDelimiter = self.contextDelimiter if context else ''
        allPairs = prefix + context + contextDelimiter + allArgsOnOneLine
        firstLineTooLong = len(allPairs.splitlines()[0]) > self.lineWrapWidth

        if multilineArgs or firstLineTooLong:
            # ic| foo.py:11 in foo()
            #     multilineStr: 'line1
            #                    line2'
            #
            # ic| foo.py:11 in foo()
            #     a: 11111111111111111111
            #     b: 22222222222222222222
            if context:
                remaining = pairs
                start = prefix + context
            # ic| multilineStr: 'line1
            #                    line2'
            #
            # ic| a: 11111111111111111111
            #     b: 22222222222222222222
            else:
                remaining = pairs[1:]
                firstArg, firstVal = pairs[0]
                start = prefixIndent(
                    prefix + context + argPrefix(firstArg), firstVal)
        # ic| foo.py:11 in foo()- a: 1, b: 2
        elif context:
            remaining = []
            start = prefix + context + contextDelimiter + allArgsOnOneLine
        # ic| a: 1, b: 2, c: 3
        else:
            remaining = []
            start = prefix + allArgsOnOneLine

        if remaining:
            start += newline

        formatted = [
            prefixIndent(self.indent + argPrefix(arg), val)
            for arg, val in remaining]

        out = start + newline.join(formatted)
        return out

    def _formatContext(self, callFrame, callNode):
        filename, lineNumber, parentFunction = self._getContext(
            callFrame, callNode)

        if parentFunction != '<module>':
            parentFunction = '%s()' % parentFunction

        context = '%s:%s in %s' % (filename, lineNumber, parentFunction)
        return context

    def _formatTime(self):
        now = datetime.utcnow()
        formatted = now.strftime('%H:%M:%S.%f')[:-3]
        return ' at %s' % formatted

    def _getContext(self, callFrame, callNode):
        lineNumber = callNode.lineno
        frameInfo = inspect.getframeinfo(callFrame)
        parentFunction = frameInfo.function
        filename = basename(frameInfo.filename)

        return filename, lineNumber, parentFunction

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def configureOutput(self, prefix=_absent, outputFunction=_absent,
                        argToStringFunction=_absent, includeContext=_absent):
        if prefix is not _absent:
            self.prefix = prefix

        if outputFunction is not _absent:
            self.outputFunction = outputFunction

        if argToStringFunction is not _absent:
            self.argToStringFunction = argToStringFunction

        if includeContext is not _absent:
            self.includeContext = includeContext


ic = IceCreamDebugger()
