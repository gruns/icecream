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

from __future__ import print_function

import ast
import inspect
import os
import pprint
import sys
from datetime import datetime
from contextlib import contextmanager
from os.path import basename
from textwrap import dedent

import colorama
import executing
from pygments import highlight
# See https://gist.github.com/XVilka/8346728 for color support in various
# terminals and thus whether to use Terminal256Formatter or
# TerminalTrueColorFormatter.
from pygments.formatters import Terminal256Formatter
from pygments.lexers import PythonLexer as PyLexer, Python3Lexer as Py3Lexer

from .coloring import SolarizedDark

try:
    from shutil import get_terminal_size
except ImportError:
    try:
        from backports.shutil_get_terminal_size import get_terminal_size
    except ImportError:
        def get_terminal_size():
            return os.environ['COLUMNS']


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


def isLiteral(s):
    try:
        ast.literal_eval(s)
    except Exception:
        return False
    return True


def colorizedStderrPrint(s):
    colored = colorize(s)
    with supportTerminalColorsInWindows():
        stderrPrint(colored)


DEFAULT_PREFIX = 'ic| '
DEFAULT_TERMINAL_WIDTH = 80
DEFAULT_LINE_WRAP_WIDTH = 70  # Characters.
DEFAULT_CONTEXT_DELIMITER = '- '
DEFAULT_OUTPUT_FUNCTION = colorizedStderrPrint
DEFAULT_ARG_TO_STRING_FUNCTION = pprint.pformat


class NoSourceAvailableError(OSError):
    """
    Raised when icecream fails to find or access source code that's
    required to parse and analyze. This can happen, for example, when

      - ic() is invoked inside a REPL or interactive shell, e.g. from the
        command line (CLI) or with python -i.

      - The source code is mangled and/or packaged, e.g. with a project
        freezer like PyInstaller.

      - The underlying source code changed during execution. See
        https://stackoverflow.com/a/33175832.
    """
    infoMessage = (
        'Failed to access the underlying source code for analysis. Was ic() '
        'invoked in a REPL (e.g. from the command line), a frozen application '
        '(e.g. packaged with PyInstaller), or did the underlying source code '
        'change during execution?')


def callOrValue(obj):
    return obj() if callable(obj) else obj


class Source(executing.Source):
    def get_text_with_indentation(self, node):
        result = self.asttokens().get_text(node)
        if '\n' in result:
            result = ' ' * node.first_token.start[1] + result
            result = dedent(result)
        result = result.strip()
        return result


def prefixLinesAfterFirst(prefix, s):
    lines = s.splitlines(True)

    for i in range(1, len(lines)):
        lines[i] = prefix + lines[i]

    return ''.join(lines)


def indented_lines(prefix, string):
    lines = string.splitlines()
    return [prefix + lines[0]] + [
        ' ' * len(prefix) + line
        for line in lines[1:]
    ]


def format_pair(prefix, arg, value):
    arg_lines = indented_lines(prefix, arg)
    value_prefix = arg_lines[-1] + ': '

    looksLikeAString = value[0] + value[-1] in ["''", '""']
    if looksLikeAString:  # Align the start of multiline strings.
        value = prefixLinesAfterFirst(' ', value)

    value_lines = indented_lines(value_prefix, value)
    lines = arg_lines[:-1] + value_lines
    return '\n'.join(lines)


def argumentToString(obj, width=DEFAULT_LINE_WRAP_WIDTH):
    s = DEFAULT_ARG_TO_STRING_FUNCTION(obj, width=width)
    s = s.replace('\\n', '\n')  # Preserve string newlines in output.
    return s


def detect_terminal_width(default=DEFAULT_TERMINAL_WIDTH):
    """ Returns the number of columns that this terminal can handle. """
    try:
        # We need to pass a terminal height in the tuple so we pass the default
        # of 25 lines but it's not used for anything.
        width = get_terminal_size((default, 25)).columns
    except Exception:  # Not in TTY or something else went wrong
        width = default
    # TODO account for argPrefix()
    return width


def supports_param(fn, param="width"):
    """ Returns True if the function supports that parameter. """
    try:
        from inspect import signature
        return param in signature(fn).parameters
    except ImportError:  # Python 2.x
        from inspect import getargspec
        return param in getargspec(fn).args


class IceCreamDebugger:
    _pairDelimiter = ', '  # Used by the tests in tests/.
    contextDelimiter = DEFAULT_CONTEXT_DELIMITER
    terminalWidth = DEFAULT_TERMINAL_WIDTH
    lineWrapWidth = DEFAULT_LINE_WRAP_WIDTH

    def __init__(self, prefix=DEFAULT_PREFIX,
                 outputFunction=DEFAULT_OUTPUT_FUNCTION,
                 argToStringFunction=argumentToString, includeContext=False,
                 detectTerminalWidth=False):
        self.enabled = True
        self.prefix = prefix
        self.includeContext = includeContext
        self.outputFunction = outputFunction
        self.argToStringFunction = argToStringFunction
        self.passWidthParam = supports_param(self.argToStringFunction)
        self._setLineWrapWidth(detectTerminalWidth=detectTerminalWidth)

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

    def _setLineWrapWidth(self, detectTerminalWidth=False, terminalWidth=None):
        prefix_length = len(self.prefix()) if callable(self.prefix) else len(self.prefix)
        if terminalWidth:
            width = terminalWidth
        elif detectTerminalWidth is True:
            width = detect_terminal_width(DEFAULT_TERMINAL_WIDTH)
        else:
            width = DEFAULT_TERMINAL_WIDTH
        self.terminalWidth = width
        self.lineWrapWidth = width - prefix_length

    def format(self, *args):
        callFrame = inspect.currentframe().f_back
        out = self._format(callFrame, *args)
        return out

    def _format(self, callFrame, *args):
        prefix = callOrValue(self.prefix)

        callNode = Source.executing(callFrame).node
        if callNode is None:
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
        source = Source.for_frame(callFrame)
        sanitizedArgStrs = [
            source.get_text_with_indentation(arg)
            for arg in callNode.args]

        pairs = list(zip(sanitizedArgStrs, args))

        out = self._constructArgumentOutput(prefix, context, pairs)
        return out

    def _constructArgumentOutput(self, prefix, context, pairs):
        def argPrefix(arg):
            return '%s: ' % arg

        kwargs = {"width": self.lineWrapWidth} if self.passWidthParam else {}
        pairs = [(arg, self.argToStringFunction(val, **kwargs)) for arg, val in pairs]
        # For cleaner output, if <arg> is a literal, eg 3, "string", b'bytes',
        # etc, only output the value, not the argument and the value, as the
        # argument and the value will be identical or nigh identical. Ex: with
        # ic("hello"), just output
        #
        #   ic| 'hello',
        #
        # instead of
        #
        #   ic| "hello": 'hello'.
        #
        pairStrs = [
            val if isLiteral(arg) else (argPrefix(arg) + val)
            for arg, val in pairs]

        allArgsOnOneLine = self._pairDelimiter.join(pairStrs)
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
                lines = [prefix + context] + [
                    format_pair(len(prefix) * ' ', arg, value)
                    for arg, value in pairs
                ]
            # ic| multilineStr: 'line1
            #                    line2'
            #
            # ic| a: 11111111111111111111
            #     b: 22222222222222222222
            else:
                arg_lines = [
                    format_pair('', arg, value)
                    for arg, value in pairs
                ]
                lines = indented_lines(prefix, '\n'.join(arg_lines))
        # ic| foo.py:11 in foo()- a: 1, b: 2
        # ic| a: 1, b: 2, c: 3
        else:
            lines = [prefix + context + contextDelimiter + allArgsOnOneLine]

        return '\n'.join(lines)

    def _formatContext(self, callFrame, callNode):
        filename, lineNumber, parentFunction = self._getContext(
            callFrame, callNode)

        if parentFunction != '<module>':
            parentFunction = '%s()' % parentFunction

        context = '%s:%s in %s' % (filename, lineNumber, parentFunction)
        return context

    def _formatTime(self):
        now = datetime.now()
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
                        argToStringFunction=_absent, includeContext=_absent,
                        terminalWidth=_absent):
        if prefix is not _absent:
            self.prefix = prefix

        if prefix is not _absent or terminalWidth is not _absent:
            new_terminal_width = terminalWidth if terminalWidth is not _absent else None
            self._setLineWrapWidth(new_terminal_width)

        if outputFunction is not _absent:
            self.outputFunction = outputFunction

        if argToStringFunction is not _absent:
            self.argToStringFunction = argToStringFunction
            self.passWidthParam = supports_param(self.argToStringFunction)

        if includeContext is not _absent:
            self.includeContext = includeContext


ic = IceCreamDebugger()
