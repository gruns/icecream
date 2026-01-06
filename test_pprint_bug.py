#!/usr/bin/env python3

import pprint

# Test list from bug report
bug_list = [
    1,
    1,
    1,
    1,
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
    0,
    0,
    0,
    0,
    1,
    1,
    1,
    1,
    1,
    0,
    1,
    0,
    1,
    0,
    1,
    0,
]

print("Default pprint:")
print(pprint.pformat(bug_list))
print()

print("With width=120:")
print(pprint.pformat(bug_list, width=120))
print()

print("With width=200:")
print(pprint.pformat(bug_list, width=200))
print()

print("repr:")
print(repr(bug_list))
print()

print("Length:", len(bug_list))
print("repr length:", len(repr(bug_list)))
