<h1 align="center">
  <img src="logo.svg" width="220px" height="370px" alt="icecream">
</h1>

<p align="center">
  <a href="https://pypi.python.org/pypi/icecream"><img src="https://badge.fury.io/py/icecream.svg"></a>
  <a href="https://travis-ci.org/gruns/icecream"><img src="https://img.shields.io/travis/gruns/icecream.svg"></a>
  <a href="http://unlicense.org/"><img src="https://img.shields.io/pypi/l/icecream.svg"></a>
  <a href="https://pypi.python.org/pypi/icecream"><img src="https://img.shields.io/pypi/pyversions/icecream.svg"></a>
</p>


### IceCream is a little library for sweet and creamy debugging.

Do you ever use `print()` or `log()` to debug your code? Of course you
do. IceCream, or `ic` for short, makes print debugging a little sweeter.

IceCream is well tested, [permissively licensed](LICENSE.txt), and supports
Python 2, Python 3, PyPy2, and PyPy3.


### Inspect Variables

Have you ever printed variables or expressions to debug your program? If you've
ever typed something like

```python
print(foo('123'))
```

or the more thorough


```python
print("foo('123')", foo('123'))
```

then `ic()` is here to help. With arguments, `ic()` inspects itself and prints
both its own arguments and the values of those arguments.

```python
from icecream import ic

def foo(i):
    return i + 333

ic(foo(123))
```

Prints

```
ic| foo(123): 456
```

Similarly,

```python
d = {'key': {1: 'one'}}
ic(d['key'][1])

class klass():
    attr = 'yep'
ic(klass.attr)
```

Prints

```
ic| d['key'][1]: 'one'
ic| klass.attr: 'yep'
```

Just give `ic()` a variable or expression and you're done. Easy.


### Inspect Execution

Have you ever used `print()` to determine which parts of your program are
executed, and in which order they're executed? For example, if you've ever added
print statements to debug code like

```python
def foo():
    print(0)
    first()

    if expression:
        print(1)
        second()
    else:
        print(2)
        third()
```

then `ic()` helps here, too. Without arguments, `ic()` inspects itself and
prints the calling filename, line number, and parent function.

```python
from icecream import ic

def foo():
    ic()
    first()
    
    if expression:
        ic()
        second()
    else:
        ic()
        third()
```

Prints

```
ic| example.py:4 in foo()
ic| example.py:11 in foo()
```

Just call `ic()` and you're done. Simple.


### Return Value

`ic()` returns its argument(s), so `ic()` can easily be inserted into
pre-existing code.

```pycon
>>> a = 6
>>> def half(i):
>>>     return i / 2
>>> b = half(ic(a))
ic| a: 6
>>> ic(b)
ic| b: 3
```


### Miscellaneous

`ic.format(*args)` is like `ic()` but the output is returned as a string instead
of written to stderr.

```pycon
>>> from icecream import ic
>>> s = 'sup'
>>> out = ic.format(s)
>>> print(out)
ic| s: 'sup'
```

Additionally, `ic()`'s output can be entirely disabled, and later re-enabled, with
`ic.disable()` and `ic.enable()` respectively.

```python
from icecream import ic

ic(1)

ic.disable()
ic(2)

ic.enable()
ic(3)
```

Prints

```
ic| 1: 1
ic| 3: 3
```

`ic()` continues to return its arguments when disabled, of course; no existing
code with `ic()` breaks.


### Configuration

`ic.configureOutput(prefix, outputFunction, argToStringFunction,
includeContext)` can be used to adopt a custom output prefix (the default is
`ic| `), change the output function (default is to write to stderr), customize
how arguments are serialized to strings, and/or include the `ic()` call's
context (filename, line number, and parent function) in `ic()` output with
arguments.

```pycon
>>> from icecream import ic
>>> ic.configureOutput(prefix='hello -> ')
>>> ic('world')
hello -> 'world': 'world'
```

`prefix` can optionally be a function, too.

```pycon
>>> import time
>>> from icecream import ic
>>>  
>>> def unixTimestamp():
>>>     return '%i |> ' % int(time.time())
>>>
>>> ic.configureOutput(prefix=unixTimestamp)
>>> ic('world')
1519185860 |> 'world': 'world'
```

`outputFunction`, if provided, is called with `ic()`'s output instead of that
output being written to stderr (the default).

```pycon
>>> import logging
>>> from icecream import ic
>>>
>>> def warn(s):
>>>     logging.warning(s)
>>>
>>> ic.configureOutput(outputFunction=warn)
>>> ic('eep')
WARNING:root:ic| 'eep': 'eep'
```

`argToStringFunction`, if provided, is called with argument values to be
serialized to displayable strings. The default is PrettyPrint's
[pprint.pformat()](https://docs.python.org/3/library/pprint.html#pprint.pformat),
but this can be changed to, for example, handle non-standard datatypes in a
custom fashion.

```pycon
>>> from icecream import ic
>>> 
>>> def toString(obj):
>>>    if isinstance(obj, str):
>>>        return '[!string %r with length %i!]' % (obj, len(obj))
>>>    return repr(obj)
>>> 
>>> ic.configureOutput(argToStringFunction=toString)
>>> ic(7, 'hello')
ic| 7: 7, 'hello': [!string 'hello' with length 5!]
```

`includeContext`, if provided and True, adds the `ic()` call's filename, line
number, and parent function to `ic()`'s output.

```pycon
>>> from icecream import ic
>>> ic.configureOutput(includeContext=True)
>>> 
>>> def foo():
>>>   ic('str')
>>> foo()
ic| example.py:12 in foo()- 'str': 'str'
```

`includeContext` is False by default.


### Installation

Installing IceCream with pip is easy.

```
$ pip install icecream
```


### Import

It's often useful to import `ic()` in a manner that falls back gracefully
if IceCream isn't installed, like in production environments (i.e. not
development). To that end, this fallback import snippet may prove useful:

```python
try:
    from icecream import ic
except ImportError:  # Graceful fallback if IceCream isn't installed.
    ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)  # noqa
```


### IceCream in Other Languages

IceCream should be enjoyed with every language.

- Dart: [icecream](https://github.com/HallerPatrick/icecream)
- Rust: [icecream-rs](https://github.com/ericchang00/icecream-rs)
- Node.js: [node-icecream](https://github.com/jmerle/node-icecream)
- C++: [IceCream-Cpp](https://github.com/renatoGarcia/icecream-cpp)
- PHP: [icecream-php](https://github.com/ntzm/icecream-php)

If you'd like a similar `ic()` function in your favorite language, please open a
pull request! IceCream's goal is to sweeten print debugging with a handy-dandy
`ic()` function in every language.
