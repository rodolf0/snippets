#!/usr/bin/env python

import itertools as itools

def lcms():
    a = (53 * x for x in itools.count(1))
    b = (151 * x for x in itools.count(1))

    na = next(a)
    nb = next(b)
    while True:
        while na < nb:
            na = next(a)
        if na == nb:
            yield na
            na = next(a)
        while nb < na:
            nb = next(b)
        if na == nb:
            yield nb
            nb = next(b)

for loops, lcm in enumerate(lcms()):
    if loops >= 10:
        break
    print(lcm)
