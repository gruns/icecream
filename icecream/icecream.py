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

import ast
import dis
import sys
import inspect
import textwrap
from os.path import basename


_absent = object()


def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


MYNAME = 'ic'
DEFAULT_PREFIX = '%s| ' % MYNAME
DEFAULT_OUTPUT_FUNCTION = errprint


def classname(obj):
    return obj.__class__.__name__


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


def isAstNodeIceCreamCall(node, icNames):
    return (
        classname(node) == 'Call' and
        classname(node.func) == 'Name' and
        node.func.id in icNames)


def determinePossibleIcNames(callFrame):
    # TODO(grun): Determine possible function names dynamically from the source
    # to account for name indirection. For example, ic() could be invoked like
    #
    #   class Foo:
    #     blah = ic
    #   Foo.blah()
    #
    # This function, as it exists now, fails to detect the above and only
    # checks for variables in globals() and locals() that are equal to
    # ic(). Like
    #
    #   from icecream import ic as foo
    #   foo()
    #
    # and
    #
    #   from icecream import ic newname = ic newname('blah')
    localNames = [name for name, v in callFrame.f_locals.items() if v == ic]
    globalNames = [name for name, v in callFrame.f_globals.items() if v == ic]

    return list(set(localNames + globalNames))


def getCallSourceLines(icNames, callFrame):
    code = callFrame.f_code

    # inspect.getblock(), which is called internally by inspect.getsource(),
    # only returns the first line of <code> when <code> represents a top-level
    # module, not the entire module's source, as needed here. The
    #
    #   if ismodule(object): return lines, 0
    #
    # check in inspect.py doesn't account for code objects that represent
    # modules, only module objects themselves.
    # 
    # A workaround is to call findsource() directly on top-level modules, which
    # bypasses getblock().
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
        if isAstNodeIceCreamCall(node, icNames) and (
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


def splitCallsOntoSeparateLines(icNames, source):
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
        node.func.col_offset for node in ast.walk(ast.parse(source))
        if isAstNodeIceCreamCall(node, icNames)]
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


def icWithoutArgs(callFrame, icNames, outputFunction):
    # For multiline invocations, like
    #
    #   ic(
    #      )
    #
    # report the call start line, not the call end line. That is, report the
    # line number of 'ic(' in the example above, not ')'. Unfortunately the
    # readily available <frameInfo.lineno> is the end line, not the start line,
    # so it can't be used.
    _, startLine, _ = getCallSourceLines(icNames, callFrame)

    frameInfo = inspect.getframeinfo(callFrame)
    filename = basename(frameInfo.filename)

    out = '%s:%s' % (filename, startLine)
    outputFunction(out)


def icWithArgs(callFrame, icNames, args, outputFunction):
    callSource, _, callSourceOffset = getCallSourceLines(icNames, callFrame)

    callOffset = callFrame.f_lasti
    relativeCallOffset = callOffset - callSourceOffset

    # Insert newlines before every expression and every ic() call so a mapping
    # between `col_offset`s (in characters) and `f_lasti`s (in bytecode) can be
    # established with dis.findlinestarts().
    oneExpressionPerLine = splitExpressionsOntoSeparateLines(callSource)
    splitSource = splitCallsOntoSeparateLines(icNames, oneExpressionPerLine)

    callStr = extractCallStrByOffset(splitSource, relativeCallOffset)
    argStrs = extractArgumentsFromCallStr(callStr)

    pairs = list(zip(argStrs, args))

    output = ', '.join('%s: %r' % (arg, value) for arg, value in pairs)
    outputFunction(output)


class IceCreamDebugger:
    def __init__(self, prefix=DEFAULT_PREFIX,
                 outputFunction=DEFAULT_OUTPUT_FUNCTION):
        self.enabled = True
        self.prefix = prefix
        self.outputFunction = outputFunction

    def __call__(self, *args):
        if self.enabled:
            callFrame = inspect.currentframe().f_back
            icNames = determinePossibleIcNames(callFrame)
        
            if not args:
                icWithoutArgs(callFrame, icNames, self._printOut)
            else:
                icWithArgs(callFrame, icNames, args, self._printOut)

        if not args:  # E.g. ic().
            ret = None
        elif len(args) == 1:  # E.g. ic(1).
            ret = args[0]
        else:  # E.g. ic(1, 2, 3).
            ret = args
        
        return ret

    def _printOut(self, s):
        if callable(self.prefix):
            prefix = self.prefix()
        else:
            prefix = self.prefix

        out = ''.join([prefix, s])
        self.outputFunction(out)

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def configureOutput(self, prefix=_absent, outputFunction=_absent):
        if prefix is not _absent:
            self.prefix = prefix

        if outputFunction is not _absent:
            self.outputFunction = outputFunction


ic = IceCreamDebugger()
