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

import os
import ast
import dis
import sys
import pprint
import inspect
import textwrap
from os.path import basename


_absent = object()


def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


MYNAME = 'ic'
DEFAULT_INDENT = ' ' * 4
DEFAULT_LINE_WRAP_WIDTH = 70  # Characters.
DEFAULT_PREFIX = '%s| ' % MYNAME
DEFAULT_CONTEXT_DELIMITER = '- '
DEFAULT_OUTPUT_FUNCTION = errprint
DEFAULT_ARG_TO_STRING_FUNCTION = pprint.pformat


def classname(obj):
    return obj.__class__.__name__


def callOrValue(obj):
    return obj() if callable(obj) else obj


def splitStringAtIndices(s, indices):
    return [s[i:j] for i, j in zip([0] + indices, indices + [None]) if s[i:j]]


def calculateLineOffsets(code):
    return dict((line, offset) for offset, line in dis.findlinestarts(code))


def joinContinuedLines(lines):
    for i, line in enumerate(lines):
        if i < len(lines) - 1 and not line.endswith('\\'):
            lines[i] += ' \\'
    joined = '\n'.join(lines)
    return joined


def isAstNodeIceCreamCall(node, icNames, methodName):
    callMatch = (
        classname(node) == 'Call' and
        classname(node.func) == 'Name' and
        node.func.id in icNames)

    methodMatch = (
        classname(node) == 'Call' and
        classname(node.func) == 'Attribute' and
        classname(node.func.value) == 'Name' and
        node.func.value.id in icNames and
        node.func.attr == methodName)

    return callMatch or methodMatch


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


def determinePossibleIcNames(callFrame):
    # TODO(grun): Determine possible ic() invocation names dynamically from the
    # source to account for name indirection. For example, ic() could be
    # invoked like
    #
    #   class Foo:
    #     blah = ic
    #   Foo.blah()
    #
    # This function, as it exists now, fails to detect the above. Instead, it
    # only checks for variables in locals() and globals() that are equal to
    # ic(). Like
    #
    #   from icecream import ic as foo
    #   foo()
    #
    # and
    #
    #   from icecream import ic newname = ic newname('blah')
    items = list(callFrame.f_locals.items()) + list(callFrame.f_globals.items())
    names = [name for name, value in items if value is ic]
    unique = list(set(names))

    return unique


def getCallSourceLines(icNames, icMethod, callFrame):
    code = callFrame.f_code

    # inspect.getblock(), which is called internally by inspect.getsource(),
    # only returns the first line of <code> when <code> represents a top-level
    # module, not the entire module's source, as needed here. The
    #
    #   if ismodule(object):
    #       return lines, 0
    #
    # check in inspect.py doesn't account for code objects of modules, only
    # actual module objects themselves.
    # 
    # A workaround is to call findsource() directly on code objects of modules,
    # which bypasses getblock().
    if code.co_name == '<module>':  # Module -> use workaround explained above.
        parentBlockStartLine = 1
        parentBlockSource = ''.join(inspect.findsource(code)[0])
    else:  # Not a module -> use inspect.getsource() normally.
        parentBlockStartLine = code.co_firstlineno
        parentBlockSource = inspect.getsource(code)

    lineno = inspect.getframeinfo(callFrame)[1]
    linenoRelativeToParent = lineno - parentBlockStartLine + 1

    # There could be multiple ic() calls on the same line(s), like
    #
    #   ic(1); ic(2); ic(3,
    #       4,
    #       5); ic(6)
    #
    # so include all of them. Which invocation is the appropriate one will be
    # determined later via bytecode offset calculations.
    #
    # TODO(grun): Support invocations of ic() where ic() is an attribute chain
    # in the AST. For example, support
    #
    #   import icecream
    #   icecream.ic()
    #
    # and
    #
    #   class Foo:
    #     blah = ic
    #   Foo.blah()
    #
    parentBlockSource = textwrap.dedent(parentBlockSource)
    potentialCalls = [
        node for node in ast.walk(ast.parse(parentBlockSource))
        if isAstNodeIceCreamCall(node, icNames, icMethod) and (
            node.lineno == linenoRelativeToParent or
            any(arg.lineno == linenoRelativeToParent for arg in node.args))]

    endLine = lineno - parentBlockStartLine + 1
    startLine = min(call.lineno for call in potentialCalls)
    lines = parentBlockSource.splitlines()[startLine - 1 : endLine]
    source = ' '.join(line.strip() for line in lines)

    callOffset = callFrame.f_lasti
    absoluteStartLineNum = parentBlockStartLine + startLine - 1
    startLineOffset = calculateLineOffsets(code)[absoluteStartLineNum]

    return source, absoluteStartLineNum, startLineOffset


def splitExpressionsOntoSeparateLines(source):
    """
    Split every expression onto its own line so any preceding and/or trailing
    expressions, like 'foo(1); ' and '; foo(2)' of

      foo(1); ic(1); foo(2)

    are properly separated from ic(1) for dis.findlinestarts(). Otherwise, any
    preceding and/or trailing expressions break ic(1)'s bytecode offset
    calculation with dis.findlinestarts().
    """
    indices = [expr.col_offset for expr in ast.parse(source).body]
    lines = [s.strip() for s in splitStringAtIndices(source, indices)]
    oneExpressionPerLine = joinContinuedLines(lines)

    return oneExpressionPerLine


def splitCallsOntoSeparateLines(icNames, icMethod, source):
    """
    To determine the bytecode offsets of ic() calls with dis.findlinestarts(),
    every ic() invocation needs to start its own line. That is, this
    
      foo(ic(1), ic(2))
    
    needs to be turned into
    
      foo(
      ic(1),
      ic(2))
    
    Then the bytecode offsets of ic(1) and ic(2) can be determined with
    dis.findlinestarts().

    This split is necessary for ic() calls inside other expressions,
    like foo(ic(1)), to be extracted correctly.
    """
    callIndices = [
        node.func.col_offset if hasattr(node, 'func') else node.col_offset
        for node in ast.walk(ast.parse(source))
        if isAstNodeIceCreamCall(node, icNames, icMethod)]
    lines = splitStringAtIndices(source, callIndices)
    sourceWithNewlinesBeforeInvocations = joinContinuedLines(lines)

    return sourceWithNewlinesBeforeInvocations


def extractCallStrByOffset(splitSource, callOffset):
    code = compile(splitSource, '<string>', 'exec')
    lineOffsets = sorted(calculateLineOffsets(code).items())

    # For lines with multiple invocations, like 'ic(1); ic(2)', determine which
    # invocation was called.
    for lineno, offset in lineOffsets:
        if callOffset >= offset:
            sourceLineIndex = lineno - 1
        else:
            break

    lines = [s.rstrip(' ;') for s in splitSource.splitlines()]
    line = lines[sourceLineIndex]

    # Find the ic() call's matching right parenthesis. This is necessary
    # whenever there are closing tokens (e.g. ')', ']', '}', etc) after the
    # ic() call. Like
    #
    #   foo(
    #     foo(
    #       {
    #         ic(
    #           bar()) == 3}))
    #
    # where the <line> 'ic(bar()) == 3}))' needs to be trimmed to just
    # 'ic(foo())'. Unfortunately, afaik there's no way to determine the
    # character width of a function call, or its last argument, from the AST,
    # so a workaround is to loop and test each successive right paren in
    # <line>, from left to right, until ic()'s matching right paren is
    # found. Bit of a hack, but ¯\_(ツ)_/¯.
    tmp = line[:line.find(')') + 1]
    while True:
        try:
            ast.parse(tmp)
            break
        except SyntaxError:
            tmp = line[:line.find(')', len(tmp)) + 1]

    callStr = tmp
    return callStr


def extractArgumentsFromCallStr(callStr):
    """
    Parse the argument string via an AST instead of the overly simple
    callStr.split(','). The latter incorrectly splits any string parameters
    that contain commas therein, like ic(1, 'a,b', 2).
    """
    params = callStr.split('(', 1)[-1].rsplit(')', 1)[0].strip()

    body = ast.parse(params).body[0]
    eles = body.value.elts if classname(body.value) == 'Tuple' else [body.value]

    indices = [ele.col_offset for ele in eles]
    argStrs = [s.strip(' ,') for s in splitStringAtIndices(params, indices)]

    return argStrs


def argumentToString(obj):
    s = DEFAULT_ARG_TO_STRING_FUNCTION(obj)
    s = s.replace('\\n', '\n')  # Preserve string newlines in output.
    return s


class IceCreamDebugger:
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
            out = self._format(callFrame, *args)
            self.outputFunction(out)

        if not args:  # E.g. ic().
            ret = None
        elif len(args) == 1:  # E.g. ic(1).
            ret = args[0]
        else:  # E.g. ic(1, 2, 3).
            ret = args

        return ret

    def format(self, *args):
        callFrame = inspect.currentframe().f_back
        out = self._format(callFrame, *args)
        return out

    def _format(self, callFrame, *args):
        icNames = determinePossibleIcNames(callFrame)

        parentFrame = inspect.currentframe().f_back
        icMethod = inspect.getframeinfo(parentFrame).function

        prefix = callOrValue(self.prefix)
        context = self._formatContext(callFrame, icNames, icMethod)
        if not args:
            out = prefix + context
        else:
            if not self.includeContext:
                context = ''
            out = self._formatArgs(
                callFrame, icNames, icMethod, prefix, context, args)

        return out

    def _formatArgs(self, callFrame, icNames, icMethod, prefix, context, args):
        callSource, _, callSourceOffset = getCallSourceLines(
            icNames, icMethod, callFrame)

        callOffset = callFrame.f_lasti
        relativeCallOffset = callOffset - callSourceOffset
        
        # Insert newlines before every expression and every ic() call so a
        # mapping between `col_offset`s (in characters) and `f_lasti`s (in
        # bytecode) can be established with dis.findlinestarts().
        oneExpressionPerLine = splitExpressionsOntoSeparateLines(callSource)
        splitSource = splitCallsOntoSeparateLines(
            icNames, icMethod, oneExpressionPerLine)

        callStr = extractCallStrByOffset(splitSource, relativeCallOffset)
        argStrs = extractArgumentsFromCallStr(callStr)

        pairs = list(zip(argStrs, args))

        out = self._constructArgumentOutput(prefix, context, pairs)
        return out

    def _constructArgumentOutput(self, prefix, context, pairs):
        newline = os.linesep
        def argPrefix(arg):
            return '%s: ' % arg

        pairs = [(arg, self.argToStringFunction(value)) for arg, value in pairs]

        allArgsOnOneLine = ', '.join(argPrefix(arg) + val for arg, val in pairs)
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
                remaining = pairs[1 : ]
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

    def _formatContext(self, callFrame, icNames, icMethod):
        filename, lineNumber, parentFunction = self._getContext(
            callFrame, icNames, icMethod)

        if parentFunction != '<module>':
            parentFunction = '%s()' % parentFunction

        context = '%s:%s in %s' % (filename, lineNumber, parentFunction)
        return context

    def _getContext(self, callFrame, icNames, icMethod):
        # For multiline invocations, like
        #
        #   ic(
        #      )
        #
        # report the call start line, not the call end line. That is, report
        # the line number of 'ic(' in the example above, not ')'. Unfortunately
        # the readily available <frameInfo.lineno> is the end line, not the
        # start line, so it can't be used.
        _, lineNumber, _ = getCallSourceLines(icNames, icMethod, callFrame)

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
