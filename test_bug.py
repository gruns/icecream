#!/usr/bin/env python3

from icecream import ic


def data_reverse(data):
    bb = []
    for b in range(0, len(data), 8):
        bb.append(data[b : b + 8])

    left = 0
    right = len(bb) - 1

    while right >= left:
        bb[left], bb[right] = bb[right], bb[left]
        left += 1
        right -= 1

    return [el for b in bb for el in b]


# Test with the problematic input
input_data = [
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
result = data_reverse(input_data)

print("Input:")
print(input_data)
print("\nActual result:")
print(result)
print("\nExpected result:")
print(
    [
        0,
        1,
        0,
        1,
        0,
        1,
        0,
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
        1,
        1,
        1,
    ]
)

print("\nUsing ic():")
ic(input_data)
ic(result)
