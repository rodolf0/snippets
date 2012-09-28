#!/usr/bin/env python

from itertools import combinations
from collections import defaultdict

stats = defaultdict(int)
with open('Artist_lists_small.txt', 'r') as f:
  for line in f:
    for pair in combinations(line.split(','), 2):
      stats[pair] += 1

# filtrar self-pairs
stats = [(k, v) for k, v in stats.items() if k[0] != k[1]]

# top-50
for p in sorted(stats, key=lambda x: x[1], reverse=True)[:50]:
  print(p)


# vim: set sw=2 sts=2 : #
