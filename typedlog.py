#!/usr/bin/env python

import sys

def typedlog(stream, colspec):
    for line in stream:
        line = line.rstrip().split()
        yield tuple(colspec[idx](field)
                    for idx, field in enumerate(line))

def main():
    colspec = (int, float, lambda x: x)
    for tup in typedlog(sys.stdin, colspec):
        print(tup)

if __name__ == "__main__":
    sys.exit(main())
