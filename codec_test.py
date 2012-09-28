#!/usr/bin/env python2

import codecs, sys

r = codecs.getreader('latin_1')

with r(sys.stdin) as stream:
  for line in stream:
    sys.stdout.write(line)

# vim: set sw=2 sts=2 : #
