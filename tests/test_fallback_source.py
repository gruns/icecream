import warnings
from io import StringIO
import sys

from icecream.icecream import Source
from icecream import ic, stderr_print


class FakeTeletypeBuffer(StringIO):
    def isatty(self):
        return True


def test_fallback_recovers_arg_text_when_executing_fails():
    real_executing = Source.executing

    class NoNode:
        node = None

    def broken(frame):
        return NoNode()

    Source.executing = staticmethod(broken)
    old_output = ic.outputFunction
    ic.configureOutput(outputFunction=stderr_print)
    try:
        real_stderr = sys.stderr
        sys.stderr = FakeTeletypeBuffer()
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                my_test_var_xyz = 12345
                ic(my_test_var_xyz)
        finally:
            output = sys.stderr.getvalue()
            sys.stderr = real_stderr
    finally:
        Source.executing = real_executing
        ic.configureOutput(outputFunction=old_output)
    assert "my_test_var_xyz" in output, "fallback did not recover arg text: %r" % output
    assert len(caught) == 0, "spurious warning emitted: %r" % [str(w.message) for w in caught]
