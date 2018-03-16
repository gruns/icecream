<h1 align="center">
  <img src="icon.svg" width="220px" alt="icecream">
</h1>

<p align="center">
  <a href="https://pypi.python.org/pypi/icecream">
    <img src="https://badge.fury.io/py/icecream.svg">
  </a>
  <a href="https://travis-ci.org/gruns/icecream">
    <img src="https://img.shields.io/travis/gruns/icecream.svg">
  </a>
  <a href="http://unlicense.org/">
    <img src="https://img.shields.io/pypi/l/icecream.svg">
  </a>
  <a href="https://pypi.python.org/pypi/icecream">
    <img src="https://img.shields.io/pypi/pyversions/icecream.svg">
  </a>
</p>


### IceCream is a little library for sweet and creamy debugging.

Do you ever use `print()` or `log()` to debug your code? Of course you
do. IceCream, or `ic` for short, makes print debugging a little sweeter.

IceCream is well tested, [permissively licensed](LICENSE.txt), and supports
Python 2, Python 3, PyPy2, and PyPy3.


### Ice Cream with Toppings (Arguments)

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
both its own arguments and those argument's values.

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


### Plain Ice Cream (without Arguments)

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
prints the calling filename and line number.

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


### Ice Cream Infusion (Return Value)

`ic()` returns its argument(s), so `ic()` can easily be added to, and debug,
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


### Ice Cream Servings

`ic.format(*args)` can be used to generate and return `ic()` output as a string
directly.

```pycon
>>> from icecream import ic
>>> s = ic.format('sup')
>>> print(s)
ic| 'sup': 'sup'
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


### Custom Ice Cream

`ic.configureOutput(prefix, outputFunction, argToStringFunction,
includeContext)` can be used to adopt a custom output prefix (the default is
`ic| `), change the output function (default is to write to stderr), customize
how arguments are serialized to strings, and/or include the `ic()` call's
context (filename, line number, and parent function) in `ic()`'s output.

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
serialized to printable strings. The default is PrettyPrinter's
[pprint.pformat](https://docs.python.org/3/library/pprint.html#pprint.pformat),
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
number, and parent function to `ic()`'s output. `includeContext` is False by
default.

```pycon
>>> from icecream import ic
>>> ic.configureOutput(includeContext=True)
>>> 
>>> def foo():
>>>   ic('str')
>>> foo()
```

Prints

```
ic| example.py:12 in foo()- 'str': 'str'
```


### Installation

Installing IceCream with pip is easy.

```
$ pip install icecream
```


### Other Flavors (Languages)

IceCream should be enjoyed with every language.

- JavaScript: [node-icecream](https://github.com/jmerle/node-icecream)

If you'd like a similar `ic()` function in your favorite language, please open a
pull request! IceCream's goal is to sweeten print debugging with a handy-dandy
`ic()` function in every language.
