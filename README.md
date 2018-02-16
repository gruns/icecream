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


### IceCream is a little library for sweet and creamy print debugging.

Do you ever use `print()` statements to debug your code? Of course you
do. IceCream, or `ic` for short, makes `print()` debugging a little sweeter.

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
both its arguments and its argument's values.

```python
from icecream import ic

def foo(s):
    return s[::-1]

ic(foo('123'))
```

Prints

```
ic| foo('123'): 321
```

Similarly,

```python
d = {'d': {1: 'one'}}
ic(d['d'][1])

class klass():
    attr = 'yep'
ic(klass.attr)
```

prints

```
ic| d['d'][1]: 'one'
ic| klass.attr: 'yep'
```

Just give `ic()` a variable or expression and you're done. Easy.


### Plain Ice Cream (without Arguments)

Do you ever add print statments to determine which parts of your program are
executed, and in which order they're executed? For example, if you've ever added
prints statements to debug something like

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
ic| example.py:4
ic| example.py:11
```

Just call `ic()` and you're done. Simple.


### Return Value

`ic()` returns its argument(s), so `ic()` can be inserted into, and debug, a
pre-existing expression without problem.

```python
>>> def foo(i):
>>>     return i / 2
>>> b = ic(foo(6))
ic| foo(6): 3
>>> ic(b)
ic| b: 3
```


### Installation

Installing IceCream with pip is easy.

```
$ pip install icecream
```


### Other Flavors (Languages)

IceCream is currently just for Python, but IceCream should be enjoyed with every
language.

If you'd like a similar `ic()` method in your favorite language, please open a
pull request! IceCream's goal is to sweeten print debugging with a handy-dandy
`ic()` function in every language.
