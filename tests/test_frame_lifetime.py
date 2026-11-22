"""Regression coverage for caller-frame reference cycles."""

import gc
import sys
import unittest
import weakref
from unittest.mock import patch

from icecream import IceCreamDebugger


class Payload:
    pass


def discard_output(text):
    pass


def fail_output(text):
    raise ValueError("output failed")


@unittest.skipUnless(sys.implementation.name == "cpython",
                     "requires CPython reference-counted object lifetime")
class TestFrameLifetime(unittest.TestCase):
    def setUp(self):
        self.gc_was_enabled = gc.isenabled()
        gc.collect()
        gc.disable()

    def tearDown(self):
        gc.collect()
        if self.gc_was_enabled:
            gc.enable()

    def reference_after_call(self, debugger, method="__call__",
                             expect_error=False, with_argument=True):
        payload = Payload()
        reference = weakref.ref(payload)
        try:
            if with_argument:
                getattr(debugger, method)(payload)
            else:
                getattr(debugger, method)()
        except ValueError:
            if not expect_error:
                raise
        else:
            if expect_error:
                self.fail("expected a formatting or output error")
        return reference

    def test_call_releases_argument(self):
        debugger = IceCreamDebugger(outputFunction=discard_output)
        reference = self.reference_after_call(debugger)
        self.assertIsNone(reference())

    def test_format_releases_argument(self):
        debugger = IceCreamDebugger(outputFunction=discard_output)
        reference = self.reference_after_call(debugger, "format")
        self.assertIsNone(reference())

    def test_release_does_not_depend_on_formatter(self):
        debugger = IceCreamDebugger(outputFunction=discard_output)
        def format_without_inspection(call_frame, *args):
            return "formatted"
        with patch.object(debugger, "_format", new=format_without_inspection):
            for method in ("__call__", "format"):
                with self.subTest(method=method):
                    reference = self.reference_after_call(debugger, method)
                    self.assertIsNone(reference())

    def test_no_arguments_releases_caller_locals(self):
        debugger = IceCreamDebugger(outputFunction=discard_output)
        for method in ("__call__", "format"):
            with self.subTest(method=method):
                reference = self.reference_after_call(
                    debugger, method, with_argument=False)
                self.assertIsNone(reference())

    def test_output_error_releases_argument(self):
        debugger = IceCreamDebugger(outputFunction=fail_output)
        reference = self.reference_after_call(debugger, expect_error=True)
        self.assertIsNone(reference())

    def test_formatting_error_releases_argument(self):
        debugger = IceCreamDebugger(outputFunction=discard_output)
        def fail_format(call_frame, *args):
            raise ValueError("formatting failed")
        with patch.object(debugger, "_format", new=fail_format):
            for method in ("__call__", "format"):
                with self.subTest(method=method):
                    reference = self.reference_after_call(
                        debugger, method, expect_error=True)
                    self.assertIsNone(reference())

    def test_disabled_call_releases_argument(self):
        debugger = IceCreamDebugger(outputFunction=discard_output)
        debugger.disable()
        reference = self.reference_after_call(debugger)
        self.assertIsNone(reference())

    def test_passthrough_keeps_returned_argument_alive(self):
        debugger = IceCreamDebugger(outputFunction=discard_output)
        payload = Payload()
        reference = weakref.ref(payload)
        result = debugger(payload)
        self.assertIs(result, payload)
        del payload
        self.assertIs(reference(), result)
        del result
        self.assertIsNone(reference())
