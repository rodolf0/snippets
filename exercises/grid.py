#!/usr/bin/env python2

import math, subprocess

def best_grid(n, spare=2):
  """
    return the most square grid that holds at
    least n elements and no more than n+spare

    int(w) * int(h) >= n
    int(w) * int(h) <= n+spare
    min(w - h)

    to view the deduction of the algorithm grafically plot on w, h 2D axis
    h = n / w
    h = n+spare / w
  """
  w = int(math.ceil(math.sqrt(n)))
  h = w
  while w * h > n + spare or w * h < n:
    while w * h > n + spare:
      h -= 1
    while w * h < n:
      w += 1
  return (w, h)


if __name__ == '__main__':
  # calculate grid for n elements ranging from 1 to 200
  with open('_griddata.dat', 'wb') as f:
    for n in xrange(1, 200):
      w, h = best_grid(n, 2)
      f.write("%d %d %d\n" % (n, w, h))

  # plot widths and height as functions of n as well as best case
  with open('_gnuplot.script', 'wb') as f:
    f.write("plot x**0.5 title 'Perfect square',")
    f.write("     'griddata.dat' using 1:2 title 'best width',")
    f.write("     'griddata.dat' using 1:3 title 'best height'")

  subprocess.call("gnuplot -p _gnuplot.script".split(' '))
