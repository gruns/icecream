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

import ast
import enum
import inspect
import pprint
import sys
from types import FrameType
from typing import Optional, cast, Any, Callable, Generator, List, Sequence, Tuple, Type, Union, cast, Literal
import warnings
from datetime import datetime
import functools
from contextlib import contextmanager
from os.path import basename, realpath
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


class Sentinel(enum.Enum):
    absent = object()


def bindStaticVariable(name: str, value: Any) -> Callable:
    def decorator(fn: Callable) -> Callable:
        setattr(fn, name, value)
        return fn
    return decorator


@bindStaticVariable('formatter', Terminal256Formatter(style=SolarizedDark))
@bindStaticVariable('lexer', Py3Lexer(ensurenl=False))
def colorize(s: str) -> str:
    self = colorize
    return highlight(
        s,
        cast(Py3Lexer, self.lexer),
        cast(Terminal256Formatter, self.formatter)
    )  # pyright: ignore[reportFunctionMemberAccess]


@contextmanager
def supportTerminalColorsInWindows() -> Generator:
    # Filter and replace ANSI escape sequences on Windows with equivalent Win32
    # API calls. This code does nothing on non-Windows systems.
    if sys.platform.startswith('win'):
        colorama.init()
        yield
        colorama.deinit()
    else:
        yield


def stderrPrint(*args: object) -> None:
    print(*args, file=sys.stderr)


def isLiteral(s: str) -> bool:
    try:
        ast.literal_eval(s)
    except Exception:
        return False
    return True


def colorizedStderrPrint(s: str) -> None:
    colored = colorize(s)
    with supportTerminalColorsInWindows():
        stderrPrint(colored)


def colorizedStdoutPrint(s: str) -> None:
    colored = colorize(s)
    with supportTerminalColorsInWindows():
        print(colored)


def safe_pformat(obj: object, *args: Any, **kwargs: Any) -> str:
    try:
        return pprint.pformat(obj, *args, **kwargs)
    except TypeError as e:
        # Sorting likely tripped on symbolic/elementwise comparisons
        warnings.warn(f"pprint failed ({e}); retrying without dict sorting")
        try:
            # Py 3.8+: disable sorting globally for all nested dicts
            return pprint.pformat(obj, *args, sort_dicts=False, **kwargs)
        except TypeError:
            # Py < 3.8: last-ditch, always works
            return repr(obj)


DEFAULT_PREFIX = 'ic| '
DEFAULT_LINE_WRAP_WIDTH = 70  # Characters.
DEFAULT_CONTEXT_DELIMITER = '- '
DEFAULT_OUTPUT_FUNCTION = colorizedStderrPrint
DEFAULT_ARG_TO_STRING_FUNCTION = safe_pformat

"""
This info message is printed instead of the arguments when icecream
fails to find or access source code that's required to parse and analyze.
This can happen, for example, when

  - ic() is invoked inside a REPL or interactive shell, e.g. from the
    command line (CLI) or with python -i.

  - The source code is mangled and/or packaged, e.g. with a project
    freezer like PyInstaller.

  - The underlying source code changed during execution. See
    https://stackoverflow.com/a/33175832.
"""
NO_SOURCE_AVAILABLE_WARNING_MESSAGE = (
    'Failed to access the underlying source code for analysis. Was ic() '
    'invoked in a REPL (e.g. from the command line), a frozen application '
    '(e.g. packaged with PyInstaller), or did the underlying source code '
    'change during execution?')


def callOrValue(obj: object) -> object:
    return obj() if callable(obj) else obj


class Source(executing.Source):
    def get_text_with_indentation(self, node: ast.expr) -> str:
        result = self.asttokens().get_text(node)
        if '\n' in result:
            result = ' ' * node.first_token.start[1] + result # type: ignore[attr-defined]
            result = dedent(result)
        result = result.strip()
        return result


def prefixLines(prefix: str, s: str, startAtLine: int = 0) -> List[str]:
    lines = s.splitlines()

    for i in range(startAtLine, len(lines)):
        lines[i] = prefix + lines[i]

    return lines


def prefixFirstLineIndentRemaining(prefix: str, s: str) -> List[str]:
    indent = ' ' * len(prefix)
    lines = prefixLines(indent, s, startAtLine=1)
    lines[0] = prefix + lines[0]
    return lines


def formatPair(prefix: str, arg: Union[str, Sentinel], value: str) -> str:
    if arg is Sentinel.absent:
        argLines = []
        valuePrefix = prefix
    else:
        argLines = prefixFirstLineIndentRemaining(prefix, arg)
        valuePrefix = argLines[-1] + ': '

    looksLikeAString = (value[0] + value[-1]) in ["''", '""']
    if looksLikeAString:  # Align the start of multiline strings.
        valueLines = prefixLines(' ', value, startAtLine=1)
        value = '\n'.join(valueLines)

    valueLines = prefixFirstLineIndentRemaining(valuePrefix, value)
    lines = argLines[:-1] + valueLines
    return '\n'.join(lines)


class _SingleDispatchCallable:
    def __call__(self, *args: object) -> str:
        # This is a marker class, not a real thing you should use
        raise NotImplemented
    
    register: Callable[[Type], Callable]


def singledispatch(func: Callable) -> _SingleDispatchCallable:
    func = functools.singledispatch(func)

    # add unregister based on https://stackoverflow.com/a/25951784
    assert func.register.__closure__ is not None
    closure = dict(zip(func.register.__code__.co_freevars,
                       func.register.__closure__))
    registry = closure['registry'].cell_contents
    dispatch_cache = closure['dispatch_cache'].cell_contents

    def unregister(cls: Type) -> None:
        del registry[cls]
        dispatch_cache.clear()

    func.unregister = unregister  # type: ignore[attr-defined]
    return cast(_SingleDispatchCallable, func)


@singledispatch
def argumentToString(obj: object) -> str:
    s = DEFAULT_ARG_TO_STRING_FUNCTION(obj)
    s = s.replace('\\n', '\n')  # Preserve string newlines in output.
    return s


@argumentToString.register(str)
def _(obj: str) -> str:
    if '\n' in obj:
        return "'''" + obj + "'''"

    return "'" + obj.replace('\\', '\\\\') + "'"


class IceCreamDebugger:
    _pairDelimiter = ', '  # Used by the tests in tests/.
    lineWrapWidth = DEFAULT_LINE_WRAP_WIDTH
    contextDelimiter = DEFAULT_CONTEXT_DELIMITER

    def __init__(self, prefix: Union[str, Callable[[], str]] =DEFAULT_PREFIX,
                 outputFunction: Callable[[str], None]=DEFAULT_OUTPUT_FUNCTION,
                 argToStringFunction: Union[_SingleDispatchCallable, Callable[[Any], str]]=argumentToString, includeContext: bool=False,
                 contextAbsPath: bool=False):
        self.enabled = True
        self.prefix = prefix
        self.includeContext = includeContext
        self.outputFunction = outputFunction
        self.argToStringFunction = argToStringFunction
        self.contextAbsPath = contextAbsPath

    def __call__(self, *args: object) -> object:
        if self.enabled:
            currentFrame = inspect.currentframe()
            assert currentFrame is not None and currentFrame.f_back is not None
            callFrame = currentFrame.f_back
            self.outputFunction(self._format(callFrame, *args))

        if not args:  # E.g. ic().
            passthrough = None
        elif len(args) == 1:  # E.g. ic(1).
            passthrough = args[0]
        else:  # E.g. ic(1, 2, 3).
            passthrough = args

        return passthrough

    def format(self, *args: object) -> str:
        currentFrame = inspect.currentframe()
        assert currentFrame is not None and currentFrame.f_back is not None
        callFrame = currentFrame.f_back
        out = self._format(callFrame, *args)
        return out

    def _format(self, callFrame: FrameType, *args: object) -> str:
        prefix = cast(str, callOrValue(self.prefix))

        context = self._formatContext(callFrame)
        if not args:
            time = self._formatTime()
            out = prefix + context + time
        else:
            if not self.includeContext:
                context = ''
            out = self._formatArgs(
                callFrame, prefix, context, args)

        return out

    def _formatArgs(self, callFrame: FrameType, prefix: str, context: str, args: Sequence[object]) -> str:
        callNode = Source.executing(callFrame).node
        if callNode is not None:
            assert isinstance(callNode, ast.Call)
            source = cast(Source, Source.for_frame(callFrame))
            sanitizedArgStrs = [
                source.get_text_with_indentation(arg)
                for arg in callNode.args]
        else:
            warnings.warn(
                NO_SOURCE_AVAILABLE_WARNING_MESSAGE,
                category=RuntimeWarning, stacklevel=4)
            sanitizedArgStrs = [Sentinel.absent] * len(args)

        pairs = list(zip(sanitizedArgStrs, cast(List[str], args)))

        out = self._constructArgumentOutput(prefix, context, pairs)
        return out

    def _constructArgumentOutput(self, prefix: str, context: str, pairs: Sequence[Tuple[Union[str, Sentinel], str]]) -> str:
        def argPrefix(arg: str) -> str:
            return '%s: ' % arg

        pairs = [(arg, self.argToStringFunction(val)) for arg, val in pairs]
        # For cleaner output, if <arg> is a literal, eg 3, "a string",
        # b'bytes', etc, only output the value, not the argument and the
        # value, because the argument and the value will be identical or
        # nigh identical. Ex: with ic("hello"), just output
        #
        #   ic| 'hello',
        #
        # instead of
        #
        #   ic| "hello": 'hello'.
        #
        # When the source for an arg is missing we also only print the value,
        # since we can't know anything about the argument itself.
        pairStrs = [
            val if (arg is Sentinel.absent or isLiteral(arg))
            else (argPrefix(arg) + val)
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
                    formatPair(len(prefix) * ' ', arg, value)
                    for arg, value in pairs
                ]
            # ic| multilineStr: 'line1
            #                    line2'
            #
            # ic| a: 11111111111111111111
            #     b: 22222222222222222222
            else:
                argLines = [
                    formatPair('', arg, value)
                    for arg, value in pairs
                ]
                lines = prefixFirstLineIndentRemaining(prefix, '\n'.join(argLines))
        # ic| foo.py:11 in foo()- a: 1, b: 2
        # ic| a: 1, b: 2, c: 3
        else:
            lines = [prefix + context + contextDelimiter + allArgsOnOneLine]

        return '\n'.join(lines)

    def _formatContext(self, callFrame: FrameType) -> str:
        filename, lineNumber, parentFunction = self._getContext(callFrame)

        if parentFunction != '<module>':
            parentFunction = '%s()' % parentFunction

        context = '%s:%s in %s' % (filename, lineNumber, parentFunction)
        return context

    def _formatTime(self) -> str:
        now = datetime.now()
        formatted = now.strftime('%H:%M:%S.%f')[:-3]
        return ' at %s' % formatted

    def _getContext(self, callFrame: FrameType) -> Tuple[str, int, str]:
        frameInfo = inspect.getframeinfo(callFrame)
        lineNumber = frameInfo.lineno
        parentFunction = frameInfo.function

        filepath = (realpath if self.contextAbsPath else basename)(frameInfo.filename)  # type: ignore[operator]
        return filepath, lineNumber, parentFunction

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def use_stdout(self) -> None:
        self.outputFunction = colorizedStdoutPrint

    def use_stderr(self) -> None:
        self.outputFunction = colorizedStderrPrint

    def configureOutput(
        self: "IceCreamDebugger",
        prefix: Union[str, Literal[Sentinel.absent]] = Sentinel.absent,
        outputFunction: Union[Callable, Literal[Sentinel.absent]] = Sentinel.absent,
        argToStringFunction: Union[Callable, Literal[Sentinel.absent]] = Sentinel.absent,
        includeContext: Union[bool, Literal[Sentinel.absent]] = Sentinel.absent,
        contextAbsPath: Union[bool, Literal[Sentinel.absent]] = Sentinel.absent,
        lineWrapWidth: Union[bool, Literal[Sentinel.absent]] = Sentinel.absent
    ) -> None:
        noParameterProvided = all(
            v is Sentinel.absent for k, v in locals().items() if k != 'self')
        if noParameterProvided:
            raise TypeError('configureOutput() missing at least one argument')

        if prefix is not Sentinel.absent:
            self.prefix = prefix

        if outputFunction is not Sentinel.absent:
            self.outputFunction = outputFunction

        if argToStringFunction is not Sentinel.absent:
            self.argToStringFunction = argToStringFunction

        if includeContext is not Sentinel.absent:
            self.includeContext = includeContext

        if contextAbsPath is not Sentinel.absent:
            self.contextAbsPath = contextAbsPath

        if lineWrapWidth is not Sentinel.absent:
            self.lineWrapWidth = lineWrapWidth


ic = IceCreamDebugger()
