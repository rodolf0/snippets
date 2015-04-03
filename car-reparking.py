#!/usr/bin/env python

def orderCars(tin, tout):

  print 'Input:', tin
  print 'Desired Output:', tout

  for i in xrange(len(tin)):
    # swap order of cars using '-' as tmp space
    if tin[i] != tout[i]:
      wrong_car = tin[i]
      right_car = tout[i]

      idx_wrong = i
      idx_spc = tin.index('-')
      idx_right = tin.index(right_car)

      # move the wrong car to the empty slot
      if wrong_car != '-':
        print "move car %s to slot %d" % (wrong_car, idx_spc)
        tin[idx_spc] = wrong_car
        tin[i] = '-'

      # move the right car to the place we just created
      if right_car != '-':
        print "move car %s to slot %d" % (right_car, i)
        tin[i] = right_car
        tin[idx_right] = '-'

      print tin



import random
i = ['-', 'a', 'b', 'd', 'c']
o = ['-', 'a', 'b', 'd', 'c']
random.shuffle(i)
random.shuffle(o)
orderCars(i, o)
