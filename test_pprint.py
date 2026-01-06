#!/usr/bin/env python3

import pprint

test_list = [
    1,
    0,
    1,
    0,
    1,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    1,
    1,
    1,
    1,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
]

print("Using repr():")
print(repr(test_list))

print("\nUsing pprint.pformat():")
print(pprint.pformat(test_list))

print("\nUsing pprint.pformat with width=100:")
print(pprint.pformat(test_list, width=100))

print("\nUsing pprint.pformat with width=1000:")
print(pprint.pformat(test_list, width=1000))
