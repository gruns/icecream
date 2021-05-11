import os
import sys
from io import open

try:
    from pathlib import Path
except Exception:
    Path = ()


colorama = None

if os.name == "nt":
    try:
        import colorama
    except Exception:
        pass

PY2 = sys.version_info[0] == 2
string_types = (str, bytes)

if PY2:
    string_types += (unicode,)  # noqa


def write_to_out(out, string, color):
    if callable(out):
        out(string)
        return

    out = current_stream(out)

    if isinstance(out, Path):
        out = str(out)

    if isinstance(out, string_types) or hasattr(out, "__fspath__"):
        with open(out, "a", encoding="utf8") as f:
            f.write(string)
    else:
        if (
            color in (None, True)
            and colorama
            and isatty(out)
            and colorama.AnsiToWin32(out).should_wrap()
        ):
            out = colorama.AnsiToWin32(
                out, convert=True, strip=True, autoreset=True
            ).stream

        try:
            out.write(string)
        except UnicodeEncodeError:
            encoding = getattr(out, "encoding", "utf8")
            string = string.encode(encoding, error="replace")
            out.write(string)

        getattr(out, "flush", lambda: None)()


def current_stream(stream):
    if stream in ("stderr", None):
        stream = sys.stderr
    elif stream == "stdout":
        stream = sys.stdout
    return stream


def should_color(color, stream):
    if color is None:
        stream = current_stream(stream)
        color = isatty(stream)
        if color and colorama:
            color = colorama.AnsiToWin32(stream).should_wrap()
    return color


def isatty(stream):
    return getattr(stream, "isatty", lambda: False)()
